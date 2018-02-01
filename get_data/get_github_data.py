from initialize_data import *
from access_tokens import *
from datetime import datetime

##### Get data from GitHub API 
base = 'https://api.github.com/repos/'
commits = '/stats/commit_activity'
token = "access_token=" + github_access_token

# commits by week 
github_commits =  get_table_from_db('select * from github_commits;')

def get_commits(url, max_dt):
	commits_by_week = get_json(url,wjson=False)
	github_commits_by_week = pd.DataFrame(commits_by_week)
	if not github_commits_by_week.empty:
		github_commits_by_week['week_date'] = pd.to_datetime(github_commits_by_week['week'],unit='s')
		github_commits_by_week = github_commits_by_week[github_commits_by_week.week_date >= max_dt]
		github_commits_by_week = github_commits_by_week.drop(['week','days'],axis=1)
	return github_commits_by_week

api_wrapper_append(github_commits,get_commits,'GitHub',base,commits+'?'+token,'week_date',['commit_count'],True,True,'github_commits')
print("commits by week done")

# total commits in the past year, total stars, total forks, earliest creation date
github_data_total_sum = pd.DataFrame([])
github_data_total_dt = pd.DataFrame([])
github_commits = get_table_from_db('select * from github_commits;')

for index, row in protocols.iterrows():

	for repo in row['github_repos']:
		if repo != 'None':
			repoItems = get_json(base+repo+'?'+token,wjson=False) 
			repo_data_total_sum = pd.DataFrame({
								'total_stars_count' : repoItems['stargazers_count'],
								'total_forks_count' : repoItems['forks_count'],
								'total_commits_past_year': github_commits[github_commits.protocol==row['protocol']]['commit_count'].sum()
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


insert_db(github_data_total_final,'github_data_total')
print("done")