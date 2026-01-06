# real-pdfQA

"real-PDFQA" is created based on the following datasets (see also [the pdfQA paper](https://arxiv.org/abs/2601.02285v1)):
- [ClimRetrieve](https://aclanthology.org/2024.emnlp-main.969/)
- [FinQA](https://arxiv.org/abs/2109.00122)
- [FinanceBench](https://arxiv.org/abs/2311.11944)
- [ClimateFinanceBench](https://arxiv.org/abs/2505.22752)
- [FeTaQA](https://arxiv.org/abs/2104.00369)
- [NaturalQuestions](https://research.google/pubs/natural-questions-a-benchmark-for-question-answering-research/)
- [PaperTab and PaperText from Qasper](https://arxiv.org/abs/2105.03011)
- [Tat-QA](https://arxiv.org/abs/2105.07624)

We create tuples of (raw data, PDF) for the pipeline. The "raw data" comes from parsing the PDFs with PyMUPDF and chunking it with the [LlamaIndex sentenceSplitter function](https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/sentence_splitter/) (as opposed to "syn-pdfQA", where we have clean raw data). An exact file for a QA pair in "real-pdfQA" can be identified using the '{file_type}/{file_name}' combination in the three folders:
- 01.1_Input_Files_Non_PDF: contains the raw data in its parsed format plus the ending "__pymupdf" to signal it is a parsed document.
- 01.2_Input_Files_PDF: contains the PDF files in its orginal format.
- 01.3_Input_Files_CSV: contains the pyMUPDF-parsed file splitted with the LlamaIndex sentenceSplitter function, also plus the "__pymupdf" to signal it is based on a parsed document.

All (raw data, PDF) tuples can be found in [this Google Drive folder](https://drive.google.com/drive/folders/1fc3TT3aycxvyctSMQ3MNQEflXx8BflGh?usp=sharing). We are working on making it more accessible in the future.



