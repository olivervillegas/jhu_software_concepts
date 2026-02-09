from scrape import GradCafeScraper, save_data
from clean import GradCafeDataCleaner
import subprocess

scraper = GradCafeScraper(delay=1.5)
raw_data = scraper.scrape_data(max_pages=5)  # intentionally small
save_data(raw_data, "data/applicant_data.json")

cleaner = GradCafeDataCleaner()
cleaned = cleaner.clean_data(raw_data)
save_data(cleaned, "data/applicant_data_cleaned.json")

# Optional: load instructor-provided LLM data instead
subprocess.run(["python", "load_data.py"])
