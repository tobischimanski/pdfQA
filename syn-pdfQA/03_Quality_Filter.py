import json
import glob
import pandas as pd
import numpy as np
from openai import OpenAI
from openai import AsyncOpenAI
from sklearn.metrics.pairwise import cosine_similarity
import asyncio
import sys

# windows or not?
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# read API key
with open("key.txt", "r", encoding="utf-8") as f:
    OPENAI_API_KEY = f.read().strip()


g_eval_prompt = """You will be given a set of sources, a question and an answer.

Your task is to rate the faithfulness of the answer. Please make sure you read and understand these instructions carefully.

Evaluation Criteria:
Faithfulness (1-5) - this evaluates whether the generated answer strictly adheres to the set of sources without introducing unsupported or contradicting claims.

Evaluation Steps:
1. Read the sources and question: Identify relevant information in the sources that directly addresses the question.
2. Compare the answer to the sources: Check if the answer strictly adheres to the sources and avoids unsupported or contradicting claims.
3. Assign a faithfulness score (1-5):
- 1: The answer misrepresents or contradicts the sources.
- 2: Contains multiple unsupported claims, errors, or contradictions.
- 3: Partially faithful with some unsupported claims or inaccuracies.
- 4: Mostly faithful with minor deviations.
- 5: Fully faithful and strictly adheres to the sources.

Set of sources:
----------
{Sources}
----------

Question:
----------
{Question}
----------

Answer:
----------
{Answer}
----------

Evaluation Form (ouput ONLY a single score - nothing else):
- Faithfulness:
"""

# guideline is derive from the answer type in modules in the generation process
guidelines = {
    "yes-no-question": "The QUESTION must be answered by stricly only a 'Yes' or 'No'.",
    "value-question": "The QUESTION must be answered by a single value.",
    "word-answer": "The QUESTION must be answered by one to five words, without forming a full sentence.",
    "one-sentence-answer": "The QUESTION must be answered by a single sentence.",
    "open-ended-question-short": "The QUESTION must be answered by a short open-ended answer.",
    "open-ended-question-long": "The QUESTION must be answered by a long open-ended answer.",
}

formal_checks_prompt = """You will be given a question, a guideline, and an answer.

Your task is to check whether the formal criteria of the question and answer are fulfilled.
The evaluation is based on the following criteria. All must be satisfied for the final result to be "yes".

Evaluation Criteria:
- Is the question free of references that could be misunderstood in the context of a full document? (e.g., the question does not refer vaguely to "the table")
- Is the question unambiguous and likely to have a deterministic answer? (disallowed are questions such as "What is one example for...?")
- Does the question align with the guideline? (do only judge clear misalignments, e.g. a yes/no question was not answered with "yes" or "no")

Question:
----------
{Question}
----------

Guideline:
----------
{Guideline}
----------

Answer:
----------
{Answer}
----------

Instruction:
Answer only with "yes" or "no".
If all evaluation criteria are met, respond with "yes". Otherwise, respond with "no".

Your answer:
"""

# prompts
def get_prompts(data_json, prompt_template, source_column="source_text", source_identifier_column="sources"):
  prompts = []
  # go through every row of the dataset
  for count in np.arange(0, len(data_json)):
    data_sub = data_json[count]
    # get sources
    source_text = ""
    for i, source in enumerate(data_sub[source_column]):
      si = data_sub[source_identifier_column][i]
      source_text += f"\n-----\n{si}: {source}\n-----\n"
    # questions
    question = data_sub["question"]
    # get answer
    answer = data_sub["answer"]


    # fill into prompt template
    prompt = prompt_template.format(Sources=source_text, Question=question, Answer=answer)
    prompts.append(prompt)

  parsed_prompts = []
  for p in prompts:
    messages = [
      {"role": "user", "content": p},
    ]
    parsed_prompts.append(messages)

  # return
  return parsed_prompts, prompts

def get_prompts_formal_checks(data_json, prompt_template, guidelines):
  prompts = []
  # go through every row of the dataset
  for count in np.arange(0, len(data_json)):
    data_sub = data_json[count]
    # get guidlines
    guideline = guidelines[data_sub["answer_type"]]
    # questions
    question = data_sub["question"]
    # get answer
    answer = data_sub["answer"]


    # fill into prompt template
    prompt = prompt_template.format(Question=question, Guideline=guideline, Answer=answer)
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

# Function to find top k similar entries
def find_top_k_similar(df, question, client, model, top_k=5, column_name="embeddings_text-embedding-3-small"):
    df = df.copy()
    # Embed the question
    response = client.embeddings.create(model=model, input=question)
    question_embedding = np.array(response.data[0].embedding)

    # Calculate cosine similarity
    embeddings = np.vstack(df[column_name])
    similarities = cosine_similarity([question_embedding], embeddings).flatten()

    # Add similarities to DataFrame and sort by similarity
    df['similarity'] = similarities
    top_k_df = df.sort_values(by='similarity', ascending=False).head(top_k)
    return top_k_df[['similarity'] + [col for col in df.columns if col != column_name]]

def extend_data(data, df, client, model, top_k=5, column_name="embeddings_text-embedding-3-small"):
  # extend sources and source identifiers with top k entries
  for count in np.arange(0, len(data)):
    data_sub = data[count]
    question = data_sub["question"]

    # use df without exisiting source identifier
    exisisting_si = data_sub["sources"]
    df_sub = df.loc[~df["source_identifier"].isin(exisisting_si)]

    # search for top-k similar to question
    top_k_df = find_top_k_similar(df_sub, question, client, model, top_k, column_name)

    # extended lists
    #sources_extended = data_sub["source_text"] + top_k_df["content"].tolist()
    source_identifiers_extended = data_sub["sources"] + top_k_df["source_identifier"].tolist()

    # also use the surrounding sources (alternative: uses only surrounding context of raw sources)
    source_identifiers_extended_v2 = []
    for si in source_identifiers_extended:
      number = int(si.split("_")[1])
      source_identifiers_extended_v2.append(si)
      source_identifiers_extended_v2.append(f"Source_{number+1}")
      source_identifiers_extended_v2.append(f"Source_{number-1}")

    # get all sources that have the source identifier
    sources_extended_df = df[df["source_identifier"].isin(source_identifiers_extended_v2)].copy()
    sources_sorted = sources_extended_df["content"].tolist()
    source_identifiers_sorted = sources_extended_df["source_identifier"].tolist()

    data_sub["source_text_extended"] = sources_sorted
    data_sub["sources_extended"] = source_identifiers_sorted
  return data


async def main():
    # openai key
    ACLIENT = AsyncOpenAI(api_key = OPENAI_API_KEY)
    CLIENT = OpenAI(api_key= OPENAI_API_KEY)
    MODEL = "gpt-4.1-mini-2025-04-14" # "gpt-4o-2024-08-06" # "gpt-4.1-2025-04-14"
    embedding_model = "text-embedding-3-small"

    for report_type in ["research articles"]:
      all_data = glob.glob(f"03_Raw_Question_Answer_Data/{report_type}/*.json")

      # exclude those that were already done
      # change / to \\ for windows
      done = [x.split("\\")[-1].split("_vfQA")[0] for x in glob.glob(f"04_Quality_Filtered_Question_Answer_Data/{report_type}/*.json")]
      not_done_all_data = [x for x in all_data if x.split("\\")[-1].split("_rawQA")[0] not in done]

      # not_done_all_data or all_data
      for file_path in not_done_all_data:
        print(file_path)
        data = json.load(open(file_path))

        ### INNER VALIDITY: Does the question and answer make sense with respect to the sources?
        # create prompts
        parsed_prompts, prompts = get_prompts(data, g_eval_prompt)

        # create answers
        answers = await createAnswersDef(parsed_prompts, ACLIENT, MODEL)
        raw_answers, scores = createColumns(answers)

        # map scores to data
        for i, d in enumerate(data):
          d["raw_g-eval_score_IV"] = raw_answers[i]
          d["g-eval_score_IV"] = scores[i]


        ### OUTER VALIDITY
        file_name = file_path.split("\\")[-1].split("_rawQA")[0] # change / to \\ for windows
        report_data = pd.read_parquet(f"./02_Parsed_Input_Files_to_Sources/{report_type}/{file_name}_clustered.parquet")
        # extend data
        data = extend_data(data, report_data, CLIENT, embedding_model, 5, "embeddings_text-embedding-3-small")

        # create prompts
        parsed_prompts, prompts = get_prompts(data, g_eval_prompt, "source_text_extended", "sources_extended")

        # create answers
        answers = await createAnswersDef(parsed_prompts, ACLIENT, MODEL)
        raw_answers, scores = createColumns(answers)

        # map scores to data
        for i, d in enumerate(data):
          d["raw_g-eval_score_OV"] = raw_answers[i]
          d["g-eval_score_OV"] = scores[i]

        ### FORMALITY CHECKS
        parsed_prompts, prompts = get_prompts_formal_checks(data, formal_checks_prompt, guidelines)
        answers = await createAnswersDef(parsed_prompts, ACLIENT, MODEL)
        raw_answers = [answ.choices[0].message.content for answ in answers]
        for i, d in enumerate(data):
          d["formal_checks"] = raw_answers[i]

        # store outcome dict
        # Save to JSON file
        report_data_name = file_path.split("\\")[-1].split("_rawQA.")[0] # change / to \\ for windows
        output_file = f'04_Quality_Filtered_Question_Answer_Data/{report_type}/{report_data_name}_vfQA.json'
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)

# run
if __name__ == "__main__":
    asyncio.run(main())
