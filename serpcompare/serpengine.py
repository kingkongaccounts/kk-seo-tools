import time
import base64
import asyncio
import httpx

class DfsEngine:
  def __init__(self, username, password):
    # Setup the Base URL for the API and the the Request Headers
    self.base_url = "https://api.dataforseo.com/v3/serp/google/organic/live/regular"
    self.username = username
    self.password = password
    base64_bytes = base64.b64encode(("%s:%s" % (self.username, self.password)).encode("ascii")).decode("ascii")
    self.headers = {'Authorization' : 'Basic %s' %  base64_bytes, 'Content-Encoding' : 'gzip'}
  
  # Function to get UULE value for a location name for geo-location search targeting
  def get_location_uule(self, location_name):
    # Mapping of location name length with their corresponding UULE secret
    location_value_map = {
      4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J',
      10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P',
      16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U', 21: 'V',
      22: 'W', 23: 'X', 24: 'Y', 25: 'Z', 26: 'a', 27: 'b',
      28: 'c', 29: 'd', 30: 'e', 31: 'f', 32: 'g', 33: 'h',
      34: 'i', 35: 'j', 36: 'k', 37: 'l', 38: 'm', 39: 'n',
      40: 'o', 41: 'p', 42: 'q', 43: 'r', 44: 's', 45: 't',
      46: 'u', 47: 'v', 48: 'w', 49: 'x', 50: 'y', 51: 'z',
      52: '0', 53: '1', 54: '2', 55: '3', 56: '4', 57: '5',
      58: '6', 59: '7', 60: '8', 61: '9', 62: '-', 63: ' ',
      64: 'A', 65: 'B', 66: 'C', 67: 'D', 68: 'E', 69: 'F', 
      70: 'G', 71: 'H', 72: 'I', 73: 'J', 76: 'M', 83: 'T', 
      89: 'L'
    }
    # Get the length of location_name for UULE secret
    location_value = len(location_name)
    # Get the UULE secret character from the above mapping or None if no mapping is found
    uule_secret = location_value_map.get(location_value, None)
    
    # Convert the location name to bytes
    location_bytes = location_name.encode('utf-8')
    # Encode the location bytes in base64
    location_base64_bytes = base64.b64encode(location_bytes)
    # Convert the location base64 bytes back to string
    location_base64_string = location_base64_bytes.decode('utf-8')
    
    # Return the UULE string by combining the UULE Secret and Base64 Encoded Location Name
    return f'w+CAIQICI{uule_secret}{location_base64_string}'
  
  # Old Function to get the Search URL for the given query to be used for fetching SERP results
  def get_search_url(self, query, lang, country, geolocation):
    # Create the Search URL including the Search Location if provided
    base_url = 'http://www.google.com/search?'
    if geolocation:
      params = f'q={query}&hl={lang}&gl={country}&uule={self.get_location_uule(geolocation)}&brd_json=1'
    else:
      params = f'q={query}&hl={lang}&gl={country}&brd_json=1'
    # Return the final Search URL by combining the Base URL with the Parameters
    return base_url + params
  
  # Asynchronous function to fetch the SERP Results via the SERP API based on the given parameters
  async def fetch_serp(self, client: httpx.AsyncClient, keyword: str, lang: str, country: str):
    # Setup post data as a JSON array to be sent for the SERP request
    post_data = dict()
    post_data[len(post_data)] = {
      "keyword": keyword,
      "depth": 10,
      "language_code": lang,
      "location_name": country
    }
    
    try:   
      print(f"Fetching SERP Results for keyword '{keyword}'!")
      serp_results = await client.post(self.base_url, json=post_data, headers=self.headers, timeout=15)
      if serp_results:
        print(f"SERP Results fetched for keyword '{keyword}'!")
        return serp_results.json()
      else:
        print(f"Failed to fetch SERP Results for keyword '{keyword}'! Status code: {serp_results.status_code}")
        return None
    except Exception as e:
      # Catch for any unexpected errors
      print(f"An unexpected error occurred: {str(e)}")
      return None
    
  # Function to extract just the Organic Results from the SERP Results
  def get_organic_results(self, serp_results: dict):
    # Grab just the Results Array from the SERP Results
    results = serp_results['tasks'][0]['result'][0]['items']
    
    # Filter and extract just the Organic Results from the Results Array
    organic_results = []
    for item in results:
      if item['type'] == "organic":
        organic_results.append(item)
        
    return organic_results
   
  # Function to mark the Common items in both SERP Results and calculate Similarity Percent
  def mark_and_calculate_similarity(self, results1, results2):
    # Initialize sets to track unique links
    links1 = set()
    links2 = set()

    # Initialize counters for common items
    common_items_count = 0

    # First pass to populate sets and mark 'isCommon' in results1
    for item in results1:
      link = item['url']
      links1.add(link)
      # Preemptively mark all as uncommon; will correct if found common later
      item['isCommon'] = False

    # Second pass for results2, check against links1 for commonality, and mark 'isCommon'
    for item in results2:
      link = item['url']
      links2.add(link)
      # Check if common and mark, also increment common counter if common
      if link in links1:
        item['isCommon'] = True
        common_items_count += 1  # Increment if common
      else:
        item['isCommon'] = False

    # Now, correct 'isCommon' for results1 with knowledge of links2
    for item in results1:
      if item['url'] in links2:
        item['isCommon'] = True

    # Calculate similarity percentage based on the smaller set
    smaller_set_length = min(len(links1), len(links2))
    similarity_percent = (common_items_count / smaller_set_length) * 100 if smaller_set_length > 0 else 0

    return results1, results2, similarity_percent 
    
# Test Scripts
async def main():
  engine = DfsEngine("contact@tixort.au", "54acd97ad552c5f4")
  client = httpx.AsyncClient()

  query = "kids wallpaper"
  results = await engine.fetch_serp(client, query, "en", "Australia")
  
  print(results)
  
  if results:
    organic_results = engine.get_organic_results(results)

    for item in organic_results:
      print(f"{item['rank_group']} : {item['url']}")
      print(f"{item['title']}")
    print(f"Results Count: {len(organic_results)}")
  else:
    pass
  
if __name__ == '__main__':
    asyncio.run(main())
  