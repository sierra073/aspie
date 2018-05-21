from initialize_data import *
from access_tokens import *
import pandas as pd
from bs4 import BeautifulSoup
#import twitter

# twitterapi = twitter.Api(consumer_key=twitter_consumer_key,
#                          consumer_secret=twitter_consumer_secret,
#                          access_token_key=twitter_access_token_key,
#                          access_token_secret=twitter_access_token_secret)


# def get_twitter_status_data(x, max_dt):

#     count = 100
#     results = twitterapi.GetSearch(
#         raw_query="q=" + x + "&%23" + x + "&result_type=recent&since=" + max_dt + "&count=100")

#     data = pd.DataFrame([])
#     for r in results:
#         tweet = pd.DataFrame({'date': r.created_at, 'id': r.id}, index=[0])
#         tweet['date'] = pd.to_datetime(tweet['date'])
#         data = data.append(tweet, ignore_index=True)

#     while (pd.to_datetime(data['date'].min(), unit='s') >= pd.to_datetime(max_dt)):
#         min_id = data['id'].min()
#         print(count)

#         results = twitterapi.GetSearch(
#             raw_query="q=" + x + "&%23" + x + "&result_type=recent&" + "max_id=" + str(min_id) + "&since=" + max_dt + "&count=100")

#         for r in results:
#             tweet = pd.DataFrame({'date': r.created_at, 'id': r.id}, index=[0])
#             tweet['date'] = pd.to_datetime(tweet['date'])
#             data = data.append(tweet, ignore_index=True)

#         count += 100  # increment counter

#     if not data.empty:
#         data = data.groupby('date').id.nunique().reset_index()
#     else:
#         data['date'] = max_dt
#         data['id'] = 0

#     return(data)


def get_twitter_followers(url, max_dt):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    f = soup.find_all(class_="stat stat-last")
    f0 = f[0]
    nf = f0.find(class_="statnum")
    num_followers = int(nf.contents[0].replace(',', ''))
    followers_dt = pd.DataFrame({'date': pd.to_datetime('now'), 'followers': num_followers}, index=[0])
    return(followers_dt)


twitter_followers = get_table_from_db('select * from twitter_followers;')
api_wrapper_append(twitter_followers, get_twitter_followers, 'Twitter', "https://twitter.com/", "", 'date', ['follower_count'], True, False, 'twitter_followers')
print("done")
