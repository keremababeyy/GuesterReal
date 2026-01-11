from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import csv
import subprocess
import time
import requests
from datetime import datetime

app = Flask(__name__, static_folder='.')
CORS(app)

# File paths
CSV_PATH = '/Users/keremababey/Desktop/Guester Panel/Fetch Online Reviews/classified_reviews_all_pages.csv'
LAMARTINE_SCRAPER_PATH = '/Users/keremababey/Desktop/Guester Panel/Fetch Online Reviews/scraper_lamartine.py'
DYNAMIC_SCRAPER_PATH = '/Users/keremababey/Desktop/Guester Panel/Fetch Online Reviews/main.py'

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'guester.html')

@app.route('/api/load-reviews', methods=['GET'])
def load_reviews():
    """Load reviews from CSV. If CSV doesn't exist, run Lamartine scraper first."""
    try:
        # Check if CSV exists
        if not os.path.exists(CSV_PATH):
            print("CSV file not found. Running Lamartine scraper...")
            # Run scraper_lamartine.py to create CSV with Lamartine reviews
            result = subprocess.run(['python3', LAMARTINE_SCRAPER_PATH], 
                                  capture_output=True, 
                                  text=True,
                                  cwd=os.path.dirname(LAMARTINE_SCRAPER_PATH))
            
            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'message': f'Failed to create CSV: {result.stderr}'
                }), 500
            
            # Wait a bit for file to be fully written
            time.sleep(2)
        
        # Read CSV file
        reviews = []
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['platform'] = 'Booking.com'  # Add platform field
                reviews.append(row)
        
        print(f"Loaded {len(reviews)} reviews from CSV")
        return jsonify({
            'success': True,
            'data': reviews,
            'count': len(reviews)
        })
        
    except Exception as e:
        print(f"Error loading reviews: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/refresh-reviews', methods=['POST'])
def refresh_reviews():
    """Run Lamartine scraper to fetch new reviews, then load the updated CSV"""
    try:
        print("Starting Lamartine review refresh...")
        
        # Run scraper_lamartine.py
        result = subprocess.run(['python3', LAMARTINE_SCRAPER_PATH], 
                              capture_output=True, 
                              text=True,
                              cwd=os.path.dirname(LAMARTINE_SCRAPER_PATH),
                              timeout=600)  # 10 minute timeout
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': f'Scraper failed: {result.stderr}'
            }), 500
        
        # Wait 7 seconds as requested
        time.sleep(7)
        
        # Read the updated CSV
        reviews = []
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['platform'] = 'Booking.com'
                reviews.append(row)
        
        print(f"Refresh complete! Loaded {len(reviews)} reviews")
        return jsonify({
            'success': True,
            'data': reviews,
            'count': len(reviews),
            'message': f'Successfully refreshed! {len(reviews)} Lamartine reviews loaded.'
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': 'Scraper timeout - took longer than 10 minutes'
        }), 500
    except Exception as e:
        print(f"Error refreshing reviews: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# Keep the existing search hotels endpoint
@app.route('/api/search-hotels', methods=['POST'])
def search_hotels():
    """Search for hotels using Google Places API"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'success': True, 'results': []})
    
    try:
        # Google Places API configuration
        # You'll need to get your API key from: https://console.cloud.google.com/
        GOOGLE_API_KEY = 'AIzaSyCUYvvz89AcDAYlAMQqfrAk4vH42D1M0Vk'
        if not GOOGLE_API_KEY:
            # Fallback to mock data if no API key
            print("⚠️  No Google API key found. Using mock data.")
            print("   Set GOOGLE_PLACES_API_KEY environment variable for real results.")
            return get_mock_hotel_results(query)
        
        # Google Places API - Text Search
        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
        params = {
            'query': f'{query} hotel Istanbul',
            'key': 'AIzaSyCUYvvz89AcDAYlAMQqfrAk4vH42D1M0Vk',
            'type': 'lodging'
        }
        
        response = requests.get(url, params=params, timeout=5)
        google_data = response.json()
        
        if google_data.get('status') != 'OK':
            print(f"Google API returned status: {google_data.get('status')}")
            return get_mock_hotel_results(query)
        
        # Format results
        results = []
        for place in google_data.get('results', [])[:10]:  # Limit to 10 results
            results.append({
                'name': place.get('name', 'Unknown Hotel'),
                'location': place.get('formatted_address', 'Istanbul, Turkey'),
                'rating': place.get('rating', 'N/A'),
                'verified': True
            })
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        print(f"Error searching Google Places: {str(e)}")
        return get_mock_hotel_results(query)

def get_mock_hotel_results(query):
    """Fallback mock results when Google API is not available"""
    query_lower = query.lower()
    
    mock_database = {
        'hilton': [
            {'name': 'Hilton Istanbul Bomonti', 'location': 'Bomonti, Istanbul, Turkey', 'rating': 4.5, 'verified': True},
            {'name': 'Hilton Istanbul Bosphorus', 'location': 'Besiktas, Istanbul, Turkey', 'rating': 4.6, 'verified': True},
            {'name': 'Conrad Istanbul Bosphorus', 'location': 'Ortakoy, Istanbul, Turkey', 'rating': 4.7, 'verified': True}
        ],
        'marriott': [
            {'name': 'Istanbul Marriott Hotel Sisli', 'location': 'Sisli, Istanbul, Turkey', 'rating': 4.4, 'verified': True},
            {'name': 'The Ritz-Carlton Istanbul', 'location': 'Taksim, Istanbul, Turkey', 'rating': 4.8, 'verified': True},
            {'name': 'JW Marriott Istanbul Bosphorus', 'location': 'Besiktas, Istanbul, Turkey', 'rating': 4.6, 'verified': True}
        ],
        'pera': [
            {'name': 'Pera Palace Hotel', 'location': 'Beyoglu, Istanbul, Turkey', 'rating': 4.7, 'verified': True},
            {'name': 'Pera Rose Hotel', 'location': 'Galata, Istanbul, Turkey', 'rating': 4.3, 'verified': True}
        ],
        'lamartine': [
            {'name': 'Lamartine Hotel', 'location': 'Taksim, Istanbul, Turkey', 'rating': 4.7, 'verified': True}
        ]
    }
    
    # Find matching hotels
    results = []
    for key, hotels in mock_database.items():
        if key in query_lower:
            results = hotels
            break
    
    # If no match, create generic results
    if not results:
        results = [
            {'name': f'{query.title()} Hotel', 'location': 'Taksim, Istanbul, Turkey', 'rating': 4.5, 'verified': True},
            {'name': f'{query.title()} Suites', 'location': 'Sultanahmet, Istanbul, Turkey', 'rating': 4.3, 'verified': True},
            {'name': f'{query.title()} Palace', 'location': 'Besiktas, Istanbul, Turkey', 'rating': 4.6, 'verified': True}
        ]
    
    return jsonify({'success': True, 'results': results})

# Keep the existing save hotels endpoint
@app.route('/api/save-hotels', methods=['POST'])
def save_hotels():
    data = request.get_json()
    hotels = data.get('hotels', [])
    
    if not hotels:
        return jsonify({'success': False, 'message': 'No hotels provided'})
    
    hotel_names = []
    
    # ALWAYS include Lamartine Hotel in comparisons (our hotel)
    hotel_names.append("Lamartine Hotel")
    
    print(f"\n{'='*60}")
    print(f"🏨 {len(hotels)} COMPETITOR HOTELS SELECTED + LAMARTINE HOTEL:")
    print(f"   1. Lamartine Hotel (Our Hotel) ⭐")
    
    for i, hotel in enumerate(hotels, 1):
        print(f"   {i + 1}. {hotel['name']} - {hotel['location']}")
        hotel_names.append(hotel['name'])

    fixed_names = ''
    script_path = "/Users/keremababey/Desktop/Guester Panel/Grok Api Url Fetcher/openaient.py"
    
    print(f"{'='*60}\n")
    fixed_names = ", ".join(hotel_names)
    print(f'🔄 Sending to Grok API: {fixed_names}')
    os.system(f'python3 "{script_path}" "{fixed_names}"')
    
    total_hotels = len(hotels) + 1  # +1 for Lamartine
    return jsonify({'success': True, 'message': f'{total_hotels} hotels (including Lamartine) will be compared'})

@app.route('/api/run-scraper-and-benchmark', methods=['POST'])
def run_scraper_and_benchmark():
    """
    Complete workflow:
    1. Run main.py scraper (which reads search_results.json)
    2. Wait for completion
    3. Read classified_reviews_all_pages.csv
    4. Calculate benchmark metrics
    5. Return competitive analysis data
    """
    try:
        from collections import defaultdict
        
        print("\n" + "="*60)
        print("🚀 STARTING SCRAPER AND BENCHMARK GENERATION")
        print("="*60)
        
        # Step 1: Run the dynamic scraper (main.py - reads from search_results.json)
        print("\n📊 Step 1: Running dynamic scraper...")
        result = subprocess.run(
            ['python3', DYNAMIC_SCRAPER_PATH],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(DYNAMIC_SCRAPER_PATH),
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode != 0:
            print(f"❌ Scraper failed: {result.stderr}")
            return jsonify({
                'success': False,
                'message': f'Scraper failed: {result.stderr[:500]}'
            }), 500
        
        print("✅ Scraper completed successfully")
        
        # Step 2: Wait a bit for file to be fully written
        time.sleep(3)
        
        # Step 3: Read and analyze the CSV
        print("\n📈 Step 2: Analyzing reviews and generating benchmarks...")
        
        if not os.path.exists(CSV_PATH):
            return jsonify({
                'success': False,
                'message': 'CSV file not found after scraping'
            }), 500
        
        # Read CSV
        reviews = []
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reviews.append(row)
        
        if not reviews:
            return jsonify({
                'success': False,
                'message': 'No reviews found in CSV'
            }), 500
        
        print(f"📊 Read {len(reviews)} reviews from CSV")
        
        # Group reviews by hotel
        hotel_data = defaultdict(lambda: {
            'positive': 0,
            'negative': 0,
            'total': 0,
            'authors': set(),
            'dates': []
        })
        
        for review in reviews:
            hotel_name = review.get('Hotel_Name', 'Unknown')
            classification = review.get('Classification', '').lower()
            author = review.get('Author', '')
            date = review.get('Date', '')
            
            hotel_data[hotel_name]['total'] += 1
            
            if classification == 'positive':
                hotel_data[hotel_name]['positive'] += 1
            elif classification == 'negative':
                hotel_data[hotel_name]['negative'] += 1
            
            if author and author != 'Unknown Author':
                hotel_data[hotel_name]['authors'].add(author)
            if date and date != 'N/A':
                hotel_data[hotel_name]['dates'].append(date)
        
        # Calculate metrics for each hotel
        benchmarks = []
        for hotel_name, data in hotel_data.items():
            total = data['total']
            positive = data['positive']
            negative = data['negative']
            
            # Calculate sentiment score (percentage of positive reviews)
            sentiment_score = round((positive / total * 100), 1) if total > 0 else 0
            
            # Calculate rating (0-5 scale based on sentiment)
            # 100% positive = 5.0, 0% positive = 1.0
            rating = round(1 + (sentiment_score / 100 * 4), 1)
            
            benchmarks.append({
                'name': hotel_name,
                'total_reviews': total,
                'positive_reviews': positive,
                'negative_reviews': negative,
                'sentiment_score': sentiment_score,
                'rating': rating,
                'unique_reviewers': len(data['authors'])
            })
        
        # Sort by rating (highest first)
        benchmarks.sort(key=lambda x: x['rating'], reverse=True)
        
        print(f"✅ Generated benchmarks for {len(benchmarks)} hotels")
        for bm in benchmarks:
            print(f"   • {bm['name']}: {bm['rating']}★ ({bm['total_reviews']} reviews, {bm['sentiment_score']}% positive)")
        
        print("\n" + "="*60)
        print("✅ SCRAPER AND BENCHMARK GENERATION COMPLETE")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'message': f'Successfully analyzed {len(benchmarks)} hotels',
            'benchmarks': benchmarks,
            'total_reviews': len(reviews)
        })
        
    except subprocess.TimeoutExpired:
        print("❌ Scraper timeout")
        return jsonify({
            'success': False,
            'message': 'Scraper took too long (>30 minutes)'
        }), 500
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/deneme',methods=['GET'])
def denemeFunc():
    return jsonify({'name':'kerem','surname':'ababey'})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Guester System Starting...")
    print("="*60)
    print(f"🌐 Server: http://localhost:5001")
    print(f"📊 CSV Path: {CSV_PATH}")
    print(f"🏨 Lamartine Scraper: {LAMARTINE_SCRAPER_PATH}")
    print(f"🔄 Dynamic Scraper: {DYNAMIC_SCRAPER_PATH}")
    print("="*60 + "\n")
    
    # ALWAYS scrape Lamartine on startup to ensure CSV has data
    print("🏨 Ensuring Lamartine reviews are available...")
    try:
        result = subprocess.run(
            ['python3', LAMARTINE_SCRAPER_PATH],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(LAMARTINE_SCRAPER_PATH),
            timeout=600
        )
        
        if result.returncode == 0:
            print("✅ Lamartine reviews ready!")
        else:
            print("⚠️  Failed to scrape Lamartine on startup")
            print(f"   Error: {result.stderr[:200]}")
    except Exception as e:
        print(f"⚠️  Startup scraper error: {e}")
    
    print("\n" + "="*60)
    print("✅ Server ready to accept connections")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
