import json
import glob
import pandas as pd
import numpy as np
import random
from openai import AsyncOpenAI
import asyncio
import sys

# windows or not?
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# read API key
with open("key.txt", "r", encoding="utf-8") as f:
    OPENAI_API_KEY = f.read().strip()

prompt_template_summary = r"""You are a domain expert in {domain} and are provided with SOURCES from a domain document. Your task is to create a QUESTION and ANSWER based on the SOURCES.


    Use the following questions SOURCES:
    [Begin of SOURCES]
    {sources}
    [End of SOURCES]


    Create a QUESTION and an ANSWER for the QUESTION following these GUIDELINES:
    {guidelines}

    Your task is to create a QUESTION that is realistic in the context of a question-answering benchmark over reports. Do not come up with artificial questions that would never appear in reality. In reality, the provided sources appear throughout the entire document. Thus, do not refer to a source identifier or assume that the source is standalone. The QUESTION should be designed to make sense with respect to the entire document (that you have no full access to).

    Please output the answer in a JSON format using the keys "question", "answer", and "sources". "question" contains the QUESTION you have produced. "answer" contains the ANSWER to the question. "sources" includes the source identifiers in the SOURCES (e.g., ["Source 1", "Source 2"]). Strictly cite only the sources that were actually used to create the question, not necessarily all the sources given.

    Output the JSON file with the keys "question", "answer", and "sources":
    """

# modules
modules = {
    # source quantity
    "arbitrary sources": "The QUESTION must be answerable using one or more given SOURCES. Strive for connecting SOURCES in a logical manner.",
    "strict multiple sources": "The QUESTION must be answerable using as many as possible given SOURCES. However, produce a single QUESTION that only uses logically connected SOURCES.",
    # answer type
    "yes-no-question": "The QUESTION must be answerable by strictly only a 'Yes' or 'No'. Please do not use any other words in the answer.",
    "value-question": "The QUESTION must be answerable by a single value.",
    "word-answer": "The QUESTION must be answerable by one to five words, without forming a full sentence.",
    "one-sentence-answer": "The QUESTION must be answerable by a single sentence.",
    "open-ended-question-short": "The QUESTION must be answerable by a short open-ended answer.",
    "open-ended-question-long": "The QUESTION must be answerable by a long open-ended answer.",
    # replicate or reasoning
    "replicate": "The QUESTION must be answerable by a simple replication of parts of the SOURCES or a simple summary of SOURCES.",
    "reasoning": "The QUESTION must be answerable by a reasoning process over the SOURCES.",
    # modality
    "text-only": "The QUESTION must be answerable with only the contents of a text.",
    "table-only": "The QUESTION must be answerable with only the contents of a table, including its caption.",
    "mixed-modality": "The QUESTION must be answerable through a combination of multiple modalities between text, table, or others.",
    "clustering": "The QUESTION can make use of a combination of multiple modalities between text, table, or a others.",
    # difficulty
    "simple": "The QUESTION is very simple and straightforward to answer given the SOURCES.",
    "medium": "The QUESTION is moderately complex and requires some reasoning to answer, given the SOURCES.",
    "complex": "The QUESTION is very complex and requires a lot of reasoning to answe,r given the SOURCES."
}

def create_useful_configuration(n_sources, proximity_question=True):
  configuration = {}
  # Randomly choose a answer type
  configuration["answer_type"] = random.choice(["yes-no-question", "value-question", "word-answer", "one-sentence-answer", "open-ended-question-short", "open-ended-question-long"])
  # Randomly choose replicate or reasoning
  configuration["reasoning"] = random.choice(["replicate", "reasoning"])
  # Choose a modality
  if proximity_question:
    # FOR SUST REPORTS: random.choice(["mixed-modality", "table-only"]); ELSE: random.choice(["text-only", "mixed-modality", "table-only"])
    # GENERALLY: configuration["modality"] = random.choice(["text-only", "mixed-modality", "table-only"])
    # FOR DEMONSTRATION, we only focus on text because it's easier
    configuration["modality"] = random.choice(["text-only"])# TODO: include: ["text-only", "mixed-modality", "table-only"]
  else:
    configuration["modality"] = "clustering"

  configuration["source quantity"] = random.choice(["strict multiple sources", "arbitrary sources"]) if configuration["modality"] in ["clustering", "mixed-modality", "text-only"] else "arbitrary sources"
  # Choose a difficulty
  configuration["difficulty"] = random.choice(["simple", "medium", "complex"]) if configuration["reasoning"] == "reasoning" else "simple"

  return configuration

def createGuidelines_Sources_Clustering(report_data, n_sources, configuration, modules):
  # Create guidelines with the configuration
  guidelines = ""
  for i, value in enumerate(configuration.values()):
    guidelines += f"{i+1}. {modules[value]}\n"

  # Select random cluster
  cluster_indexes = report_data.cluster.unique()
  seed_cluster = random.choice(cluster_indexes)
  report_data_cluster = report_data[report_data.cluster == seed_cluster]

  # Randomly select n_sources in the cluster, or all if n_sources > len(report_data_cluster)
  if n_sources > len(report_data_cluster):
    n_sources = len(report_data_cluster)

  report_data_cluster_used = report_data_cluster.sample(n_sources).sort_values(by="source_identifier")

  # Create source indexes
  sources = report_data_cluster_used.content.to_list()
  source_identifiers = report_data_cluster_used.source_identifier.to_list()
  modalities = report_data_cluster_used.type.to_list()

  # Go through each row of sources and create Source X (modality: text): [text]
  source_text = ""
  for i, source in enumerate(sources):
    source_text += f"\n-----\n{source_identifiers[i]} (modality: {modalities[i]}): {source}\n-----\n"

  return guidelines, source_text, sources


def createGuidelines_Sources_Proximity(report_data, n_sources, configuration, modules):
  # Create guidelines with the configuration
  guidelines = ""
  for i, value in enumerate(configuration.values()):
    guidelines += f"{i+1}. {modules[value]}\n"

  # If modality is "text-only", just give back full-text paragraphs
  if configuration["modality"] == "text-only":
    # Create subset of dataset with only "full text"
    report_data_text_only = report_data[report_data["type"] == "text"]
    len_sources = len(report_data_text_only)
    # Create source indexes
    seed_x = random.randint(0, len_sources-1)
    lower = int(np.ceil(seed_x - (n_sources / 2))) if seed_x - (n_sources / 2) > 0 else 0
    upper = int(np.ceil(seed_x + (n_sources / 2))) if seed_x + (n_sources / 2) < len_sources else len_sources - 1
    source_indexes = list(range(lower, upper))

    # Create the sources
    sources = report_data_text_only.iloc[source_indexes].content.to_list()
    source_identifiers = report_data_text_only.iloc[source_indexes].source_identifier.to_list()

    # Go through each row of sources and create Source X (modality: text): [text]
    source_text = ""
    for i, source in enumerate(sources):
      source_text += f"\n-----\n{source_identifiers[i]} (modality: text): {source}\n-----\n"

  ### if modality is table only, then only table
  if configuration["modality"] == "table-only":
    # Create subset of dataset with only "real_table"
    report_data_sub = report_data[report_data["type"] == "table"]
    len_sources = len(report_data_sub)
    # Create source indexes
    seed_x = random.randint(0, len_sources-1)
    sources = report_data_sub.iloc[[seed_x]].content.to_list()
    source_identifiers = report_data_sub.iloc[[seed_x]].source_identifier.to_list()
    source_text = f"\n-----\n{source_identifiers[0]} (modality: table): {sources[0]}\n-----\n"

  if configuration["modality"] == "mixed-modality":
    # seed_x needs to be a table indentifier
    report_data_sub = report_data[report_data["type"] == "table"]
    len_sources = len(report_data_sub)
    seed_x_temp = random.randint(0, len_sources-1)
    index_temp = report_data_sub.iloc[[seed_x_temp]].index[0]
    # Row number of index_temp
    seed_x = report_data.index.get_loc(index_temp)
    len_sources = len(report_data)
    lower = int(np.ceil(seed_x - (n_sources / 2))) if seed_x - (n_sources / 2) > 0 else 0
    upper = int(np.ceil(seed_x + (n_sources / 2))) if seed_x + (n_sources / 2) < len_sources else len_sources - 1
    source_indexes = list(range(lower, upper))

    sources = report_data.iloc[source_indexes].content.to_list()
    source_identifiers = report_data.iloc[source_indexes].source_identifier.to_list()
    modalities = report_data.iloc[source_indexes].type.to_list()

    # Go through each row of sources and create Source X (modality: text): [text]
    source_text = ""
    for i, source in enumerate(sources):
      source_text += f"\n-----\n{source_identifiers[i]} (modality: {modalities[i]}): {source}\n-----\n"

  return guidelines, source_text, sources

def create_question_answer_sources_prompt(configuration, report_data, n_sources, proximity_question, modules, domain):
  # Create guidelines and prompt
  if proximity_question:
    guidelines, source_text, raw_sources = createGuidelines_Sources_Proximity(report_data, n_sources, configuration, modules)
  else:
    guidelines, source_text, raw_sources = createGuidelines_Sources_Clustering(report_data, n_sources, configuration, modules)

  filled_prompt = prompt_template_summary.format(
      domain=domain,
      sources=source_text,
      guidelines=guidelines
  )

  prompt_message = [
      {"role": "user", "content": filled_prompt},
    ]

  return filled_prompt, prompt_message, raw_sources

# asynced creation of answers
async def answer_async_OpenAI(prompts, MODEL, CLIENT):
  coroutines = []
  for m in prompts:
    #p = "What is 100 * 44554 / 24334 + 4 - 8?"
    co = CLIENT.chat.completions.create(
        model = MODEL,
        temperature = 0,
        seed = 23,
        messages = m
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


### FIND SOURCE POSITION
def majority_bucket(values, max_val):
    buckets = {25: 0, 50: 0, 75: 0, 100: 0}

    for v in values:
        pct = v / max_val
        if pct <= 0.25:
            buckets[25] += 1
        elif pct <= 0.50:
            buckets[50] += 1
        elif pct <= 0.75:
            buckets[75] += 1
        else:
            buckets[100] += 1

    total = len(values)
    for bucket in [25, 50, 75, 100]:
        if buckets[bucket] > total / 2:
            return bucket

    # no clear majority → lowest bucket
    return 25


def post_process_answer(answer, report_data, configuration, proximity_question):
  try:
    # Load JSON string into a Python dictionary
    data = json.loads(answer.replace("```json", "").replace("```", ""))
  except:
    #print("JSON did not work")
    return None

  # Infer the characterstics
  data["modality_configured"] = configuration["modality"]
  data["modalities_used"] = report_data[report_data.source_identifier.isin(data["sources"])]["type"].to_list()
  data["num_sources_used"] = len(data["sources"])
  # Plig in value from the configuration
  data["answer_type"] = configuration["answer_type"]
  data["reasoning"] = configuration["reasoning"]
  data["difficulty"] = configuration["difficulty"]
  if proximity_question:
    data["source_sampling_strategy"] = "proximity"
  else:
    data["source_sampling_strategy"] = "clustering"
  data["n_sources_seen"] = configuration["n_sources_seen"]

  # Store obvious variables
  data["file_name"] = report_data.file_name.iloc[0]
  # document word spread
  data["file_length"] = len(" ".join(report_data.text_only.to_list()).split(" "))
  # Create a subset of the dataset with the minimal and maximal source number used and then count the words
  # Find the row indices for the identifiers
  start_index = report_data[report_data['source_identifier'] == data["sources"][0]].index[0]
  end_index = report_data[report_data['source_identifier'] == data["sources"][-1]].index[0]
  sub_df = report_data.loc[start_index:end_index]
  data["source_spread"] = len(" ".join(sub_df.text_only.to_list()).split(" "))
  # Also save text of all cited sources
  sources_used = report_data[report_data.source_identifier.isin(data["sources"])].content.to_list()
  data["source_text"] = sources_used

  # surces bucket
  num_max_source = int(report_data.source_identifier.iloc[-1].split("_")[-1])
  data["sources_position"] = majority_bucket([int(source.split("_")[-1]) for source in data["sources"]], num_max_source)
  return data


def createRandomPrompts(report_data, questions_per_file, modules, domain, num_sources_configured="random"):
  # Create randomly n questions per file
  prompts, messages, proximity_questions, configurations  = [], [], [], []
  for i in range(questions_per_file):
      # Create configuration quite randomly
      if num_sources_configured == "random":
        n_sources = random.randint(5, 15)
      else:
        n_sources = random.randint(num_sources_configured[0], num_sources_configured[1])
      proximity_question = random.randint(0, 1) # false means, we create a question using clustering

      # Create configuration
      configuration = create_useful_configuration(n_sources, proximity_question)
      # Create prompt
      filled_prompt, prompt_messages, raw_sources = create_question_answer_sources_prompt(configuration, report_data, n_sources, proximity_question, modules, domain)

      # Add n_sources seen into configuration
      configuration["n_sources_seen"] = len(raw_sources)

      # Filter out prompts that are longer than 100.000 signs (likely a wrong sources in it)
      if len(filled_prompt) > 100000:
        #print("Exceeded 100.000 characters.")
        continue

      # Append all
      messages.append(prompt_messages)
      prompts.append(filled_prompt)
      proximity_questions.append(proximity_question)
      configurations.append(configuration)

  return prompts, messages, proximity_questions, configurations

async def main():
    # openai key
    ACLIENT = AsyncOpenAI(api_key=OPENAI_API_KEY)
    MODEL = "gpt-4.1-2025-04-14"  # "gpt-5-2025-08-07" "gpt-4o-2024-11-20" ""gpt-4.1-2025-04-14""

    report_type = "research articles"

    # take th
    all_sources = glob.glob(f"./02_Parsed_Input_Files_to_Sources/{report_type}/*")
    all_sources = all_sources[0:100]  # Arxiv was [0:100] and 25 questions per file

    # configure sources per file
    questions_per_file = 50
    # domain = "analysing company's annual reporting"
    # domain = "analysing research articles"
    # domain = "analysing company's sustainability reporting"
    domain = "analysing books"

    # num sources
    num_sources_configured = [5, 15]

    # not already done files
    done_files = glob.glob(f"./03_Raw_Synthetic_Question_Answer_Data/{report_type}/*.json")
    done_files = [i.split("\\")[-1].split("_rawQA.")[0] for i in done_files] # change to \\ for windows
    not_done_files = [i for i in all_sources if i.split("\\")[-1].split("_clustered")[0] not in done_files]

    # all_sources OR not_done_files
    for file_path in not_done_files:
        #try:
            print(file_path)
            # store results
            outcome_dicts = []
            report_data = pd.read_parquet(file_path)
            # process into "table" and "text" for Arxiv
            report_data["type"] = report_data["type"].apply(lambda x: "table" if x == "table" else "text")
            # Go through individual files
            prompts, messages, proximity_questions, configurations = createRandomPrompts(report_data,
                                                                                         questions_per_file, modules,
                                                                                         domain, num_sources_configured)
            answers = await createAnswersDef(messages, ACLIENT, MODEL)
            raw_answers = [answer.choices[0].message.content for answer in answers]

            for i, answer in enumerate(raw_answers):
                data_dict = post_process_answer(answer, report_data, configurations[i], proximity_questions[i])
                # Append
                if data_dict is not None:
                    outcome_dicts.append(data_dict)

            # store outcome dict
            # Save to JSON file
            # report_data_name = file_path.split("/")[-1].split("_clustered.")[0]
            report_data_name = file_path.split("\\")[-1].split("_clustered.")[0] # for windows
            output_file = f'03_Raw_Question_Answer_Data/{report_type}/{report_data_name}_rawQA.json'
            with open(output_file, 'w') as f:
                json.dump(outcome_dicts, f, indent=4)
        #except:
        #    print(f"ERROR for {file_path}")
        #    continue

# run
if __name__ == "__main__":
    asyncio.run(main())
