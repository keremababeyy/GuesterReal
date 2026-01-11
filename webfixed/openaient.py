import os
import sys
import json
import requests

# --- DYNAMIC FILE PATHS FOR VPS DEPLOYMENT ---
# Detects the directory where this script is sitting
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Replaces the hardcoded Mac paths with paths inside the same folder
# file_path2 was the folder, file_path was the specific txt file
RESULTS_JSON_PATH = os.path.join(BASE_DIR, 'search_results.json')
CACHE_TXT_PATH = os.path.join(BASE_DIR, 'hotel_name_cache.txt')
# --------------------------------------------

API_KEY = 'AIzaSyAilKfZvCkrkoGphG6mSw3pozjEgwF1KuM'
SEARCH_ENGINE_ID = '56ae653510ea24914'
url = 'https://www.googleapis.com/customsearch/v1'

hotel_names = sys.argv[1]
search_query = ''

lst = []
hotel_name_list=[]

if(',' in hotel_names):
    for x in hotel_names.split(','):
        hotel_name_list.append(x)
else:
    hotel_name_list.append(hotel_names)

slug_list=[]
if(len(hotel_name_list)==1):
    params = {
    'q' : f'{hotel_name_list[0]} booking reviews verified',
    'key' : API_KEY,
    'cx' : SEARCH_ENGINE_ID
    }
    response = requests.get(url, params=params)
    results = response.json()
    if 'items' in results:
        filename = results['items'][0]['link'].split('/')[-1]
        slug = filename.split('.html')[0]
        if(".en-gb") in slug:
            slug = filename.split('.en-gb')[0]
        print(slug)
        slug_list.append(slug)
else:
    for item in hotel_name_list:
        params = {
        'q' : f'{item} booking reviews verified',
        'key' : API_KEY,
        'cx' : SEARCH_ENGINE_ID
        }
        response = requests.get(url, params=params)
        results = response.json()
        if 'items' in results:
            filename = results['items'][0]['link'].split('/')[-1]
            slug = filename.split('.html')[0]
            if(".en-gb") in slug:
                slug = filename.split('.en-gb')[0]
            print(slug)
            slug_list.append(slug)

output = {
        "hotel_name": hotel_name_list,
        "links": slug_list
    }
print(json.dumps(output, indent=4))

# Save the search results to the dynamic JSON path
with open(RESULTS_JSON_PATH, 'w') as f:
    json.dump(output, f, indent=4)

print(hotel_name_list)

# Note: I have kept the commented out section below but updated the file_path reference
# for consistency should you ever uncomment it.

'''for item in url_names['hotels']:
    hotel_slug = item['name']
    full_url = f'https://www.booking.com/reviews/tr/hotel/{hotel_slug}.en-gb.html?aid=356980&label=gog235jc-10CA0o5AFCCWxhbWFydGluZUgzWANoqQGIAQGYATO4AQfIAQzYAQPoAQH4AQGIAgGoAgG4AqLB78oGwAIB0gIkNzg3NTA3ODUtODQ1NC00MzAxLWEyZmItNTMzZGNmZmVhZDk42AIB4AIB&sid=9bece4481b541e92cef1e65fb2dd279d&customer_type=total&hp_nav=0&keep_landing=1&order=featuredreviews&page={{page_num}}&r_lang=en&rows=75&'
    lst.append(full_url)
    print(f"✓ Built URL for: {hotel_slug}")

# Save to file using the dynamic cache path
with open(CACHE_TXT_PATH, "w") as f:
    for x in lst:
        f.write(str(x) + "\n")

print(f"\n✅ SUCCESS: Saved {len(lst)} URLs to {CACHE_TXT_PATH}")
'''