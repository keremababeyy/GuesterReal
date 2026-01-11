import os
import sys
import json
import requests


file_path2 = "/Users/keremababey/Desktop/Guester Panel/Grok Api Url Fetcher/"
API_KEY = 'AIzaSyAilKfZvCkrkoGphG6mSw3pozjEgwF1KuM'
SEARCH_ENGINE_ID = '56ae653510ea24914'
url = 'https://www.googleapis.com/customsearch/v1'


hotel_names = sys.argv[1]

search_query = ''





file_path = "/Users/keremababey/Desktop/Guester Panel/Grok Api Url Fetcher/hotel_name_cache.txt"
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

with open(f'{file_path2}search_results.json', 'w') as f:
        json.dump(output, f, indent=4)


        
    

print(hotel_name_list)
    # Build URLs
'''for item in url_names['hotels']:
    hotel_slug = item['name']
    full_url = f'https://www.booking.com/reviews/tr/hotel/{hotel_slug}.en-gb.html?aid=356980&label=gog235jc-10CA0o5AFCCWxhbWFydGluZUgzWANoqQGIAQGYATO4AQfIAQzYAQPoAQH4AQGIAgGoAgG4AqLB78oGwAIB0gIkNzg3NTA3ODUtODQ1NC00MzAxLWEyZmItNTMzZGNmZmVhZDk42AIB4AIB&sid=9bece4481b541e92cef1e65fb2dd279d&customer_type=total&hp_nav=0&keep_landing=1&order=featuredreviews&page={{page_num}}&r_lang=en&rows=75&'
    lst.append(full_url)
    print(f"✓ Built URL for: {hotel_slug}")

# Save to file
with open(file_path, "w") as f:
    for x in lst:
        f.write(str(x) + "\n")

print(f"\n✅ SUCCESS: Saved {len(lst)} URLs to {file_path}")
print("\nGenerated URLs:")
for i, url in enumerate(lst, 1):
    slug = url.split('/hotel/')[1].split('.en-gb')[0]
    print(f"  {i}. Slug: {slug}")'''
