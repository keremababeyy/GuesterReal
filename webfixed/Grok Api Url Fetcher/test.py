import requests
import json
API_KEY = 'AIzaSyAilKfZvCkrkoGphG6mSw3pozjEgwF1KuM'
SEARCH_ENGINE_ID = '56ae653510ea24914'
url = 'https://www.googleapis.com/customsearch/v1'

search_query = 'Lamartine Hotel Booking Reviews Verified'

params = {
    'q' : search_query,
    'key' : API_KEY,
    'cx' : SEARCH_ENGINE_ID
    }

response = requests.get(url, params=params)
results = response.json()

if 'items' in results:
        print(results['items'][0]['link'])