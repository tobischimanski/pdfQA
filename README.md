# pdfQA: Diverse, Challenging, and Realistic Question Answering over PDFs

This is the repository for the paper "pdfQA: Diverse, Challenging, and Realistic Question Answering over PDFs". It aims to make the benchmark dataset based on PDFs accessible and easy to use.

We start with a dataset description.

## Datasets

The datasets have the following structure (marked with * is only present in syn-pdfQA):
- file_type (is called "dataset" in real-pdfQA): this is the file type (dataset) from which the data is obtained. We have questions on financial reports, research articles, books, and sustainability disclosures (in real-pdfQA, it is the datasets ClimRetrieve, ClimateFinanceBench, FinQA, FinanceBench, FeTaQA NaturalQuestions, PaperTab, PaperText, Tat-QA).
- file_name: this is the exact file name of the document on which the QA pair is on.
- question: question to be answer on the document.
- answer: answer of the question.
- sources*: a list of source identifiers that are connected to the raw data files (e.g. ".csv" files in "syn-pdfQA" folder).
- source_text: a list of texts from the document that are relevant to answer the question.
- answer_type*: yes/no, value extraction, single word, or open-ended answers.
- answer_length*: the length of the answer.
- reasoning*: whether the answer is a replication of information or needs reasoning.
- question difficulty*: a pre-defined level of difficulty (simple, medium, hard).
- modalities*: the modalities used to answer the question (e.g., text, tables, mixed modalities).
- num_sources*: how many relevant sources are needed to answer the question.
- source_spread*: a distance measure of how 136
much text is between the first and the last 137
relevant source, 138
- sources_position*: a proxy for where in the 139
file the relevant sources are clustered, 140
- file_length*: the length of the file.

## GitHub in Progress

We will work on further details in the upcoming weeks. If you need any data, feel free to reach out to tobias.schimanski@df.uzh.ch in the meantime.

