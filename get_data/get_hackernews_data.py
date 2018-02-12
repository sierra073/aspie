from initialize_data import *
import pandas as pd

from hackernews import HackerNews
hn = HackerNews()

all_items = pd.DataFrame([])

for story_id in hn.top_stories(limit=200):
    story = hn.get_item(story_id)
    if story.item_type == 'story':
        story = pd.DataFrame({'item_id': story.item_id, 'title':story.title},index=[0])
        all_items = all_items.append(story)

def get_hackernews_title_count(string,all_items):
    count = 0
    for index, row in all_items.iterrows():
        if row['title'].encode('utf-8').find(string) != -1:
            count +=1

    hackernews_cnt =  pd.DataFrame({'date': pd.to_datetime('now').date(), 'story_count': count},index=[0])
    return hackernews_cnt

data = get_table_from_db('select * from hackernews_stories;')
hackernews_day_count_all = pd.DataFrame([])

for index, row in protocols.iterrows():
    string = row['protocol']
    hackernews_day_count = get_hackernews_title_count(string,all_items)
    hackernews_day_count['protocol'] = string
    cols = hackernews_day_count.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    hackernews_day_count = hackernews_day_count[cols]
    hackernews_day_count_all = hackernews_day_count_all.append(hackernews_day_count)

if data['date'].max() == hackernews_day_count_all['date'].max():
    data['date_rank'] = data.sort_values(['protocol','date'],ascending=False).groupby(['protocol']).cumcount() + 1
    data = data[data.date_rank > 1]
    data = data.drop(['date_rank'],axis=1)
    data = data.reset_index(drop=True)

counts_by_day = data.append(hackernews_day_count_all,ignore_index=True)
counts_by_day['date'] = pd.to_datetime(counts_by_day['date']).dt.date
counts_by_day = counts_by_day.reset_index()
counts_by_day = counts_by_day.drop_duplicates()
counts_by_day = counts_by_day.drop(['index'],axis=1)
counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol','date']).max()).reset_index()

# ensure each protocol is listed
result_protocols = pd.DataFrame(counts_by_day.groupby('protocol').size()).reset_index()
for index, row in protocols.iterrows():
    if not (result_protocols['protocol'].str.contains(row['protocol']).any()):
        counts_by_day = counts_by_day.merge(pd.DataFrame({'protocol':row['protocol']},index=[0]),on = 'protocol',how = 'outer')

insert_db(counts_by_day,'hackernews_stories')
