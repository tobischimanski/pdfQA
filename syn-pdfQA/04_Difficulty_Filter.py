import json
import glob
import pandas as pd
import numpy as np
from openai import AsyncOpenAI
import asyncio
from bs4 import BeautifulSoup
import sys

# windows or not?
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# read API key
with open("key.txt", "r", encoding="utf-8") as f:
    OPENAI_API_KEY = f.read().strip()

# Prompt adapted from LlamaIndex
prompt_template_answering = """Your task is to answer the QUESTION with the given CONTEXT INFORMATION.

CONTEXT INFORMATION:
---------------------
{context_str}
---------------------

QUESTION: {query_str}

Given the CONTEXT INFORMATION and not prior knowledge, answer the QUESTION.

Follow the following guideline when answering the QUESTION:
{guideline}
"""

# guideline is derive from the question type in modules in the generation process
guidelines = {
    "yes-no-question": "The QUESTION must be answered by stricly only a 'Yes' or 'No'.",
    "value-question": "The QUESTION must be answered by a single value.",
    "word-answer": "The QUESTION must be answered by one to five words, without forming a full sentence.",
    "one-sentence-answer": "The QUESTION must be answered by a single sentence.",
    "open-ended-question-short": "The QUESTION must be answered by a short open-ended answer.",
    "open-ended-question-long": "The QUESTION must be answered by a long open-ended answer.",
}

g_eval_prompt = """You will be given a question, a proposed answer, and a ground truth answer.

Your task is to rate the correctness of the proposed answer. Please make sure you read and understand these instructions carefully.

Evaluation Criteria:
Correctness (1-5) - This evaluates whether the proposed answer is factually correct based on the ground truth. Your task is to determine if the proposed answer is aligned with and entailed by the ground truth answer.


Evaluation Steps:
1. Read the question and ground truth answer: Understand the key facts and details provided in the ground truth answer that are relevant to the question.
2. Compare the proposed answer to the ground truth answer: Check if the proposed answer is factually accurate, consistent, and aligned with the ground truth answer.
3. Assign a correctness score (1-5):
   - 1: The proposed answer is factually incorrect or contradicts the ground truth.
   - 2: The proposed answer contains multiple factual errors or significant inaccuracies.
   - 3: The proposed answer is partially correct but includes some factual errors or omissions.
   - 4: The proposed answer is mostly correct with minor factual deviations.
   - 5: The proposed answer is fully correct and strictly aligns with the ground truth.


Question:
-----
{Question}
-----

Ground Truth Answer:
-----
{Ground_Truth_Answer}
-----

Proposed Answer:
-----
{Proposed_Answer}
-----

Evaluation Form (output ONLY a single score - nothing else):
- Correctness:
"""


def open_raw_file(file_path, report_type, reduce_file_by=0):
  file_name = file_path.split("/")[-1].split("_vfQA.")[0] # change to \\ from / for windows
  # for 10K
  if report_type == "10K":
    report_type_file_ending = ".htm"
    raw_file = f"01.1_Input_Files_Non_PDF/{report_type}/{file_name}{report_type_file_ending}"
    with open(raw_file, "r", encoding="utf-8") as f:
      html_string = f.read()

    soup = BeautifulSoup(html_string, "html.parser")
    plain_text = soup.get_text(separator=" ", strip=True)
    return plain_text
  # for Arxiv
  if report_type == "Arxiv":
    report_type_file_ending = ".tex"
    raw_file = f"01.1_Input_Files_Non_PDF/{report_type}/{file_name}{report_type_file_ending}"

    with open(raw_file, "r", encoding="utf-8") as f:
      string = f.read()
    return string

  # for Sust_reports, books
  # since these files are so long, integrate options of reducing the file randomly if it is too long for long-context QA
  if report_type == "Sust_reports" or report_type == "books":
    report_type_file_ending = ".parquet"
    raw_file = f"02_Parsed_Input_Files_to_Sources/{report_type}/{file_name}_clustered{report_type_file_ending}"
    df = pd.read_parquet(raw_file)
    # reduce the file by 1-reduce_file_by% of entry
    if reduce_file_by > 0:
      df = df.sample(frac=1-reduce_file_by, random_state=42)
      # order by source_identifier
      df = df.sort_values(by="source_identifier")
    string = "\n\n\n".join([str(x) for x in df.content.to_list()])
    return string


# prompts and filter
def get_prompts_create(data_json, full_document_raw, prompt_template, answer_guidelines):
  prompts = []
  new_data = []
  # go through every row of the dataset
  for count in np.arange(0, len(data_json)):
    data_sub = data_json[count]

    ### ATTENTION: IMPORTANT FILTERING STEP: filter all data points that are not passing inner and outer validity filters
    if (data_sub["raw_g-eval_score_OV"] != "5") or (data_sub["raw_g-eval_score_IV"] != "5") or (data_sub["formal_checks"] == "no"):
      continue
    else:
      new_data.append(data_sub)

    # questions
    question = data_sub["question"]
    # get guideline
    guideline = answer_guidelines[data_sub["answer_type"]]

    # fill into prompt template
    prompt = prompt_template.format(context_str=full_document_raw, query_str=question, guideline=guideline)
    prompts.append(prompt)

  parsed_prompts = []
  for p in prompts:
    messages = [
      {"role": "user", "content": p},
    ]
    parsed_prompts.append(messages)

  # return
  return new_data, parsed_prompts, prompts



# prompts and filter
def get_prompts_eval(data_json, raw_ans, prompt_template):
  prompts = []
  # go through every row of the dataset
  for i, d in enumerate(data_json):
    # get sources
    Question = d["question"]
    # questions
    Ground_Truth_Answer = d["answer"]
    # get answer
    Proposed_Answer = raw_ans[i]

    # fill into prompt template
    prompt = prompt_template.format(Question=Question, Ground_Truth_Answer=Ground_Truth_Answer, Proposed_Answer=Proposed_Answer)
    prompts.append(prompt)

  parsed_prompts = []
  for p in prompts:
    messages = [
      {"role": "user", "content": p},
    ]
    parsed_prompts.append(messages)

  # return
  return parsed_prompts, prompts


# asynced creation of answers
async def answer_async_OpenAI(prompts, MODEL, CLIENT):
  coroutines = []
  for m in prompts:
    #p = "What is 100 * 44554 / 24334 + 4 - 8?"
    co = CLIENT.chat.completions.create(
        model = MODEL,
        temperature = 0.0,
        seed = 23,
        messages = m,
        logprobs = True,
        top_logprobs=5,
    )
    coroutines.append(co)
  # Schedule calls *concurrently*:
  out = await asyncio.gather(*coroutines)
  #print(L)
  return out

async def createAnswersDef(prompts, CLIENT, MODEL):
  # create answers
  answers = await answer_async_OpenAI(prompts, MODEL, CLIENT)
  #print("Answers Given")
  return answers

# ANSWERING
def createColumns(answers):
  # top-5 token-level representations
  raw_answers, tokens, all_logprobs, logprob_first = [], [], [], []
  for answ in answers:
    answer_local = answ.choices[0].message.content
    raw_answers.append(answ.choices[0].message.content)
    if len(answer_local) > 1:
      logprob_first.append("Invalid answer")
      all_logprobs.append("Invalid answer")
      tokens.append("Invalid answer")
      continue

    # get token-level probability
    token_score = answ.choices[0].logprobs.content[0].token
    all_probs_score = answ.choices[0].logprobs.content[0].top_logprobs
    list_scores= [[x.token, np.round(np.exp(x.logprob)*100,2)] for x in all_probs_score]
    tokens.append(all_probs_score)
    logprob_first.append(list_scores[0][1])
    all_logprobs.append(str(list_scores))

  scores = []
  for i, a in enumerate(raw_answers):
    try:
      score = float(a) * (logprob_first[i]/100)
      scores.append(score)
    except:
      scores.append("Invalid answer")

  return raw_answers, scores


async def main():
    # openai key
    ACLIENT = AsyncOpenAI(api_key = OPENAI_API_KEY)
    MODEL_create_answer = "gpt-4o-mini-2024-07-18" # "gpt-4.1-mini-2025-04-14" # "gpt-4o-2024-11-20" # "gpt-4.1-2025-04-14"
    MODEL_eval_answer = "gpt-4.1-mini-2025-04-14"

    for report_type in ["research articles"]:
      all_data = glob.glob(f"04_Quality_Filtered_Question_Answer_Data/{report_type}/*.json")

      for file_path in all_data:
        print(file_path)
        data = json.load(open(file_path))

        #### CREATE ANSWERS
        raw_full_document = open_raw_file(file_path, report_type)

        # get prompts and new data
        new_data, parsed_prompts, prompts = get_prompts_create(data, raw_full_document, prompt_template_answering, guidelines)

        # answer the question
        not_answered = True
        # if document is too long, then we reduce the answer space randomly => applies to books
        reduce_by = 0.1 # reduce long file by 10% as long as it works
        while not_answered:
          try:
            answers = await createAnswersDef(parsed_prompts, ACLIENT, MODEL_create_answer)
            raw_answers = [a.choices[0].message.content for a in answers]
            not_answered = False
          except:
            print("Context too long.")
            raw_full_document = open_raw_file(file_path, report_type, reduce_by)
            new_data, parsed_prompts, prompts = get_prompts_create(data, raw_full_document, prompt_template_answering, guidelines)
            reduce_by += 0.1


        ### EVALUATE ANSWERS
        parsed_prompts_eval, prompts_eval = get_prompts_eval(new_data, raw_answers, g_eval_prompt)
        answers_eval = await createAnswersDef(parsed_prompts_eval, ACLIENT, MODEL_eval_answer)
        raw_answers_eval, scores = createColumns(answers_eval)

        # map scores to data
        for i, d in enumerate(new_data):
          d[f"answer_C_{MODEL_create_answer}"] = raw_answers[i]
          d[f"raw_g-eval_score_C_{MODEL_create_answer}"] = raw_answers_eval[i]
          d[f"g-eval_score_C_{MODEL_create_answer}"] = scores[i]

        # store outcome dict
        # Save to JSON file
        report_data_name = file_path.split("\\")[-1].split("_vfQA.")[0] # change to \\ from / for windows
        output_file = f'05_Difficulty_Filtered_Question_Answer_Data/{report_type}/{report_data_name}_cfQA_{MODEL_create_answer}.json'
        with open(output_file, 'w') as f:
            json.dump(new_data, f, indent=4)

# run
if __name__ == "__main__":
    asyncio.run(main())
