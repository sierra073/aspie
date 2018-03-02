from initialize_data import *
import pandas as pd

# insert activity
conn = psycopg2.connect( host=HOST, user=USER, password=PASSWORD, dbname=DB , port=5432)
cur = conn.cursor()

cur.execute('''delete from protocols_activity_hist;''')

queryfile=open('kpi.sql', 'r')
query = queryfile.read()
queryfile.close()
cur.execute('insert into protocols_activity_hist ' + query)

cur.close()
conn.commit()
conn.close()

activity_hist = get_table_from_db('select * from protocols_activity_hist;')

# insert score
datad = activity_hist.groupby(['date']).size().reset_index()

scores_by_day = pd.DataFrame([])
score_by_day = pd.DataFrame([])

for d in datad['date']:
    datas = activity_hist[activity_hist.date==d]
    datasub = datas.drop(['date','search_count','price'],axis=1)
    datasub = datasub.set_index('protocol').astype(float)
    datas = datas.reset_index(drop=True)
    
    score_by_day['protocol'] = datasub.index
    score_by_day['date'] = d
    
    for col in datasub.columns.tolist():
        col_metric = datasub[col].rank(pct=True,method='min').reset_index()
        score_by_day[col] = col_metric[col]
    
    score_by_day['social_score'] = score_by_day[['reddit_post_count','reddit_subscriber_count','twitter_follower_count','hackernews_count']].mean(axis=1) * 100 
    score_by_day['developer_score'] = score_by_day[['commit_count', 'star_count', 'stack_question_count']].mean(axis=1) * 100
    score_by_day['search_score'] = datas['search_count'].astype(float)
    score_by_day['price'] = datas['price'].astype(float)
    score_by_day['activity_score'] = score_by_day[['social_score','developer_score','search_score']].mean(axis=1)
    score_by_day['kpi'] = score_by_day['price'] / score_by_day['activity_score']
    scores_by_day = scores_by_day.append(score_by_day)

insert_db(scores_by_day[['protocol','date','social_score','developer_score','search_score', 'price','activity_score','kpi']],'protocols_kpi_hist')
print("kpi done")