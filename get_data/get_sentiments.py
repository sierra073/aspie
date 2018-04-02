import requests, json
import time
from datetime import datetime
from initialize_data import *
from access_tokens import *
import praw
import tweepy
import numpy as np
from textblob import TextBlob

def get_sentiment_page(subreddit):

    url = 'https://www.reddit.com/r/' + subreddit
    r2 = requests.get("https://api.havenondemand.com/1/api/sync/analyzesentiment/v2?url=" + url + '&apikey=fe6dea49-084f-4cd8-be86-0976baf9a714')
    if(r2.status_code == 200):
        data2 = json.loads(r2.text)
        return data2['sentiment_analysis'][0]['aggregate']['score']
    else:
        print("Error return code = "+str(r2.status_code))

def get_forum_texts():
    texts = []
    reddit = praw.Reddit(client_id=reddit_clientid,
                         client_secret=reddit_secret,
                         user_agent=reddit_username)

    for submission in reddit.subreddit('cryptocurrency').hot(limit=200):
        texts.append(submission.selftext)

        for comment in submission.comments[:]:
            if hasattr(comment, 'created'):
                texts.append(comment.body)
            else:
                pass
    print("got forum")
    return texts

def get_tweets(keywords):
    # set twitter api credentials
    consumer_key= twitter_consumer_key
    consumer_secret= twitter_consumer_secret
    access_token=twitter_access_token_key
    access_token_secret=twitter_access_token_secret

    # access twitter api via tweepy methods
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    twitter_api = tweepy.API(auth)

    #while True:
    # fetch tweets by keywords
    tweets = []
    for kw in keywords:
        print kw
        tweet = tweepy.Cursor(twitter_api.search, q=kw, tweet_mode='extended').items(100)
        tweets.append([t._json['full_text'] for t in tweet])
        time.sleep(45)

    tweets = [item for sublist in tweets for item in sublist]
    return tweets

def get_polarity(texts,keywords):
    sentiment_out = []
    print len(texts)
    for text in texts: 
        for keyword in keywords:
            if keyword in text:
                analysis = TextBlob(text)
                sentiment_out.append(analysis.sentiment.polarity)
                break
    return np.mean(sentiment_out)

def insert_db_today(df,tablename):
    conn = psycopg2.connect( host=HOST, user=USER, password=PASSWORD, dbname=DB , port=5432)
    cur = conn.cursor()
    #format today's date
    today = datetime.now()
    month_string = str(today.month)
    if len(month_string) < 2:
        month_string = "0" + month_string
    day_string = str(today.day)
    if len(day_string) < 2:
        day_string = "0" + day_string
    date_string = str(today.year) + '-' + month_string + '-' + day_string
    cur.execute("delete from " + tablename + " where date = '" + date_string +"';")
    columns_list = df.columns.values.tolist()
    columns = ', '.join(map(str, columns_list))
    #build query
    query = '(' + ','.join(["%s"] * len(columns.split(','))) + ')'
    df = df.fillna("NULL")
    final_query = ','.join(cur.mogrify(query, row.values.tolist()) for index, row in df.iterrows())
    final_query = final_query.replace("'NULL'",'NULL')
    #insert into table
    cur.execute('insert into ' + tablename + '(protocol,date,reddit_forum,twitter,sentiment_avg) values ' + final_query)
    print("data inserted")

    cur.close()
    conn.commit()
    conn.close()

def main():
    #reddit_sentiments_protocol = pd.DataFrame([])
    keyword_sentiments = pd.DataFrame([])
    forum_texts = get_forum_texts()

    for index, row in protocols.iterrows():
        print row['protocol']
        # subreddits = row['subreddits']
        # subreddits = [s for s in subreddits if s != 'None']
        # for sub in subreddits:
        #     value = get_sentiment_page(sub)
        #     reddit_sentiments_single = pd.DataFrame({'protocol': row['protocol'],
        #                                              'date': pd.to_datetime(datetime.now()).date(),
        #                                              'reddit_individual': value}, index=[0])
        #     reddit_sentiments_protocol = reddit_sentiments_protocol.append(reddit_sentiments_single)

        keywords = row['sentiment_keywords']
        tweets = get_tweets(keywords)

        reddit_forum = get_polarity(forum_texts,keywords)
        twitter = get_polarity(tweets,keywords)

        keyword_sentiments_protocol = pd.DataFrame({'protocol': row['protocol'],
                                         'date': pd.to_datetime(datetime.now()).date(),
                                         'reddit_forum': reddit_forum,
                                         'twitter': twitter}, index=[0])
        keyword_sentiments = keyword_sentiments.append(keyword_sentiments_protocol)

    #reddit_sentiments_indiv = pd.DataFrame(reddit_sentiments_protocol.groupby(['protocol','date']).mean()).round(3).reset_index()
    sentiments_final = keyword_sentiments.reset_index(drop=True)
    #sentiments_final = reddit_sentiments_indiv.merge(keyword_sentiments, how='outer', on = ['protocol','date'])
    sentiments_final['sentiment_avg'] =np.where(sentiments_final['reddit_forum'].isnull(), 
                                                sentiments_final['twitter'], 
                                                sentiments_final['reddit_forum']*.1 + sentiments_final['twitter']*.9)
    sentiments_final = sentiments_final[['protocol','date','reddit_forum','twitter','sentiment_avg']]
    print("got all sentiments")
    insert_db_today(sentiments_final,'protocols_sentiment')

main()