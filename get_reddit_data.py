from initialize_data import *
from access_tokens import *
import praw
import psraw

reddit = praw.Reddit(client_id=reddit_clientid,
                     client_secret=reddit_secret, password=reddit_password,
                     user_agent='aspie1', username=reddit_username)

# subreddit = reddit.subreddit('Ethereum').new()

# count = 0
# for submission in subreddit:
#     count+=1

# print(count)

print(len(list(psraw.submission_search(reddit, subreddit='Ethereum', limit = 250))))