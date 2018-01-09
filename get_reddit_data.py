from initialize_data import *
from access_tokens import *
import praw

reddit = praw.Reddit(client_id=reddit_clientid,
                     client_secret=reddit_secret, password=reddit_password,
                     user_agent='aspie1', username=reddit_username)

subreddit = reddit.subreddit('Ethereum').new(limit=10)
for submission in subreddit:
    print(submission.title)