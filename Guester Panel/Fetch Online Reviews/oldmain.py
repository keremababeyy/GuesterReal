import os
import csv
import requests
from bs4 import BeautifulSoup
import re
import time

# --- Configuration ---
BASE_URL = "https://www.booking.com/reviews/tr/hotel/lamartine.en-gb.html?aid=356980&label=gog235jc-10CA0o5AFCCWxhbWFydGluZUgzWANoqQGIAQGYATO4AQfIAQzYAQPoAQH4AQGIAgGoAgG4Aqyt1skGwAIB0gIkNTgwNWFkNDQtZTlmMC00NTY2LWFjMDUtNDUxNWMzZjkzMDZl2AIB4AIB&sid=9bece4481b541e92cef1e65fb2dd279d&customer_type=total&hp_nav=0&old_page=0&order=featuredreviews&page={page_num}&r_lang=en&rows=75&"
OUTPUT_FILENAME = "classified_reviews_all_pages.csv"

def detect_total_pages(html_content):
    """Detects the total number of review pages from pagination."""
    soup = BeautifulSoup(html_content, 'lxml')
    max_page = 1
    
    # Look for pagination links
    pagination_links = soup.find_all('a', class_=re.compile(r'pagenumber'))
    for link in pagination_links:
        try:
            page_num = int(link.get_text(strip=True))
            if page_num > max_page:
                max_page = page_num
        except ValueError:
            continue
    
    # Alternative: search in href attributes
    if max_page == 1:
        all_links = soup.find_all('a', href=re.compile(r'page=\d+'))
        for link in all_links:
            match = re.search(r'page=(\d+)', link.get('href', ''))
            if match:
                page_num = int(match.group(1))
                if page_num > max_page:
                    max_page = page_num
    
    return max_page


def extract_and_classify_booking_reviews(html_content, page_num):
    """
    Extracts positive and negative text blocks from HTML content,
    and returns a flat list of classified quotes ready for CSV export.
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # This list will hold a flat structure: one dictionary per quote
        flat_quotes = []

        # Target the main review content container
        review_boxes = soup.find_all('div', class_='review_item_review_content')
        
        if not review_boxes:
            print(f"  ⚠️  Could not find review content on page {page_num}")
            return []

        # Extract data from each box
        for i, box in enumerate(review_boxes):
            
            # --- Quote Extraction ---
            pos_quote_element = box.find('p', class_='review_pos')
            neg_quote_element = box.find('p', class_='review_neg')
            
            positive_quote = pos_quote_element.get_text(" ", strip=True) if pos_quote_element else None
            negative_quote = neg_quote_element.get_text(" ", strip=True) if neg_quote_element else None
            
            # --- Reviewer Data ---
            review_item_wrapper = box.find_parent('div', class_='review_item')
            author = 'Unknown Author'
            review_date = 'N/A'
            
            if review_item_wrapper:
                # Extract author name
                author_element = review_item_wrapper.find('p', class_='reviewer_name')
                author = author_element.text.strip() if author_element else 'Unknown Author'
                
                # Extract review date
                date_element = review_item_wrapper.find('p', class_='review_item_date')
                if not date_element:
                    date_element = review_item_wrapper.find('span', class_='c-review-block__date')
                review_date = date_element.text.strip() if date_element else 'N/A'
            
            # --- Classification and Flattening ---
            
            # If a positive quote exists, add it as a row
            if positive_quote:
                flat_quotes.append({
                    'Review_ID': f"P{page_num}_R{i + 1}",
                    'Author': author,
                    'Date': review_date,
                    'Classification': 'Positive',
                    'Quote_Text': positive_quote
                })
            
            # If a negative quote exists, add it as a separate row
            if negative_quote:
                flat_quotes.append({
                    'Review_ID': f"P{page_num}_R{i + 1}",
                    'Author': author,
                    'Date': review_date,
                    'Classification': 'Negative',
                    'Quote_Text': negative_quote
                })
            
        return flat_quotes

    except Exception as e:
        print(f"  ❌ Error during extraction on page {page_num}: {e}")
        return []


def scrape_all_pages(base_url):
    """Fetches and extracts reviews from all pages until no more reviews are found."""
    
    print("=" * 60)
    print("Starting review scraper - will fetch until no more reviews found...")
    print("=" * 60)
    
    all_reviews = []
    page_num = 1
    consecutive_empty_pages = 0
    max_empty_pages = 3  # Stop after 3 consecutive empty pages
    
    while True:
        page_url = base_url.format(page_num=page_num)
        print(f"\n📄 Fetching page {page_num}...")
        
        try:
            response = requests.get(page_url, timeout=30)
            response.raise_for_status()
            html_content = response.text
            
            # Check if HTML is too short (likely error page)
            if len(html_content) < 1000:
                print(f"  ⚠️  Page {page_num}: HTML too short, likely no content")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= max_empty_pages:
                    print(f"\n🛑 Stopped: {max_empty_pages} consecutive empty pages detected")
                    break
                page_num += 1
                time.sleep(1)
                continue
            
            # Extract reviews from this page
            reviews = extract_and_classify_booking_reviews(html_content, page_num)
            
            if reviews:
                all_reviews.extend(reviews)
                print(f"  ✅ Page {page_num}: Extracted {len(reviews)} quotes (Total so far: {len(all_reviews)})")
                consecutive_empty_pages = 0  # Reset counter on successful page
            else:
                print(f"  ⚠️  Page {page_num}: No reviews found")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= max_empty_pages:
                    print(f"\n🛑 Stopped: {max_empty_pages} consecutive pages with no reviews")
                    break
            
            # Move to next page
            page_num += 1
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error on page {page_num}: {e}")
            consecutive_empty_pages += 1
            if consecutive_empty_pages >= max_empty_pages:
                print(f"\n🛑 Stopped: {max_empty_pages} consecutive errors")
                break
            page_num += 1
            time.sleep(2)  # Longer delay after error
            continue
        
        except Exception as e:
            print(f"  ❌ Unexpected error on page {page_num}: {e}")
            consecutive_empty_pages += 1
            if consecutive_empty_pages >= max_empty_pages:
                print(f"\n🛑 Stopped: {max_empty_pages} consecutive errors")
                break
            page_num += 1
            time.sleep(2)
            continue
    
    print(f"\n✅ Scraping complete! Total pages checked: {page_num - 1}")
    return all_reviews


def save_to_csv(data, output_filename):
    """Saves the flat list of extracted data to a CSV file."""
    if not data:
        print("\n⚠️  No data to save. CSV file not created.")
        return

    # Define the column headers for the CSV
    fieldnames = ['Review_ID', 'Author', 'Date', 'Classification', 'Quote_Text']
    
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Use DictWriter to write dictionaries easily
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader() # Write the header row
            writer.writerows(data) # Write all the data rows
            
        print(f"\n✨ Data successfully saved to {output_filename}")
        print(f"Total quotes saved: {len(data)}")

    except Exception as e:
        print(f"❌ An error occurred while writing the CSV file: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    print("🚀 Starting Booking.com Review Scraper with Pagination\n")
    
    # Scrape all pages
    extracted_data = scrape_all_pages(BASE_URL)

    # Display a preview
    if extracted_data:
        print("\n--- Displaying Classified Data Preview ---")
        for row in extracted_data[:5]:
            print(f"ID: {row['Review_ID']} | Type: {row['Classification']} | Author: {row['Author']}")
            print(f"   Date: {row['Date']}")
            print(f"   Quote: {row['Quote_Text'][:80]}...") # Show first 80 chars
            print()
            
        # Save the data to CSV
        save_to_csv(extracted_data, OUTPUT_FILENAME)
        
        print("\n" + "=" * 60)
        print(f"✅ SUCCESS: Scraped {len(extracted_data)} review quotes from all pages!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ FAILURE: No reviews were extracted.")
        print("=" * 60)
