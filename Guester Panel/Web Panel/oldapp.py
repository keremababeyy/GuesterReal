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
SCRAPER_PATH = '/Users/keremababey/Desktop/Guester Panel/Fetch Online Reviews/main.py'

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'guester.html')

@app.route('/api/load-reviews', methods=['GET'])
def load_reviews():
    """Load reviews from CSV. If CSV doesn't exist, run main.py first."""
    try:
        # Check if CSV exists
        if not os.path.exists(CSV_PATH):
            print("CSV file not found. Running scraper...")
            # Run main.py to create CSV
            result = subprocess.run(['python3', SCRAPER_PATH], 
                                  capture_output=True, 
                                  text=True,
                                  cwd=os.path.dirname(SCRAPER_PATH))
            
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
    """Run main.py to fetch new reviews, then load the updated CSV"""
    try:
        print("Starting review refresh...")
        
        # Run main.py scraper
        result = subprocess.run(['python3', SCRAPER_PATH], 
                              capture_output=True, 
                              text=True,
                              cwd=os.path.dirname(SCRAPER_PATH),
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
            'message': f'Successfully refreshed! {len(reviews)} reviews loaded.'
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
    print(f"\n{'='*60}")
    print(f"🏨 {len(hotels)} HOTELS SELECTED:")
    for i, hotel in enumerate(hotels, 1):
        print(f"   {i}. {hotel['name']} - {hotel['location']}")
        hotel_names.append(hotel['name'])

    fixed_names = ''
    script_path = "/Users/keremababey/Desktop/Guester Panel/Grok Api Url Fetcher/openaient.py"
    
    print(f"{'='*60}\n")
    fixed_names = ", ".join(hotel_names)
    print('output: '+fixed_names)
    os.system(f'python3 "{script_path}" "{fixed_names}"')
    
    return jsonify({'success': True, 'message': f'{len(hotels)} hotels received'})

@app.route('/api/deneme',methods=['GET'])
def denemeFunc():
    return jsonify({'name':'kerem','surname':'ababey'})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Guester System Starting...")
    print("="*60)
    print(f"🌐 Server: http://localhost:5001")
    print(f"📊 CSV Path: {CSV_PATH}")
    print(f"🔄 Scraper: {SCRAPER_PATH}")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
