import json
import pandas as pd
import requests
from urlparse2 import urlparse
import time
import re
import psycopg2

# variables
REQUEST_HEADERS =  {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
HOST = '127.0.0.1'
USER = 'sierra'
PASSWORD = 'cryptofund'
DB = 'cryptometrics'

##### Helper functions
def get_json(url,wjson):
    parsed_u = urlparse(url)
    if wjson==True:
        # it's a specific .json? link
        url = "{}://{}{}.json?{}".format(parsed_u.scheme, parsed_u.netloc, parsed_u.path, parsed_u.query)
    print "Requesting {}".format(url)
    content = requests.get(url,headers=REQUEST_HEADERS)
    data = json.loads(content.content)
    return data

# convert strings in the form of "[a,b]" to a list
def stringToList(string):
    string = string[1:len(string)-1]
    try:
        if len(string) != 0: 
            tempList = string.split(", ")
            newList = list(map(lambda x: str(x), tempList))
        else:
            newList = []
    except:
        newList = [-9999]
    return(newList)

# Execute a query on a Postgres database and populate a pandas dataframe
def get_table_from_db(query):
    conn = psycopg2.connect( host=HOST, user=USER, password=PASSWORD, dbname=DB , port=5431)
    cur = conn.cursor()
    cur.execute(query)

    names = [x[0] for x in cur.description]
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=names)

    conn.close()
    return df

# populate a Postgres table from a pandas dataframe
def insert_db(df,tablename):
    conn = psycopg2.connect( host=HOST, user=USER, password=PASSWORD, dbname=DB , port=5431)
    cur = conn.cursor()
    #empty the table
    cur.execute('delete from ' + tablename + ';')

    columns_list = df.columns.values.tolist()
    columns = ', '.join(map(str, columns_list))
    #build query
    query = '(' + ','.join(["%s"] * len(columns.split(','))) + ')'
    df = df.fillna("NULL")
    final_query = ','.join(cur.mogrify(query, row.values.tolist()) for index, row in df.iterrows())
    final_query = final_query.replace("'NULL'",'NULL')
    #insert into table
    cur.execute('insert into ' + tablename + ' values ' + final_query)
    print("data inserted")

    cur.close()
    conn.commit()
    conn.close()

#### Import input data with Protocols info 
protocols = pd.read_csv("https://raw.githubusercontent.com/sierra073/aspie/master/data/input/protocols.csv")

protocols['github_repos'] = protocols['github_repos'].apply(lambda x: stringToList(x))
protocols['subreddits'] = protocols['subreddits'].apply(lambda x: stringToList(x))
protocols['stackoverflow'] = protocols['stackoverflow'].apply(lambda x: stringToList(x))
protocols['twitter'] = protocols['twitter'].apply(lambda x: stringToList(x))
protocols['search'] = protocols['search'].apply(lambda x: stringToList(x))

#### wrapper function around whatever API calls are used to get a certain metric if we are appending it to current data
def api_wrapper_append(data,api_func,site,u_srt,u_end,date_col,count_col,sum,allow_multiple_days,tablename):
    counts_by_day = pd.DataFrame([])
    for index, row in protocols.iterrows():
        data_sub = data[data.protocol==row['protocol']]

        if site=='GitHub':
            items = row['github_repos']
        elif site=='Reddit':
            items = row['subreddits']
        elif site=='StackOverflow':
            items = row['stackoverflow']
        elif site=='Twitter':
            items = row['twitter']
        elif site=='Search':
            items = row['search']

        for item in items:
            if item != 'None':
                max_dt = pd.to_datetime(data_sub[date_col]).max()
                if str(max_dt) != 'NaT':
                    count_by_day = api_func(u_srt + item + u_end,max_dt)
                    count_by_day['protocol'] = row['protocol']
                    counts_by_day = counts_by_day.append(count_by_day)

    if not counts_by_day.empty:
        #rename/format columns
        if tablename=='github_commits':
            cols = counts_by_day.columns.tolist()
            cols = cols[::-1]
            counts_by_day = counts_by_day[cols]
        elif tablename!='github_stars':
            cols = counts_by_day.columns.tolist()
            cols = cols[-1:] + cols[:-1]
            counts_by_day = counts_by_day[cols]
        li = [['protocol'], [date_col], count_col]
        counts_by_day.columns = [item for sublist in li for item in sublist]
        counts_by_day[date_col] = pd.to_datetime(counts_by_day[date_col],infer_datetime_format=True).dt.date
        #aggregate
        if sum==True:
            counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol',date_col]).sum()).reset_index()
        elif sum==False:
            counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol',date_col]).size()).reset_index()
        else:
            counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol',date_col]).mean()).round(0).reset_index()
        #rename/format columns again
        li = [['protocol'], [date_col], count_col]
        counts_by_day.columns = [item for sublist in li for item in sublist]
        data[date_col] = pd.to_datetime(data[date_col],infer_datetime_format=True)
        # sort current data and remove latest date
        if allow_multiple_days==True:
            data['date_rank'] = data.sort_values(['protocol',date_col],ascending=False).groupby(['protocol']).cumcount() + 1
            data = data[data.date_rank > 1]
            data = data.drop(['date_rank'],axis=1)
            data = data.reset_index(drop=True)
        if allow_multiple_days==False:
            if data[date_col].max() == counts_by_day[date_col].max():
                data['date_rank'] = data.sort_values(['protocol',date_col],ascending=False).groupby(['protocol']).cumcount() + 1
                data = data[data.date_rank > 1]
                data = data.drop(['date_rank'],axis=1)
                data = data.reset_index(drop=True)

        # append new data and reformat. be overly certain to remove index column and drop any duplicates
        counts_by_day = data.append(counts_by_day,ignore_index=True)
        counts_by_day[date_col] = pd.to_datetime(counts_by_day[date_col])
        counts_by_day = counts_by_day.reset_index()
        counts_by_day = counts_by_day.dropna()
        counts_by_day = counts_by_day.drop_duplicates()
        counts_by_day = counts_by_day.drop(['index'],axis=1)
        counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol',date_col]).max()).reset_index()

        # ensure each protocol is listed
        result_protocols = pd.DataFrame(counts_by_day.groupby('protocol').size()).reset_index()
        for index, row in protocols.iterrows():
            if not (result_protocols['protocol'].str.contains(row['protocol']).any()):
                counts_by_day = counts_by_day.merge(pd.DataFrame({'protocol':row['protocol']},index=[0]),on = 'protocol',how = 'outer')

        # export to Postgres
        insert_db(counts_by_day,tablename)