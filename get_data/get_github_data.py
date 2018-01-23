from initialize_data import *
from access_tokens import *
from datetime import datetime

##### Get data from GitHub API 
base = 'https://api.github.com/repos/'
commits = '/stats/commit_activity'
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
	print("first request done")

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
github_stars = pd.read_csv("../data/output/github_stars.csv")
api_wrapper_append(github_stars,get_star_pages,'GitHub',base,"",'starred_at',['count'],False,True,'github_stars')
print("stars done")

# commits by week
github_commits_by_week = pd.DataFrame([])

for index, row in protocols.iterrows():
	for repo in row['github_repos']:
		if repo != 'None':
			commits_by_week = get_json(base+repo+commits+'?'+token,wjson=False)
			repo_github_commits_by_week = pd.DataFrame(commits_by_week)
			repo_github_commits_by_week['protocol'] = row['protocol']
			github_commits_by_week = github_commits_by_week.append(repo_github_commits_by_week, ignore_index=True)

github_commits_by_week['week_date'] = pd.to_datetime(github_commits_by_week['week'],unit='s')
github_commits_by_week_final = pd.DataFrame(github_commits_by_week.groupby(['protocol','week_date']).sum()).reset_index()

# ensure each protocol is listed
result_protocols = pd.DataFrame(github_commits_by_week_final.groupby('protocol').size()).reset_index()
for index, row in protocols.iterrows():
	if not (result_protocols['protocol'].str.contains(row['protocol']).any()):
		github_commits_by_week_final = github_commits_by_week_final.merge(pd.DataFrame({'protocol':row['protocol']},index=[0]),on = 'protocol',how = 'outer')

github_commits_by_week_final = github_commits_by_week_final.drop('week',axis=1)
github_commits_by_week_final.to_csv("../data/output/github_commits.csv",index=False)
print("commits by week done")

# total commits in the past year, total stars, total forks, earliest creation date
github_data_total_sum = pd.DataFrame([])
github_data_total_dt = pd.DataFrame([])

for index, row in protocols.iterrows():

	for repo in row['github_repos']:
		if repo != 'None':
			repoItems = get_json(base+repo+'?'+token,wjson=False) 
			repo_data_total_sum = pd.DataFrame({
								'total_stars_count' : repoItems['stargazers_count'],
								'total_forks_count' : repoItems['forks_count'],
								'total_commits_past_year': github_commits_by_week_final[github_commits_by_week_final.protocol==row['protocol']]['total'].sum()
								}, index=[0])
			repo_data_total_sum['protocol'] = row['protocol']
			github_data_total_sum = github_data_total_sum.append(repo_data_total_sum, ignore_index=True)

			repo_data_total_dt = pd.DataFrame({
								'created_at' : repoItems['created_at']
								}, index=[0])
			repo_data_total_dt['protocol'] = row['protocol']
			github_data_total_dt = github_data_total_dt.append(repo_data_total_dt, ignore_index=True)

github_data_total_dt['created_at'] = pd.to_datetime(github_data_total_dt['created_at'],infer_datetime_format=True).dt.date
github_data_total_dt = pd.DataFrame(github_data_total_dt.groupby(['protocol']).min()).reset_index()

github_data_total_final = pd.DataFrame(github_data_total_sum.groupby(['protocol']).sum()).reset_index()
github_data_total_final = github_data_total_final.merge(github_data_total_dt, on='protocol')

result_protocols = pd.DataFrame(github_data_total_final.groupby('protocol').size()).reset_index()
for index, row in protocols.iterrows():
	if not (result_protocols['protocol'].str.contains(row['protocol']).any()):
		github_data_total_final = github_data_total_final.merge(pd.DataFrame({'protocol':row['protocol']},index=[0]),on = 'protocol',how = 'outer')


github_data_total_final.to_csv("../data/output/github_data_total.csv",index=False)
print("done")