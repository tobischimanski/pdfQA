# syn-pdfQA

"syn-pdfQA" is created using the synthethic data generation pipeline describe in the [the pdfQA paper](https://arxiv.org/abs/2601.02285v1). 

We use tuples of (raw data, PDF) for the pipeline. The "raw data" comes in a structured form like ".html" or ".tex". An exact file for a QA pair in "syn-pdfQA" can be identified using the '{file_type}/{file_name}' combination in the three folders:
- 01.1_Input_Files_Non_PDF: contains the raw data in its original format like ".html" for financial reporting or ".tex" for research articles.
- 01.2_Input_Files_PDF: contains the PDF files in its orginal format.
- 01.3_Input_Files_CSV: contains a parsed version of the non-PDF file into csv splitting the files by paragraph units. You may to wish that splitting strategy or go ahead with our proposed chunking.

All (raw data, PDF) tuples can be found in [this Google Drive folder](https://drive.google.com/drive/folders/15mBSETh24BVkuchvozJ40YWt51OkfL8s?usp=sharing). We are working on making it more accessible in the future.

