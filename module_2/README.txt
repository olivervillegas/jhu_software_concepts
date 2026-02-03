Grad Cafe Web Scraper - Module 2
=================================

Name: Jim Oliver Villegas
JHED ID: jvilleg7

Module Info: Module 2 - Web Scraping Graduate Admissions Data
Due Date: 01 February 2026

OVERVIEW
--------
This project scrapes graduate school admissions data from thegradcafe.com, 
collecting information about 30,000+ applicant entries including program names, 
universities, decision statuses, test scores, and more. The data is then cleaned 
and standardized using both traditional methods and a local LLM for program/university 
name normalization.

REQUIREMENTS
------------
- Python 3.10 or higher
- pip (Python package installer)
- Internet connection for scraping
- ~2GB disk space for LLM model (downloaded automatically)

INSTALLATION
------------
1. Clone the repository:
   git clone <repo-url>
   cd jhu_software_concepts/module_2

2. Create a virtual environment (recommended):
   python -m venv venv
   
3. Activate the virtual environment:
   - On Windows: venv\Scripts\activate
   - On macOS/Linux: source venv/bin/activate

4. Install main requirements:
   pip install -r requirements.txt

5. Install LLM hosting requirements:
   cd llm_hosting
   pip install -r requirements.txt
   cd ..

ROBOTS.TXT COMPLIANCE
---------------------
The Grad Cafe robots.txt file has been checked (see screenshot_robots.jpg).

Key findings:
- User-agent: * Allow: / (General scraping is allowed)
- Content-Signal: search=yes,ai-train=no (Search indexing is permitted)
- Specific bots like ClaudeBot, GPTBot are disallowed
- Our educational scraper complies with the robots.txt directives

The site permits scraping for search indexing purposes. Our scraper:
- Uses a respectful User-Agent identifier
- Implements delays between requests (1.5 seconds)
- Does not use the data for AI training
- Operates within allowed paths

USAGE
-----

Step 1: Scrape Data
-------------------
Run the scraper to collect applicant data:

python scrape.py

This will:
- Scrape approximately 120 pages (250 entries per page)
- Collect 30,000+ applicant entries
- Save raw data to applicant_data.json
- Take approximately 3-4 hours due to respectful delays

To adjust scraping parameters, edit the main block in scrape.py:
- max_pages: Number of pages to scrape
- delay: Delay between requests in seconds
- fetch_details: Whether to fetch detailed pages (slower but more complete)

Step 2: Clean Data
------------------
Clean and standardize the scraped data:

python clean.py

This will:
- Load applicant_data.json
- Clean HTML remnants, standardize formats
- Save to applicant_data_cleaned.json
- Run LLM standardization for program/university names
- Output final data to applicant_data_final.json

Alternative: Manual LLM Standardization
---------------------------------------
If you prefer to run the LLM standardization separately:

cd llm_hosting
python app.py --file ../applicant_data_cleaned.json --out ../applicant_data_final.jsonl
cd ..

Then convert JSONL to JSON:
python -c "from clean import GradCafeDataCleaner; c = GradCafeDataCleaner(); c.convert_jsonl_to_json('applicant_data_final.jsonl', 'applicant_data_final.json')"

APPROACH
--------

Part 1: Web Scraping (scrape.py)
---------------------------------
The scraping approach uses a class-based design with the following components:

1. GradCafeScraper class:
   - Manages HTTP requests with urllib
   - Implements respectful delays between requests
   - Uses proper User-Agent headers

2. URL Management:
   - Base URL: https://www.thegradcafe.com
   - Search endpoint with pagination support
   - Parameters: pp=250 (results per page), p=<page_number>

3. HTML Parsing with BeautifulSoup:
   - Locates results table using class selectors
   - Extracts data from table rows (<tr> elements)
   - Parses individual cells (<td> elements) for each data field

4. Data Extraction Methods:
   - _parse_entry(): Main parser for table rows
   - _parse_program_degree(): Splits combined program/degree text
   - _extract_decision_info(): Extracts status and dates from badges
   - _parse_detail_page(): Fetches additional details from individual pages

5. Data Fields Collected:
   - university: Institution name
   - program: Program name
   - degree: Masters/PhD
   - added_date: Date entry was added to Grad Cafe
   - decision_status: Accepted/Rejected/Waitlisted
   - decision_date: Date of decision
   - url: Link to full entry
   - comments: User comments (if available)
   - semester/year: Program start term
   - international: International/American status
   - gre_score, gre_verbal, gre_writing: GRE scores
   - gpa: Grade point average

6. Regex Patterns Used:
   - Date extraction: r'on\s+(\d+\s+\w+)'
   - Program/degree split: r'[•·]' (bullet separators)
   - URL matching: r'/result/\d+'
   - Numeric extraction for scores/GPAs

Part 2: Data Cleaning (clean.py)
---------------------------------
The cleaning approach uses structured methods for data normalization:

1. GradCafeDataCleaner class:
   - Processes each entry systematically
   - Applies field-specific cleaning rules

2. HTML Cleaning:
   - Removes HTML tags: r'<[^>]+>'
   - Decodes HTML entities (&nbsp;, &amp;, etc.)
   - Strips extra whitespace

3. Value Standardization:
   - Empty/null values converted to None
   - Inconsistent representations ('n/a', 'NA', 'unknown') standardized

4. Field-Specific Cleaning:
   
   a. GPA Cleaning:
      - Extracts numeric values
      - Validates range (0.0 - 4.0)
      - Removes invalid entries
   
   b. GRE Score Cleaning:
      - Extracts numeric values
      - Validates range (130-340)
      - Handles different score formats
   
   c. Status Standardization:
      - Maps variations to standard values
      - "accept", "accepted" → "Accepted"
      - "reject", "rejected" → "Rejected"
   
   d. Degree Standardization:
      - Maps variants to standard types
      - PhD variants: PHD, Ph.D, Ph.D., Doctorate
      - Masters variants: Masters, Master's, MS, M.S., MA
   
   e. International Status:
      - Standardizes to "International" or "American"
      - Handles variations like "intl", "U.S.", "domestic"

5. LLM Integration:
   - Runs external app.py script from llm_hosting
   - Passes cleaned data through local TinyLlama model
   - Generates standardized program and university names
   - Handles variations, abbreviations, spelling errors
   
6. Post-Processing:
   - Converts JSONL output to JSON format
   - Preserves original values for traceability
   - Adds standardized fields: llm-generated-program, llm-generated-university

Part 3: LLM Standardization (llm_hosting/app.py)
-------------------------------------------------
The provided LLM package uses a local tiny language model:

1. Model: TinyLlama-1.1B-Chat (4-bit quantized)
   - Lightweight, runs on CPU
   - Downloaded automatically from Hugging Face
   
2. Approach:
   - Few-shot prompting with examples
   - Splits combined program/university strings
   - Expands abbreviations (UBC → University of British Columbia)
   - Corrects spelling (McGiill → McGill)
   
3. Post-Processing:
   - Canonical list matching (canon_universities.txt, canon_programs.txt)
   - Abbreviation expansion with regex patterns
   - Fuzzy matching using difflib (cutoff=0.86 for universities, 0.84 for programs)
   - Common fix dictionaries for known issues
   
4. Output Format:
   - JSONL (newline-delimited JSON)
   - Each entry includes original + standardized fields
   - Allows incremental processing and easy resume

DATA STRUCTURE
--------------
Each applicant entry contains the following fields:

{
  "university": "Yale University",
  "program": "Statistics and Data Science",
  "degree": "Masters",
  "added_date": "January 31, 2026",
  "decision_status": "Rejected",
  "decision_date": "26 Jan",
  "url": "https://www.thegradcafe.com/result/994070",
  "comments": null,
  "semester": null,
  "year": null,
  "international": null,
  "gre_score": null,
  "gre_verbal": null,
  "gre_writing": null,
  "gpa": null,
  "llm-generated-program": "Statistics and Data Science",
  "llm-generated-university": "Yale University"
}

PROJECT STRUCTURE
-----------------
module_2/
├── scrape.py                       # Main scraper script
├── clean.py                        # Data cleaning script
├── requirements.txt                # Python dependencies
├── README.txt                      # This file
├── screenshot_robots.jpg           # Screenshot of robots.txt
├── applicant_data.json             # Raw scraped data (generated)
├── applicant_data_cleaned.json     # Cleaned data (generated)
├── llm_extend_applicant_data.jsonl # LLM-processed JSONL (generated)
├── llm_extend_applicant_data.json  # Final cleaned data (generated)
└── llm_hosting/                    # LLM standardization package
    ├── app.py                      # LLM application
    ├── requirements.txt            # LLM dependencies
    ├── canon_universities.txt      # Canonical university names
    ├── canon_programs.txt          # Canonical program names
    └── README.md                   # LLM package documentation

KNOWN ISSUES & IMPROVEMENTS
---------------------------

Current Limitations:
1. Detailed field extraction is limited without fetching individual pages
   - GPA, GRE scores, semester/year often missing
   - Comments not always available
   - Solution: Set fetch_details=True in scrape.py (much slower)

2. LLM standardization is not perfect
   - Some university names still have variations
   - Abbreviations may not all be caught
   - Edge cases exist (e.g., very rare programs)
   - Solution: Expand canon_universities.txt and canon_programs.txt
   - Add more entries to ABBREV_UNI and COMMON_UNI_FIXES in app.py

3. Date formats are inconsistent
   - Some dates are full (January 31, 2026)
   - Some are abbreviated (26 Jan)
   - Solution: Implement comprehensive date parser

4. International status detection is basic
   - Only works when explicitly mentioned
   - Many entries remain None
   - Solution: Fetch from detail pages or improve inference

Systematic Edge Cases Found:
1. Combined program/university in "program" field
   - Handled by LLM splitting and post-processing
   
2. Spelling variations (McGiill, McGill, McG)
   - Addressed with fuzzy matching and fix dictionaries
   
3. Case inconsistencies (University Of vs University of)
   - Normalized with regex replacements
   
4. Missing degree information
   - Left as None for consistency

Future Improvements:
1. Implement caching to avoid re-scraping
2. Add progress bars for better user feedback
3. Implement resume capability for interrupted scraping
4. Add data validation and quality metrics
5. Create visualization of admission statistics
6. Implement database storage for better querying

KNOWN BUGS
----------
1. LLM University Standardization Error:
   The LLM standardization incorrectly changes some university names to 
   completely different institutions. For example:
   - "Ohio State University - Columbus" → "University of British Columbia" (WRONG)
   - "NYU Steinhardt" → "University of British Columbia" (WRONG)
   
   Root Cause: The tiny local LLM (TinyLlama-1.1B) is too small and hallucinates
   university names. It appears to default to a few common universities when uncertain.
   
   Fix: Would require either:
   a) Using a larger/better LLM model
   b) Improving the canonical university list
   c) Adding stricter post-processing rules to reject changes that are too different
   d) Only using LLM for program names, not universities
   
   For now, the original "university" field should be trusted over 
   "llm-generated-university" for most accurate data.

2. GRE AW Score Extraction:
   Some GRE Analytical Writing scores may not be captured due to format variations
   on the website. This is a minor issue affecting <5% of entries.

CANONICAL LIST UPDATES
----------------------
The following additions/changes were made to canonical lists:

canon_universities.txt:
- [List any universities you added]

canon_programs.txt:
- [List any programs you added]

ABBREV_UNI in app.py:
- [List any abbreviation patterns you added]

COMMON_UNI_FIXES in app.py:
- [List any spelling fixes you added]

TESTING
-------
To verify the scraper works:

1. Test with small sample:
   # Edit scrape.py main block:
   data = scraper.scrape_data(max_pages=2, fetch_details=False)

2. Check robots.txt compliance:
   - Screenshot saved as screenshot_robots.jpg
   - Scraper uses 1.5 second delays
   - Respectful User-Agent header

3. Verify data quality:
   python -c "from clean import load_data; d = load_data('applicant_data.json'); print(f'Entries: {len(d)}'); print(f'Sample: {d[0]}')"

TROUBLESHOOTING
---------------
- If scraping fails: Check internet connection, verify site is up
- If LLM fails: Ensure llm_hosting requirements are installed
- If model download fails: Check disk space, try manual download
- If parsing fails: Site structure may have changed, check HTML
- For other issues: Check error messages, review logs

DELIVERABLES
------------
✓ scrape.py - Web scraper implementation
✓ clean.py - Data cleaning implementation  
✓ applicant_data.json - 30,000+ entries collected
✓ applicant_data_final.json - Cleaned and standardized data
✓ requirements.txt - Dependencies list
✓ README.txt - This documentation
✓ screenshot_robots.jpg - robots.txt compliance evidence
✓ llm_hosting/ - LLM standardization package

ACADEMIC INTEGRITY
------------------
This project was completed in accordance with JHU academic integrity policies.
All code is original work. External libraries (BeautifulSoup, urllib) are used
per assignment requirements. The LLM package was provided as part of assignment
materials.

REFERENCES
----------
- Grad Cafe: https://www.thegradcafe.com
- BeautifulSoup Documentation: https://www.crummy.com/software/BeautifulSoup/
- Python urllib: https://docs.python.org/3/library/urllib.html
- llama.cpp Python bindings: https://github.com/abetlen/llama-cpp-python