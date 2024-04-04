import time
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from asgiref.sync import sync_to_async
import asyncio
import httpx
from .serpengine import DfsEngine

# Instantiate the DfsEngine Class for our SerpEngine
serpengine = DfsEngine("contact@tixort.au", "54acd97ad552c5f4")
  
# Homepage View
def home(req):
  return render(req, 'serpcompare/base.html')

# SERP History View
async def serp_history(req):
  # Fetch the Session data for the current request
  session_data = await fetch_session_data(req)
  
  return render(req, 'serpcompare/serp-history.html', {'session_data': session_data})

# Clear SERP History View
async def clear_serp_history(req):
  if (req.method == 'GET'):
    return HttpResponse('URL not found!')
  
  # Clear the Session data for the current request
  await clear_session_data(req)
  
  return render(req, 'serpcompare/serp-history.html', {'session_data': None})

# Function to fetch the session data
@sync_to_async
def fetch_session_data(req):
  # Check and return the session data if it exists otherwise return an empty session data
  session_data = req.session.get('serp_results', {})
  return session_data

# Function to clear the session data
@sync_to_async
def clear_session_data(req):
  # Clear the Session data for the current request
  if 'serp_results' in req.session:
    del req.session['serp_results']

# Handle the Fetch and Compare Request
async def serp_compare(req: HttpRequest):

  if (req.method == 'GET'):
    return HttpResponse('URL not found!')
  
  # Get the values from the Request
  keyword1 = req.POST.get('keyword1')
  keyword2 = req.POST.get('keyword2')
  country_code = req.POST.get('country')
  search_location = req.POST.get('search-location', None)
  
  # Set the default Search language
  lang = 'en'
  
  print(keyword1, keyword2, country_code, search_location)
  
  start_time = time.perf_counter()
  
  # Fetch the Session data for the current request
  session_data = await fetch_session_data(req)

  try:
    # Start an asynchronous context as client
    async with httpx.AsyncClient() as client:
            
      # Check to see if the SERP results are already present for keywords and fetch SERP results accordingly
      if session_data.get(keyword1) and session_data.get(keyword2):
        keyword1_results = session_data[keyword1]
        keyword2_results = session_data[keyword2]     
        print(f"Retrieved SERP Results for both keywords from the session!")
        
      elif session_data.get(keyword1):
        print(f"Retrieved SERP Results for keyword '{keyword1}' from the session!")
        keyword1_results = session_data[keyword1]
        
        # Fetch SERP Result for Keyword 2
        results = await serpengine.fetch_serp(client, keyword2, lang, country_code)
        
        # Store the SERP result for Keyword 2 to the Session data
        keyword2_results = serpengine.get_organic_results(results)
        session_data[keyword2] = keyword2_results
        print(f"Stored SERP Results for keyword '{keyword2}' to the session!")
        
      elif session_data.get(keyword2):
        print(f"Retrieved SERP Results for keyword '{keyword2}' from the session!")
        keyword2_results = session_data[keyword2]
        
        # Fetch SERP Result for Keyword 1
        results = await serpengine.fetch_serp(client, keyword1, lang, country_code)
        
        # Store the SERP result for Keyword 1 to the Session data
        keyword1_results = serpengine.get_organic_results(results)
        session_data[keyword1] = keyword1_results
        print(f"Stored SERP Results for keyword '{keyword1}' to the session!")
        
      else:
        print(f"SERP Results not found for both keywords! Fetching them...")
        # Fetch SERP Results for both keywords
        queries = [keyword1, keyword2]
        # Create an empty task list
        tasks = []
        # Asynchronously fetch the SERP results for each query
        for query in queries:          
          # For the current query, add the task to fetch the SERP results to the tasks list
          tasks.append(asyncio.ensure_future( serpengine.fetch_serp(client, query, lang, country_code) ))
      
        print("All tasks dispatched!")
        # Compile the results by awaiting the responses for all the tasks
        results = await asyncio.gather(*tasks)
        print("All tasks complete!")
      
        # Extract the Organic SERP Results for each keywords and store them in the Session data
        if results[0]:
          keyword1_results = serpengine.get_organic_results(results[0])
          
          session_data[keyword1] = keyword1_results
          print(f"Stored SERP Results for keyword '{keyword1}' to the session!")
        if results[1]:
          keyword2_results = serpengine.get_organic_results(results[1])
          
          session_data[keyword2] = keyword2_results
          print(f"Stored SERP Results for keyword '{keyword2}' to the session!")
        
      # Update the Session data for the request
      req.session['serp_results'] = session_data
      
      end_time = time.perf_counter()
      print(len(keyword1_results), len(keyword2_results))
      print(f'Time taken for API Call: {end_time - start_time} seconds.')
        
    st = time.perf_counter()
    # Get the Similarity Percent between the above two SERP Results and also mark the Common items between them
    keyword1_results, keyword2_results, similarity_percent = serpengine.mark_and_calculate_similarity(keyword1_results, keyword2_results)
    et = time.perf_counter()
    print(f'Time taken for finding common items: {et - st} seconds.')
    
    return render(req, 'serpcompare/serp-results.html', {'similarity': round(similarity_percent, 2), 'keyword1': keyword1, 'results1': keyword1_results, 'keyword2': keyword2, 'results2': keyword2_results})
  except Exception as e:
    # Catch-all for any unexpected errors in the above async request
    print(f'An unexpected error occurred while fetching the SERP results: {str(e)}')
    message = 'An unexpected error occurred while fetching the SERP results. Please try again!'
    return render(req, 'serpcompare/serp-results-error.html', {'message': message})
