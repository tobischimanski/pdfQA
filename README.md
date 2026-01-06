# pdfQA: Diverse, Challenging, and Realistic Question Answering over PDFs

This is the repository for the paper [pdfQA: Diverse, Challenging, and Realistic Question Answering over PDFs](https://arxiv.org/abs/2601.02285v1). It aims to make the benchmark dataset based on PDFs accessible and easy to use.

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

## (Raw Data, PDF) tuples and Code
To use the dataset effectively, the Raw Data files (e.g. ".html", ".tex") and PDFs are provided in the folders:
- syn-pdfQA: [README file](https://github.com/tobischimanski/pdfQA/blob/main/syn-pdfQA/README_syn.md) and [access to all files](https://drive.google.com/drive/folders/15mBSETh24BVkuchvozJ40YWt51OkfL8s?usp=sharing)
- real-pdfQA: [README file](https://github.com/tobischimanski/pdfQA/blob/main/real-pdfQA/README_real.md) and [access to all files](https://drive.google.com/drive/folders/1uUd_n4QCg7WBZnoX-4yRwoa-J8OAGIXh?usp=sharing)

The code of the synthethic data generation and filtering pipeline is in "syn-pdfQA" and described in the corresponding [README file](https://github.com/tobischimanski/pdfQA/blob/main/syn-pdfQA/README_syn.md).

## Further Requests

This is ongoing work. If you have any questions, feel free to reach out to tobias.schimanski@df.uzh.ch.

## Citation

If you use the dataset, please cite:
```shell
@misc{schimanski2026pdfqa,
      title={pdfQA: Diverse, Challenging, and Realistic Question Answering over PDFs}, 
      author={Tobias Schimanski and Imene Kolli and Jingwei Ni and Yu Fan and Ario Saeid Vaghefi and Elliott Ash and Markus Leippold},
      year={2026},
      eprint={2601.02285},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2601.02285}, 
}
```
