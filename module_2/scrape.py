"""
Web scraper for Grad Cafe applicant data.
Gathers graduate school admission statistics from thegradcafe.com.
"""

import urllib.request
import urllib.parse
import json
import time
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional


class GradCafeScraper:
    """Scraper for Grad Cafe admissions data."""
    
    BASE_URL = "https://www.thegradcafe.com"
    SURVEY_URL = f"{BASE_URL}/survey/"
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize the scraper.
        
        Args:
            delay: Delay between requests in seconds (respectful scraping)
        """
        self.delay = delay
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Educational Research Bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    
    def _make_request(self, url: str) -> str:
        """
        Make HTTP request with proper headers and delay.
        
        Args:
            url: URL to request
            
        Returns:
            HTML content as string
        """
        req = urllib.request.Request(url, headers=self.headers)
        
        try:
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
            time.sleep(self.delay)  # Respectful delay
            return html
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def _extract_semester_year(self, badge_text: str) -> Dict[str, Optional[str]]:
        """
        Extract semester and year from badge text like 'Fall 2026'.
        
        Args:
            badge_text: Text from semester badge
            
        Returns:
            Dictionary with semester and year
        """
        match = re.search(r'(Fall|Spring|Summer|Winter)\s+(\d{4})', badge_text, re.IGNORECASE)
        if match:
            return {"semester": match.group(1), "year": match.group(2)}
        return {"semester": None, "year": None}
    
    def _extract_gre_scores(self, badges: List[str]) -> Dict[str, Optional[str]]:
        """
        Extract GRE scores from badge list.
        
        Args:
            badges: List of badge texts
            
        Returns:
            Dictionary with GRE scores
        """
        scores = {
            "gre_score": None,
            "gre_verbal": None,
            "gre_writing": None
        }
        
        for badge in badges:
            # GRE general (quantitative)
            if re.match(r'^GRE\s+\d+$', badge, re.IGNORECASE):
                match = re.search(r'GRE\s+(\d+)', badge, re.IGNORECASE)
                if match:
                    scores["gre_score"] = match.group(1)
            
            # GRE Verbal
            elif re.match(r'^GRE\s+V', badge, re.IGNORECASE):
                match = re.search(r'GRE\s+V\s+(\d+)', badge, re.IGNORECASE)
                if match:
                    scores["gre_verbal"] = match.group(1)
            
            # GRE AW (Analytical Writing)
            elif re.match(r'^GRE\s+AW', badge, re.IGNORECASE):
                match = re.search(r'GRE\s+AW\s+([\d.]+)', badge, re.IGNORECASE)
                if match:
                    scores["gre_writing"] = match.group(1)
        
        return scores
    
    def _parse_entry(self, main_row, detail_row) -> Optional[Dict]:
        """
        Parse a pair of table rows (main + details) into structured data.
        
        Args:
            main_row: BeautifulSoup element for main row
            detail_row: BeautifulSoup element for detail row with badges
            
        Returns:
            Dictionary with applicant data or None if parsing fails
        """
        try:
            cells = main_row.find_all('td')
            if len(cells) < 5:
                return None
            
            # Extract university (first cell)
            university = cells[0].get_text(strip=True)
            
            # Extract program and degree (second cell)
            # Format: "Program Name • Degree"
            program_cell = cells[1].get_text(separator='|', strip=True)
            parts = program_cell.split('|')
            program = parts[0].strip() if len(parts) > 0 else None
            degree = parts[1].strip() if len(parts) > 1 else None
            
            # Extract added date (third cell)
            added_date = cells[2].get_text(strip=True) if len(cells) > 2 else None
            
            # Extract decision info (fourth cell)
            decision_cell = cells[3] if len(cells) > 3 else None
            decision_text = decision_cell.get_text(strip=True) if decision_cell else ""
            
            # Parse decision status and date
            status = None
            decision_date = None
            if "Accepted" in decision_text:
                status = "Accepted"
            elif "Rejected" in decision_text:
                status = "Rejected"
            elif "Wait listed" in decision_text or "Waitlisted" in decision_text:
                status = "Waitlisted"
            elif "Interview" in decision_text:
                status = "Interview"
            
            # Extract decision date (e.g., "on 26 Jan")
            date_match = re.search(r'on\s+(\d+\s+\w+)', decision_text)
            if date_match:
                decision_date = date_match.group(1)
            
            # Extract URL from link in last cell
            url = None
            link = cells[4].find('a', href=re.compile(r'/result/\d+'))
            if link and 'href' in link.attrs:
                url = self.BASE_URL + link['href']
            
            # Parse detail row for additional info (badges)
            international = None
            gpa = None
            semester = None
            year = None
            gre_scores = {"gre_score": None, "gre_verbal": None, "gre_writing": None}
            comments = None
            
            if detail_row:
                # Find all badges in detail row
                badges = detail_row.find_all('div', class_=re.compile(r'tw-inline-flex.*tw-items-center'))
                badge_texts = [badge.get_text(strip=True) for badge in badges]
                
                for badge_text in badge_texts:
                    # Semester/Year
                    if re.search(r'(Fall|Spring|Summer|Winter)\s+\d{4}', badge_text):
                        sem_year = self._extract_semester_year(badge_text)
                        semester = sem_year["semester"]
                        year = sem_year["year"]
                    
                    # International status
                    elif badge_text == "International":
                        international = "International"
                    elif badge_text == "American":
                        international = "American"
                    
                    # GPA
                    elif badge_text.startswith("GPA"):
                        gpa_match = re.search(r'GPA\s+([\d.]+)', badge_text)
                        if gpa_match:
                            gpa = gpa_match.group(1)
                
                # Extract GRE scores from badges
                gre_scores = self._extract_gre_scores(badge_texts)
                
                # Look for comments row (next sibling with paragraph)
                comment_row = detail_row.find_next_sibling('tr', class_='tw-border-none')
                if comment_row:
                    comment_p = comment_row.find('p', class_='tw-text-gray-500')
                    if comment_p:
                        comments = comment_p.get_text(strip=True)
            
            # Build entry dictionary
            entry = {
                "university": university,
                "program": program,
                "degree": degree,
                "added_date": added_date,
                "decision_status": status,
                "decision_date": decision_date,
                "url": url,
                "comments": comments,
                "semester": semester,
                "year": year,
                "international": international,
                "gre_score": gre_scores["gre_score"],
                "gre_verbal": gre_scores["gre_verbal"],
                "gre_writing": gre_scores["gre_writing"],
                "gpa": gpa,
            }
            
            return entry
            
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    def scrape_search_page(self, page: int = 1) -> List[Dict]:
        """
        Scrape a single results page.
        
        Args:
            page: Page number to scrape
            
        Returns:
            List of applicant entries
        """
        # Build URL with page parameter
        if page == 1:
            url = self.SURVEY_URL
        else:
            url = f"{self.SURVEY_URL}?page={page}"
        
        print(f"Scraping page {page}: {url}")
        
        html = self._make_request(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the results table
        table = soup.find('table', class_='tw-min-w-full')
        if not table:
            print(f"No table found on page {page}")
            return []
        
        tbody = table.find('tbody')
        if not tbody:
            print(f"No tbody found on page {page}")
            return []
        
        entries = []
        rows = tbody.find_all('tr', recursive=False)
        
        i = 0
        while i < len(rows):
            row = rows[i]
            
            # Check if this row has the main data (has 5 cells)
            cells = row.find_all('td')
            if len(cells) >= 5:
                # This is a main data row
                # Next row should be the details row with badges
                detail_row = rows[i + 1] if i + 1 < len(rows) else None
                
                entry = self._parse_entry(row, detail_row)
                if entry:
                    entries.append(entry)
                
                # Skip the detail row(s) - there may be multiple detail rows
                i += 1
                # Skip additional detail/comment rows
                while i < len(rows) and rows[i].find('td', attrs={'colspan': True}):
                    i += 1
            else:
                i += 1
        
        print(f"Found {len(entries)} entries on page {page}")
        return entries
    
    def scrape_data(self, max_pages: int = 150) -> List[Dict]:
        """
        Main scraping function to gather all applicant data.
        
        Args:
            max_pages: Maximum number of pages to scrape (20 entries per page)
            
        Returns:
            List of all applicant entries
        """
        all_entries = []
        
        for page in range(1, max_pages + 1):
            entries = self.scrape_search_page(page=page)
            
            if not entries:
                print(f"No more entries found. Stopping at page {page}")
                break
            
            all_entries.extend(entries)
            
            print(f"Total entries collected: {len(all_entries)}")
            
            # Check if we have enough entries
            if len(all_entries) >= 30000:
                print(f"Reached target of 30,000+ entries")
                break
        
        return all_entries


def save_data(data: List[Dict], filename: str = "applicant_data.json") -> None:
    """
    Save scraped data to JSON file.
    
    Args:
        data: List of applicant entries
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} entries to {filename}")


def load_data(filename: str = "applicant_data.json") -> List[Dict]:
    """
    Load data from JSON file.
    
    Args:
        filename: Input filename
        
    Returns:
        List of applicant entries
    """
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} entries from {filename}")
    return data


if __name__ == "__main__":
    # Example usage
    scraper = GradCafeScraper(delay=1.5)
    
    print("Starting Grad Cafe scraper...")
    print("This will take some time to gather 30,000+ entries respectfully.")
    
    # Scrape data (about 1500 pages for 30,000 entries at ~20 per page)
    data = scraper.scrape_data(max_pages=1500)
    
    # Save to file
    save_data(data, "applicant_data.json")
    
    print(f"\nScraping complete! Collected {len(data)} entries.")