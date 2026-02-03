Personal Developer Website - Module 1
=====================================

OVERVIEW
--------
This is a personal portfolio website built with Flask that showcases my bio, 
contact information, and projects.

REQUIREMENTS
------------
- Python 3.10 or higher
- pip (Python package installer)

INSTALLATION
------------
1. Clone the repository:
   git clone <https://github.com/olivervillegas/jhu_software_concepts>
   cd jhu_software_concepts/module_1

2. Create a virtual environment (recommended):
   python -m venv venv
   
3. Activate the virtual environment:
   - On Windows: venv\Scripts\activate
   - On macOS/Linux: source venv/bin/activate

4. Install required packages:
   pip install -r requirements.txt

RUNNING THE APPLICATION
-----------------------
1. From the module_1 directory, run:
   python run.py

2. Open your web browser and navigate to:
   http://localhost:8080
   or
   http://0.0.0.0:8080

3. To stop the server, press Ctrl+C in the terminal

PROJECT STRUCTURE
-----------------
module_1/
├── app/
│   ├── __init__.py          # Application factory
│   ├── routes.py            # Blueprint with route definitions
│   ├── static/              # Static files (CSS, images)
│   │   └── style.css        # Stylesheet
│   └── templates/           # HTML templates
│       ├── base.html        # Base template with navbar
│       ├── home.html        # Homepage template
│       ├── contact.html     # Contact page template
│       └── projects.html    # Projects page template
├── run.py                   # Application entry point
├── website_pages.pdf        # Screenshots of the running site
├── requirements.txt         # Python dependencies
└── README.txt               # This file

FEATURES
--------
- Flask web framework
- Blueprint architecture for modular design
- Responsive navigation bar (top right, highlighted current tab)
- Three main pages: Home, Contact, and Projects
- CSS styling with color scheme
- Runs on port 8080

TROUBLESHOOTING
---------------
- If port 8080 is already in use, you can change it in run.py
- Make sure all dependencies are installed: pip install -r requirements.txt
- Verify you're using Python 3.10+: python --version