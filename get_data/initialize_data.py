import json
import pandas as pd
import requests
from urlparse2 import urlparse
import time
import re
import psycopg2
from datetime import datetime, timedelta
import os
import sys

# variables
ASPIE = os.environ.get("ASPIE")
REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
HOST = '159.89.155.200'
USER = 'sbbw'
PASSWORD = 'cryptofund'
DB = 'cryptometrics'

# Helper functions


def get_json(url, wjson):
    parsed_u = urlparse(url)
    if wjson == True:
        # it's a specific .json? link
        url = "{}://{}{}.json?{}".format(parsed_u.scheme, parsed_u.netloc, parsed_u.path, parsed_u.query)
    print "Requesting {}".format(url)
    content = requests.get(url, headers=REQUEST_HEADERS)
    data = json.loads(content.content)
    return data

# convert strings in the form of "[a,b]" to a list


def stringToList(string):
    string = string[1:len(string) - 1]
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
    conn = psycopg2.connect(host=HOST, user=USER, password=PASSWORD, dbname=DB, port=5432)
    cur = conn.cursor()
    cur.execute(query)

    names = [x[0] for x in cur.description]
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=names)

    conn.close()
    return df

# populate a Postgres table from a pandas dataframe


def insert_db(df, tablename):
    conn = psycopg2.connect(host=HOST, user=USER, password=PASSWORD, dbname=DB, port=5432)
    cur = conn.cursor()
    # empty the table
    if tablename != 'reddit_posts':
        cur.execute('delete from ' + tablename + ';')
    else:
        cur.execute('''delete from ''' + tablename + ''' where protocol != 'Bitcoin';''')

    columns_list = df.columns.values.tolist()
    columns = ', '.join(map(str, columns_list))
    # build query
    query = '(' + ','.join(["%s"] * len(columns.split(','))) + ')'
    df = df.fillna("NULL")
    final_query = ','.join(cur.mogrify(query, row.values.tolist()) for index, row in df.iterrows())
    final_query = final_query.replace("'NULL'", 'NULL')
    # insert into table
    cur.execute('insert into ' + tablename + ' values ' + final_query)
    print("data inserted")

    cur.close()
    conn.commit()
    conn.close()


def insert_db_today(df, tablename):
    conn = psycopg2.connect(host=HOST, user=USER, password=PASSWORD, dbname=DB, port=5432)
    cur = conn.cursor()
    # format today's date
    today = datetime.now()
    month_string = str(today.month)
    if len(month_string) < 2:
        month_string = "0" + month_string
    day_string = str(today.day)
    if len(day_string) < 2:
        day_string = "0" + day_string
    date_string = str(today.year) + '-' + month_string + '-' + day_string
    cur.execute("delete from " + tablename + " where date = '" + date_string + "';")
    columns_list = df.columns.values.tolist()
    columns = ', '.join(map(str, columns_list))
    # build query
    query = '(' + ','.join(["%s"] * len(columns.split(','))) + ')'
    df = df.fillna("NULL")
    final_query = ','.join(cur.mogrify(query, row.values.tolist()) for index, row in df.iterrows())
    final_query = final_query.replace("'NULL'", 'NULL')

    if tablename == 'protocols_sentiment':
        cols = ' (protocol,date,reddit_forum,twitter,sentiment_avg) values '
    else:
        cols = ' (protocol,date,count) values '

    # insert into table
    cur.execute('insert into ' + tablename + cols + final_query)
    print("data inserted")

    cur.close()
    conn.commit()
    conn.close()


# Import input data with Protocols info
protocols = pd.read_csv("../data/input/protocols.csv")

protocols['github_repos'] = protocols['github_repos'].apply(lambda x: stringToList(x))
protocols['subreddits'] = protocols['subreddits'].apply(lambda x: stringToList(x))
protocols['stackoverflow'] = protocols['stackoverflow'].apply(lambda x: stringToList(x))
protocols['twitter'] = protocols['twitter'].apply(lambda x: stringToList(x))
protocols['search'] = protocols['search'].apply(lambda x: stringToList(x))
protocols['sentiment_keywords'] = protocols['sentiment_keywords'].apply(lambda x: stringToList(x))

# wrapper function around whatever API calls are used to get a certain metric if we are appending it to current data


def api_wrapper_append(data, api_func, site, u_srt, u_end, date_col, count_col, sum, allow_multiple_days, tablename):
    counts_by_day = pd.DataFrame([])
    for index, row in protocols.iterrows():
        data_sub = data[data.protocol == row['protocol']]

        if site == 'GitHub':
            items = row['github_repos']
        elif site == 'Reddit':
            items = row['subreddits']
        elif site == 'StackOverflow':
            items = row['stackoverflow']
        elif site == 'Twitter':
            items = row['twitter']
        elif site == 'Search':
            items = row['search']

        for item in items:
            if item != 'None':
                max_dt = pd.to_datetime(data_sub[date_col]).max()
                if str(max_dt) != 'NaT':
                    count_by_day = api_func(u_srt + item + u_end, max_dt)
                    count_by_day['protocol'] = row['protocol']
                    counts_by_day = counts_by_day.append(count_by_day)

    if not counts_by_day.empty:
        # rename/format columns
        if tablename == 'github_commits':
            cols = counts_by_day.columns.tolist()
            cols = cols[::-1]
            counts_by_day = counts_by_day[cols]
        elif tablename != 'github_stars':
            cols = counts_by_day.columns.tolist()
            cols = cols[-1:] + cols[:-1]
            counts_by_day = counts_by_day[cols]
        li = [['protocol'], [date_col], count_col]
        counts_by_day.columns = [item for sublist in li for item in sublist]
        counts_by_day[date_col] = pd.to_datetime(counts_by_day[date_col], infer_datetime_format=True).dt.date

        # aggregate
        if sum == True:
            counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol', date_col]).sum()).reset_index()
        elif sum == False:
            counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol', date_col]).size()).reset_index()
        else:
            counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol', date_col]).mean()).round(0).reset_index()

        # rename/format columns again
        li = [['protocol'], [date_col], count_col]
        counts_by_day.columns = [item for sublist in li for item in sublist]
        data[date_col] = pd.to_datetime(data[date_col], infer_datetime_format=True)

        # sort current data and remove latest date
        if allow_multiple_days == True:
            data['date_rank'] = data.sort_values(['protocol', date_col], ascending=False).groupby(['protocol']).cumcount() + 1
            data = data[data.date_rank > 1]
            data = data.drop(['date_rank'], axis=1)
            data = data.reset_index(drop=True)
        if allow_multiple_days == False:
            if data[date_col].max() == counts_by_day[date_col].max():
                data['date_rank'] = data.sort_values(['protocol', date_col], ascending=False).groupby(['protocol']).cumcount() + 1
                data = data[data.date_rank > 1]
                data = data.drop(['date_rank'], axis=1)
                data = data.reset_index(drop=True)

        # append new data and reformat. be overly certain to remove index column and drop any duplicates
        counts_by_day = data.append(counts_by_day, ignore_index=True)
        counts_by_day[date_col] = pd.to_datetime(counts_by_day[date_col])
        counts_by_day = counts_by_day.reset_index()
        counts_by_day = counts_by_day.dropna()
        counts_by_day = counts_by_day.drop_duplicates()
        counts_by_day = counts_by_day.drop(['index'], axis=1)
        counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol', date_col]).max()).reset_index()

        # fill in 0s for missing dates
        if (tablename == 'github_stars' or tablename == 'reddit_posts'):
            counts_by_day_final = pd.DataFrame([])
            for index, row in protocols.iterrows():
                counts_sub = counts_by_day[counts_by_day.protocol == row['protocol']]
                if not counts_sub.empty:
                    idx = pd.period_range(min(counts_sub[date_col]), datetime.now()).to_timestamp()
                    counts_sub = counts_sub.set_index(date_col)
                    counts_sub = counts_sub.reindex(index=idx)
                    counts_sub['protocol'] = counts_sub['protocol'].fillna(value=row['protocol'])
                    counts_sub[count_col] = counts_sub[count_col].fillna(value=0)
                    counts_sub = counts_sub.reset_index()
                    counts_by_day_final = counts_by_day_final.append(counts_sub)
            counts_by_day_final = counts_by_day_final.rename(columns={'index': date_col})
            cols = counts_by_day_final.columns.tolist()
            cols[0], cols[1] = cols[1], cols[0]
            counts_by_day_final = counts_by_day_final[cols]
        else:
            counts_by_day_final = counts_by_day

        # ensure each protocol is listed
        result_protocols = pd.DataFrame(counts_by_day_final.groupby('protocol').size()).reset_index()
        for index, row in protocols.iterrows():
            if not (result_protocols['protocol'].str.contains(row['protocol']).any()):
                counts_by_day_final = counts_by_day_final.merge(pd.DataFrame({'protocol': row['protocol']}, index=[0]), on='protocol', how='outer')

        # export to Postgres
        insert_db(counts_by_day_final, tablename)

# function to decode ethereum hex encoded integers


def decode_eth_hex(string):
    substr = string.split("0x")[1]
    return int(substr, 16)

# function to construct ethereum token address token history url


def make_token_url(fromblock, toblock, address):
    return 'https://api.etherscan.io/api?module=logs&action=getLogs&fromBlock=' + str(fromblock) + '&toBlock=' + str(toblock) + '&address=' + address

# function to get the token transactions count history for a given ethereum address and date offset


def get_token_history(address, offset):
    r = requests.get('http://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey=YourApiKeyToken')
    res = json.loads(r.content)
    lblock = decode_eth_hex(res['result'])

    txns_timestamps = pd.DataFrame([])
    from_tmstmp = datetime.now()

    toblock = lblock
    fromblock = toblock - 30

    while from_tmstmp > datetime.now() - timedelta(days=offset):
        eurl = make_token_url(fromblock, toblock, address)
        r = requests.get(eurl)
        res = json.loads(r.content)

        if res['status'] == '1':
            txns_timestamp = pd.DataFrame(res['result'])
            txns_timestamp['timeStamp'] = txns_timestamp['timeStamp'].apply(decode_eth_hex)
            txns_timestamp['timeStamp'] = txns_timestamp['timeStamp'].apply(datetime.fromtimestamp)
            txns_timestamps = txns_timestamps.append(txns_timestamp[['timeStamp', 'transactionHash']])

            toblock = fromblock
            fromblock = toblock - 30
            from_tmstmp = txns_timestamp['timeStamp'].min()
        else:
            fromblock = fromblock - 30

    txns_timestamps['timeStamp'] = txns_timestamps['timeStamp'].dt.date

    return txns_timestamps.drop_duplicates()
