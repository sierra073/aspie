from initialize_data import *
from access_tokens import *
from datetime import datetime

##### Get data from GitHub API 
base = 'https://api.github.com/repos/'
commits = '/stats/commit_activity'
token = "access_token=" + github_access_token

# Function to get all stars by day, using Pagination
def get_star_pages(url):
	all_results = pd.DataFrame([])
	r = requests.get(url + "/stargazers?page=1&per_page=100&" + token, headers = {'Accept': 'application/vnd.github.v3.star+json'} )
	if 'Link' in r.headers:
		last = r.headers['Link'].split(',')[1].split("?page=")[1].split("&per_page")[0]
	else:
		last = 1

	d = pd.DataFrame(json.loads(r.content))
	all_results = all_results.append(d, ignore_index=True)

	for i in range(1, int(last)+1):
		r = requests.get(url + "/stargazers?page=" + str(i) + "&per_page=100&" + token, headers = {'Accept': 'application/vnd.github.v3.star+json'} )
		results = json.loads(r.content)
		if len(results) > 1:
			d = pd.DataFrame(results)
		if len(results) == 1:
			d = pd.DataFrame(results, index = [0])
		all_results = all_results.append(d, ignore_index=True)
    
	return all_results 

#####

# stars by day for each repo
all_stars = pd.DataFrame([])

for index, row in protocols.iterrows():
	for repo in row['github_repos']:
		if repo != 'None':
			repo_stars = get_star_pages(base + repo)
			repo_stars['protocol'] = row['protocol']
			all_stars = all_stars.append(repo_stars, ignore_index=True)

all_stars['starred_at_date'] = pd.to_datetime(all_stars['starred_at'],infer_datetime_format=True).dt.date
all_stars_final = pd.DataFrame({'count' : all_stars.groupby(['protocol','starred_at_date']).size()}).reset_index()
all_stars_final.to_csv("data/output/github_stars.csv",index=False)

# commits by week
github_commits_by_week = pd.DataFrame([])

for index, row in protocols.iterrows():
	for repo in row['github_repos']:
		if repo != 'None':
			commits_by_week = get_json(base+repo+commits+'?'+token)
			repo_github_commits_by_week = pd.DataFrame(commits_by_week)
			repo_github_commits_by_week['protocol'] = row['protocol']
			github_commits_by_week = github_commits_by_week.append(repo_github_commits_by_week, ignore_index=True)

github_commits_by_week['week_date'] = pd.to_datetime(github_commits_by_week['week'],unit='s')
github_commits_by_week_final = pd.DataFrame(github_commits_by_week.groupby(['protocol','week_date']).sum()).reset_index()
github_commits_by_week_final.to_csv("data/output/github_commits.csv",index=False)


# total commits in the past year, total stars, total forks, earliest creation date
github_data_total_sum = pd.DataFrame([])
github_data_total_dt = pd.DataFrame([])

for index, row in protocols.iterrows():

	for repo in row['github_repos']:
		if repo != 'None':
			repoItems = get_json(base+repo+'?'+token) 
			repo_data_total_sum = pd.DataFrame({
								'total_stars_count' : repoItems['stargazers_count'],
								'total_forks_count' : repoItems['forks_count'],
								'total_commits_past year': github_commits_by_week_final[github_commits_by_week_final.protocol==row['protocol']]['total'].sum()
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

github_data_total_final.to_csv("data/output/github_data_total.csv",index=False)