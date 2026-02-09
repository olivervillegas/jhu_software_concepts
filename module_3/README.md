Grad Cafe Data Analysis - Module 3
=================================

Name: Jim Oliver Villegas
JHED ID: jvilleg7

Module Info: Module 3 - PostgreSQL Analytics and Flask Web Application
Due Date: 08 February 2026

OVERVIEW
--------
This project extends the Grad Cafe web scraping and data cleaning pipeline from
Module 2 by loading graduate admissions data into a PostgreSQL database, performing
SQL-based analysis, and displaying results through a Flask web application.

An instructor-provided, LLM-standardized dataset is used to ensure consistent field
naming and reliable querying. PostgreSQL is used as the backend relational database,
and all analytics are executed using SQL through the psycopg library.

REQUIREMENTS
------------
- Python 3.12 or higher
- pip (Python package installer)
- PostgreSQL (local installation)
- pgAdmin 4

INSTALLATION
------------
1. Clone the repository:
   git clone <repo-url>
   cd jhu_software_concepts/module_3

2. Create a virtual environment (recommended):
   python -m venv venv

3. Activate the virtual environment:
   - On Windows: venv\Scripts\activate
   - On macOS/Linux: source venv/bin/activate

4. Install requirements:
   pip install -r requirements.txt

USAGE
-----

Step 1: Load Data into PostgreSQL
--------------------------------
Run the data loading script:

python load_data.py

This will:
- Detect JSON or JSONL input automatically
- Map instructor-specific field names to database columns
- Clean invalid characters including NULL bytes
- Parse dates and numeric values
- Normalize decision status, degree type, and citizenship
- Truncate and reload the applicants table

Step 2: Run SQL Analysis
-----------------------
Execute the SQL analytics:

python query_data.py

This will print:
- Number of Fall 2026 applicants
- Percentage of international applicants
- Average GPA and GRE statistics
- Acceptance rates
- Program- and university-specific metrics
- Comparisons using downloaded versus LLM-generated fields

Step 3: Run Flask Web Application
---------------------------------
Start the Flask application:

python app.py

Then open the following URL in a web browser:

http://127.0.0.1:5000

APPROACH
--------

Part 1: PostgreSQL Data Loading (load_data.py)
----------------------------------------------
The data loading approach focuses on correctness and normalization:

1. Dataset Handling:
   - Supports JSON and JSONL instructor-provided files
   - Uses LLM-standardized fields for consistency

2. Field Mapping:
   - Maps instructor keys such as applicant_status, semester_year_start,
     citizenship, and masters_or_phd to database schema fields

3. Data Cleaning:
   - Removes NULL bytes
   - Extracts numeric values from GPA and GRE strings
   - Parses date strings into PostgreSQL date format

4. Database Integrity:
   - Truncates the applicants table before reload
   - Ensures consistent schema population

Part 2: SQL Analysis (query_data.py)
------------------------------------
SQL queries are executed via psycopg to compute all required metrics:

1. Aggregation Queries:
   - COUNT, AVG, ROUND
   - Defensive handling of NULL values and division by zero

2. Filtering Logic:
   - Term-based analysis (Fall 2026)
   - Citizenship-based analysis
   - Degree and program-specific queries

3. LLM Comparison:
   - Analysis using original program text
   - Analysis using LLM-generated program and university fields

Part 3: Flask Web Application (app.py)
-------------------------------------
The Flask application provides a simple frontend for analysis results:

1. Displays SQL query results on a styled webpage
2. Includes a "Pull Data" button to demonstrate data ingestion logic
3. Includes an "Update Analysis" button to refresh displayed results

DATA STRUCTURE
--------------
Each database entry contains the following fields:

p_id
program
comments
date_added
url
status
term
us_or_international
gpa
gre
gre_v
gre_aw
degree
llm_generated_program
llm_generated_university

PROJECT STRUCTURE
-----------------
module_3/
├── load_data.py
├── query_data.py
├── app.py
├── scrape.py
├── clean.py
├── requirements.txt
├── README.txt
├── limitations.pdf
├── screenshots/
│   ├── pgadmin_db_table.png
│   ├── pgadmin_rows.png
│   ├── console_query_output.png
│   └── flask_page.png
└── data/
    └── llm_extend_applicant_data.json

LIMITATIONS
-----------
A discussion of the limitations of using anonymously submitted admissions data from
Grad Cafe is provided in limitations.pdf.

ACADEMIC INTEGRITY
------------------
This project was completed in accordance with JHU academic integrity policies.
All code is original work unless otherwise noted. External libraries are used
per assignment requirements.

REFERENCES
----------
- Grad Cafe: https://www.thegradcafe.com
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- psycopg Documentation: https://www.psycopg.org/
- Flask Documentation: https://flask.palletsprojects.com/
