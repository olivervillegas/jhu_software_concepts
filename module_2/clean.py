"""
Data cleaning module for Grad Cafe applicant data.
Cleans and standardizes scraped data, integrating with LLM for program/university normalization.
"""

import json
import re
import subprocess
import sys
from typing import Dict, List, Optional, Any


class GradCafeDataCleaner:
    """Cleans and standardizes Grad Cafe applicant data."""
    
    def __init__(self):
        """Initialize the data cleaner."""
        pass
    
    def _clean_html(self, text: Optional[str]) -> Optional[str]:
        """
        Remove any remnant HTML tags and entities from text.
        
        Args:
            text: Text that may contain HTML
            
        Returns:
            Cleaned text or None
        """
        if not text:
            return None
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip() if text.strip() else None
    
    def _standardize_empty(self, value: Any) -> Any:
        """
        Standardize empty/null values to None.
        
        Args:
            value: Value to check
            
        Returns:
            Value or None if empty
        """
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned or cleaned.lower() in ['n/a', 'na', 'none', 'unknown', '']:
                return None
            return cleaned
        return value
    
    def _clean_gpa(self, gpa: Optional[str]) -> Optional[str]:
        """
        Clean and validate GPA values.
        
        Args:
            gpa: Raw GPA string
            
        Returns:
            Cleaned GPA or None
        """
        if not gpa:
            return None
        
        # Extract numeric value
        match = re.search(r'(\d+\.?\d*)', str(gpa))
        if match:
            gpa_val = match.group(1)
            # Validate range (0.0 - 4.0 typically)
            try:
                if 0.0 <= float(gpa_val) <= 4.0:
                    return gpa_val
            except ValueError:
                pass
        
        return None
    
    def _clean_gre_score(self, score: Optional[str]) -> Optional[str]:
        """
        Clean and validate GRE scores.
        
        Args:
            score: Raw GRE score string
            
        Returns:
            Cleaned score or None
        """
        if not score:
            return None
        
        # Extract numeric value
        match = re.search(r'(\d+)', str(score))
        if match:
            score_val = match.group(1)
            # Validate range (GRE scores typically 130-170 per section, 260-340 combined)
            try:
                val = int(score_val)
                if 130 <= val <= 340:  # Reasonable GRE range
                    return score_val
            except ValueError:
                pass
        
        return None
    
    def _clean_date(self, date: Optional[str]) -> Optional[str]:
        """
        Clean and standardize date formats.
        
        Args:
            date: Raw date string
            
        Returns:
            Cleaned date or None
        """
        if not date:
            return None
        
        # Remove extra whitespace
        date = ' '.join(str(date).split())
        
        return date if date else None
    
    def _clean_status(self, status: Optional[str]) -> Optional[str]:
        """
        Standardize decision status values.
        
        Args:
            status: Raw status string
            
        Returns:
            Standardized status or None
        """
        if not status:
            return None
        
        status = status.strip().lower()
        
        if 'accept' in status:
            return "Accepted"
        elif 'reject' in status:
            return "Rejected"
        elif 'waitlist' in status:
            return "Waitlisted"
        elif 'interview' in status:
            return "Interview"
        
        return status.title() if status else None
    
    def _clean_degree(self, degree: Optional[str]) -> Optional[str]:
        """
        Standardize degree type.
        
        Args:
            degree: Raw degree string
            
        Returns:
            Standardized degree or None
        """
        if not degree:
            return None
        
        degree = degree.strip().upper()
        
        # Common degree type mappings
        phd_variants = ['PHD', 'PH.D', 'PH.D.', 'DOCTORATE', 'DOCTORAL']
        masters_variants = ['MASTERS', 'MASTER', "MASTER'S", 'MS', 'M.S.', 'MA', 'M.A.', 'MSC', 'M.SC.']
        
        if any(variant in degree for variant in phd_variants):
            return "PhD"
        elif any(variant in degree for variant in masters_variants):
            return "Masters"
        
        return degree.title() if degree else None
    
    def _clean_international_status(self, status: Optional[str]) -> Optional[str]:
        """
        Standardize international/domestic status.
        
        Args:
            status: Raw status string
            
        Returns:
            Standardized status or None
        """
        if not status:
            return None
        
        status = status.strip().lower()
        
        if 'international' in status or 'intl' in status:
            return "International"
        elif 'american' in status or 'domestic' in status or 'u.s' in status or 'us' in status:
            return "American"
        
        return None
    
    def _clean_entry(self, entry: Dict) -> Dict:
        """
        Clean a single applicant entry.
        
        Args:
            entry: Raw entry dictionary
            
        Returns:
            Cleaned entry dictionary
        """
        cleaned = {}
        
        # Clean all text fields for HTML
        for key, value in entry.items():
            if isinstance(value, str):
                cleaned[key] = self._clean_html(value)
            else:
                cleaned[key] = value
        
        # Standardize empty values
        for key in cleaned:
            cleaned[key] = self._standardize_empty(cleaned[key])
        
        # Apply specific cleaning to certain fields
        if 'gpa' in cleaned:
            cleaned['gpa'] = self._clean_gpa(cleaned['gpa'])
        
        if 'gre_score' in cleaned:
            cleaned['gre_score'] = self._clean_gre_score(cleaned['gre_score'])
        
        if 'gre_verbal' in cleaned:
            cleaned['gre_verbal'] = self._clean_gre_score(cleaned['gre_verbal'])
        
        if 'gre_writing' in cleaned:
            cleaned['gre_writing'] = self._clean_gre_score(cleaned['gre_writing'])
        
        if 'decision_status' in cleaned:
            cleaned['decision_status'] = self._clean_status(cleaned['decision_status'])
        
        if 'degree' in cleaned:
            cleaned['degree'] = self._clean_degree(cleaned['degree'])
        
        if 'international' in cleaned:
            cleaned['international'] = self._clean_international_status(cleaned['international'])
        
        if 'added_date' in cleaned:
            cleaned['added_date'] = self._clean_date(cleaned['added_date'])
        
        if 'decision_date' in cleaned:
            cleaned['decision_date'] = self._clean_date(cleaned['decision_date'])
        
        return cleaned
    
    def clean_data(self, data: List[Dict]) -> List[Dict]:
        """
        Clean all applicant entries.
        
        Args:
            data: List of raw applicant entries
            
        Returns:
            List of cleaned entries
        """
        cleaned_data = []
        
        print(f"Cleaning {len(data)} entries...")
        
        for i, entry in enumerate(data):
            cleaned = self._clean_entry(entry)
            cleaned_data.append(cleaned)
            
            if (i + 1) % 1000 == 0:
                print(f"Cleaned {i + 1} entries...")
        
        print(f"Cleaning complete! {len(cleaned_data)} entries cleaned.")
        return cleaned_data
    
    def run_llm_standardization(self, input_file: str, output_file: str) -> bool:
        """
        Run the LLM standardization process on cleaned data.
        
        Args:
            input_file: Path to input JSON file
            output_file: Path to output JSONL file
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\nRunning LLM standardization...")
        print(f"Input: {input_file}")
        print(f"Output: {output_file}")
        
        try:
            # Run the LLM app.py script
            cmd = [
                sys.executable,
                "llm_hosting/app.py",
                "--file", input_file,
                "--out", output_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("LLM standardization complete!")
            print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error running LLM standardization: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    def convert_jsonl_to_json(self, jsonl_file: str, json_file: str) -> None:
        """
        Convert JSONL output back to JSON array format.
        
        Args:
            jsonl_file: Path to JSONL file
            json_file: Path to output JSON file
        """
        print(f"\nConverting JSONL to JSON...")
        
        entries = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        
        print(f"Converted {len(entries)} entries to {json_file}")


def save_data(data: List[Dict], filename: str) -> None:
    """
    Save cleaned data to JSON file.
    
    Args:
        data: List of cleaned entries
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} entries to {filename}")


def load_data(filename: str) -> List[Dict]:
    """
    Load data from JSON file.
    
    Args:
        filename: Input filename
        
    Returns:
        List of entries
    """
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} entries from {filename}")
    return data


if __name__ == "__main__":
    # Example usage
    cleaner = GradCafeDataCleaner()
    
    # Load scraped data
    print("Loading scraped data...")
    raw_data = load_data("applicant_data.json")
    
    # Clean the data
    cleaned_data = cleaner.clean_data(raw_data)
    
    # Save intermediate cleaned data
    save_data(cleaned_data, "applicant_data_cleaned.json")
    
    # Run LLM standardization
    success = cleaner.run_llm_standardization(
        "applicant_data_cleaned.json",
        "llm_extend_applicant_data.jsonl"
    )
    
    if success:
        # Convert back to JSON format
        cleaner.convert_jsonl_to_json(
            "llm_extend_applicant_data.jsonl",
            "llm_extend_applicant_data.json"
        )
        print("\nData cleaning pipeline complete!")
    else:
        print("\nLLM standardization failed. Using cleaned data without LLM processing.")