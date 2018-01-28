from initialize_data import *
from access_tokens import *
import pandas as pd

## Subreddit posts by day
reddit_posts = pd.read_csv("../data/output/reddit_posts.csv")
reddit_posts = reddit_posts[reddit_posts.protocol != 'Bitcoin']

def get_subreddit(u,max_dt):

	used_id = set()
	subreddit_dt = pd.DataFrame([])
	subreddit_dts = pd.DataFrame([])
	parsed_u = urlparse(u) 
	u = "{}://{}{}{}".format(parsed_u.scheme, parsed_u.netloc, parsed_u.path,parsed_u.query)
	data = get_json(u,wjson=True)
	count = 25
	after = data['data']['after'] # get our initial 'after' variable for the url

	# load the first page of data before entering the loop
	for entry in data['data']['children']:
		dt = int(entry['data']['created_utc'])
		if (not entry['data']['id'] in used_id) and (pd.to_datetime(dt,unit='s') >= max_dt):
			# add the id and date to our lists
			used_id.add(entry['data']['id']) 
			subreddit_dt = pd.DataFrame({'posted_date' : dt, 'post_id': entry['data']['id']}, index=[0])
			subreddit_dt['posted_date'] = pd.to_datetime(subreddit_dt['posted_date'],unit='s').dt.date
		
		if not subreddit_dt.empty:
			subreddit_dts = subreddit_dts.append(subreddit_dt,ignore_index=True)

	while (pd.to_datetime(dt,unit='s') >= max_dt):

		data = get_json("{}?after={}&count={}".format(u, after, count),wjson=True)
		#iterate our data set
		for entry in data['data']['children']:
			dt = int(entry['data']['created_utc'])
			if (not entry['data']['id'] in used_id) and (pd.to_datetime(dt,unit='s') >= max_dt):
			# add the id and date to our lists
				used_id.add(entry['data']['id']) 
				subreddit_dt = pd.DataFrame({'posted_date' : dt, 'post_id': entry['data']['id']}, index=[0])
				subreddit_dt['posted_date'] = pd.to_datetime(subreddit_dt['posted_date'],unit='s').dt.date
			
			if not subreddit_dt.empty:
				subreddit_dts = subreddit_dts.append(subreddit_dt,ignore_index=True)

		after = data['data']['after'] # set our after variable
		count+=25 # increment counter

	if not subreddit_dts.empty:
		subreddit_dts = subreddit_dts.groupby('posted_date').post_id.nunique().reset_index()
	else:
		subreddit_dts['posted_date'] = max_dt
		subreddit_dts['post_id'] = 0

	return(subreddit_dts)

#Get reddit posts by day for all protocols (starts 1/12/18)
api_wrapper_append(reddit_posts,get_subreddit,'Reddit',"https://reddit.com/r/","/new",'posted_date',['post_id'],True,True,'reddit_posts')
print("subreddit posts done")

## Subscribers by day (starts 1/14/18)
reddit_subs = pd.read_csv("../data/output/reddit_subscribers.csv")

def get_subscribers(u,d): 

	parsed_u = urlparse(u) 
	u = "{}://{}{}{}".format(parsed_u.scheme, parsed_u.netloc, parsed_u.path,parsed_u.query)
	data = get_json(u,wjson=False)
	subscribers_dt =  pd.DataFrame({'date': pd.to_datetime('now'), 'subscribers': data['data']['subscribers']},index=[0])
	return(subscribers_dt)
api_wrapper_append(reddit_subs,get_subscribers,'Reddit',"https://reddit.com/r/","/about.json",'date',['subscribers'],True,False,'reddit_subscribers')
print("done")
