from initialize_data import *
from access_tokens import *
from datetime import datetime

##### Get data from GitHub API 
base = 'https://api.github.com/repos/'
token = "access_token=" + github_access_token

# Function to get all stars by day, using Pagination
def get_star_pages(url,max_dt):
  all_results = pd.DataFrame([])
  print("Requesting " + url + "/stargazers?page=1&per_page=100&" + token)
  r = requests.get(url + "/stargazers?page=1&per_page=100&" + token, headers = {'Accept': 'application/vnd.github.v3.star+json'} )
  if 'Link' in r.headers:
      last = r.headers['Link'].split(',')[1].split("?page=")[1].split("&per_page")[0]
  else:
      last = 1

  # get minimum date on last page
  r = requests.get(url + "/stargazers?page=" + str(last) + "&per_page=100&" + token, headers = {'Accept': 'application/vnd.github.v3.star+json'} )
  results = json.loads(r.content)
  if len(results) > 1:
      d = pd.DataFrame(results)
  if len(results) == 1:
      d = pd.DataFrame(results, index = [0])
    
  # if still >= max_dt, go back a page
  min_last = pd.to_datetime(d['starred_at'].min(),infer_datetime_format=True)
  pg = int(last)

  while min_last >= max_dt and pg > 0:
      r = requests.get(url + "/stargazers?page=" + str(pg) + "&per_page=100&" + token, headers = {'Accept': 'application/vnd.github.v3.star+json'} )
      results = json.loads(r.content)
        
      if len(results) > 1:
          d = pd.DataFrame(results)
          all_results = all_results.append(d, ignore_index=True)
      elif len(results) == 1:
          d = pd.DataFrame(results, index = [0])
          all_results = all_results.append(d, ignore_index=True)
      else:
          break
      min_last = pd.to_datetime(d['starred_at'].min(),infer_datetime_format=True)
      pg -= 1

  return all_results 

# stars by day for each repo
github_stars = get_table_from_db('select * from github_stars;')
api_wrapper_append(github_stars,get_star_pages,'GitHub',base,"",'date',['star_count'],False,True,'github_stars')
print("stars done")