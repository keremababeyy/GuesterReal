import os
import csv
import requests
from bs4 import BeautifulSoup
import re
import time

# --- DYNAMIC FILE PATHS FOR VPS DEPLOYMENT ---
# Detects the directory where this script is sitting
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensures the CSV is saved in the same folder as the script
OUTPUT_FILENAME = os.path.join(BASE_DIR, "classified_reviews_all_pages.csv")
# --------------------------------------------

LAMARTINE_URL = "https://www.booking.com/reviews/tr/hotel/lamartine.en-gb.html?aid=356980&label=gog235jc-10CA0o5AFCCWxhbWFydGluZUgzWANoqQGIAQGYATO4AQfIAQzYAQPoAQH4AQGIAgGoAgG4AsPH-8oGwAIB0gIkZjBlNDRkZmQtMDgwNy00YWRmLWE5MDctMDlhODQyYzRjZDc02AIB4AIB&sid=9bece4481b541e92cef1e65fb2dd279d&customer_type=total&hp_nav=0&keep_landing=1&order=featuredreviews&page={page_num}&r_lang=en&rows=75&"
HOTEL_NAME = "Lamartine Hotel"

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
                    'Hotel_Name': HOTEL_NAME,
                    'Review_ID': f"LAM_P{page_num}_R{i + 1}",
                    'Author': author,
                    'Date': review_date,
                    'Classification': 'Positive',
                    'Quote_Text': positive_quote
                })
            
            # If a negative quote exists, add it as a separate row
            if negative_quote:
                flat_quotes.append({
                    'Hotel_Name': HOTEL_NAME,
                    'Review_ID': f"LAM_P{page_num}_R{i + 1}",
                    'Author': author,
                    'Date': review_date,
                    'Classification': 'Negative',
                    'Quote_Text': negative_quote
                })
            
        return flat_quotes

    except Exception as e:
        print(f"  ❌ Error during extraction on page {page_num}: {e}")
        return []


def scrape_all_pages():
    """Fetches and extracts reviews from all pages until no more reviews are found."""
    
    print("=" * 60)
    print("🏨 Scraping Lamartine Hotel Reviews")
    print("=" * 60)
    
    all_reviews = []
    page_num = 1
    consecutive_empty_pages = 0
    max_empty_pages = 3  # Stop after 3 consecutive empty pages
    
    while True:
        page_url = LAMARTINE_URL.format(page_num=page_num)
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
    fieldnames = ['Hotel_Name', 'Review_ID', 'Author', 'Date', 'Classification', 'Quote_Text']
    
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Use DictWriter to write dictionaries easily
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()  # Write the header row
            writer.writerows(data)  # Write all the data rows
            
        print(f"\n✨ Data successfully saved to {output_filename}")
        print(f"Total quotes saved: {len(data)}")

    except Exception as e:
        print(f"❌ An error occurred while writing the CSV file: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    print("🚀 Starting Lamartine Hotel Review Scraper\n")
    
    # Scrape all pages
    extracted_data = scrape_all_pages()

    # Display a preview
    if extracted_data:
        print("\n--- Displaying Data Preview ---")
        for row in extracted_data[:3]:
            print(f"ID: {row['Review_ID']} | Type: {row['Classification']} | Author: {row['Author']}")
            print(f"   Date: {row['Date']}")
            print(f"   Quote: {row['Quote_Text'][:80]}...")  # Show first 80 chars
            print()
            
        # Save the data to CSV
        save_to_csv(extracted_data, OUTPUT_FILENAME)
        
        print("\n" + "=" * 60)
        print(f"✅ SUCCESS: Scraped {len(extracted_data)} Lamartine reviews!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ FAILURE: No reviews were extracted.")
        print("=" * 60)