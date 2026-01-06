# syn-pdfQA

"syn-pdfQA" is created using the synthethic data generation pipeline describe in the [the pdfQA paper](https://arxiv.org/abs/2601.02285v1). 

## Data
We use tuples of (raw data, PDF) for the pipeline. The "raw data" comes in a structured form like ".html" or ".tex". An exact file for a QA pair in "syn-pdfQA" can be identified using the '{file_type}/{file_name}' combination in the three folders:
- 01.1_Input_Files_Non_PDF: contains the raw data in its original format like ".html" for financial reporting or ".tex" for research articles.
- 01.2_Input_Files_PDF: contains the PDF files in its orginal format.
- 01.3_Input_Files_CSV: contains a parsed version of the non-PDF file into csv splitting the files by paragraph units. You may to wish that splitting strategy or go ahead with our proposed chunking.

All (raw data, PDF) tuples can be found in [this Google Drive folder](https://drive.google.com/drive/folders/15mBSETh24BVkuchvozJ40YWt51OkfL8s?usp=sharing). We are working on making it more accessible in the future.

## Code for Data Generation and Filtering
Using the input data, we can create synthethic QA pairs with our pipeline and filter them according to our quality and difficulty dimensions. We use the following four python files for this purpose:
- 01_Cluster_Sources.py: This is a preprocessing step for the Raw Data where we create clusters for the sources.
- 02_Create_Answers.py: Here, we create the QA pairs from the sources, contemplating a range of guidelines and quality criteria.
- 03_Quality_Filter.py: Here, we filter out QA pairs that have potential quality issues with respect to formality, inner validity and outer validity (see also paper).
- 04_Difficulty_Filter.py: Here, we filter QA pairs that are too easy (see also paper).

For filtering "real-pdfQA", we use "01_Cluster_Sources.py", "03_Quality_Filter.py", and "04_Difficulty_Filter.py" analogously. 
