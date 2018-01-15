import requests
import json
import pandas as pd
import requests
from urlparse2 import urlparse
import time
import re
REQUEST_HEADERS =  {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

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

#### Import input data with Protocols info 
protocols = pd.read_csv("https://raw.githubusercontent.com/sierra073/aspie/master/data/input/protocols.csv")

protocols['github_repos'] = protocols['github_repos'].apply(lambda x: stringToList(x))
protocols['subreddits'] = protocols['subreddits'].apply(lambda x: stringToList(x))
protocols['stackoverflow'] = protocols['stackoverflow'].apply(lambda x: stringToList(x))
protocols['search'] = protocols['search'].apply(lambda x: stringToList(x))

### wrapper function around whatever API calls are used to get a certain metric if we are appending it to current data
def api_wrapper_append(csv_data,api_func,site,u_srt,u_end,date_col,count_col,sum,allow_multiple_days,csv_output_name):
    counts_by_day = pd.DataFrame([])

    for index, row in protocols.iterrows():
        data_sub = csv_data[csv_data.protocol==row['protocol']]

        if site=='GitHub':
            items = row['github_repos']
        elif site=='Reddit':
            items = row['subreddits']
        elif site=='StackOverflow':
            items = row['stackoverflow']

        for item in items:
            if item != 'None':
                max_dt = pd.to_datetime(data_sub[date_col]).max()
                count_by_day = api_func(u_srt + item + u_end,max_dt)
                count_by_day['protocol'] = row['protocol']
                counts_by_day = counts_by_day.append(count_by_day)

    if not counts_by_day.empty:
        counts_by_day[date_col] = pd.to_datetime(counts_by_day[date_col],infer_datetime_format=True).dt.date
        if sum==True:
            counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol',date_col]).sum()).reset_index()
        else:
            counts_by_day = pd.DataFrame(counts_by_day.groupby(['protocol',date_col]).size()).reset_index()

        if len(count_col) > 1:
            li = [['protocol'], [date_col], count_col]
            chained = []
            while li:
                chained.extend(li.pop(0))
            counts_by_day.columns = chained
        else:
            counts_by_day.columns = ['protocol', date_col, count_col]

        # sort current data and remove latest date
        if allow_multiple_days==True:
            csv_data['date_rank'] = csv_data.sort_values(['protocol',date_col],ascending=False).groupby(['protocol']).cumcount() + 1
            csv_data = csv_data[csv_data.date_rank > 1]
            csv_data = csv_data.drop(['date_rank'],axis=1)
            csv_data = csv_data.reset_index(drop=True)
        else:
            if csv_data[date_col].max() == counts_by_day[date_col].max():
                csv_data['date_rank'] = csv_data.sort_values(['protocol',date_col],ascending=False).groupby(['protocol']).cumcount() + 1
                csv_data = csv_data[csv_data.date_rank > 1]
                csv_data = csv_data.drop(['date_rank'],axis=1)
                csv_data = csv_data.reset_index(drop=True)
        # append new data and reformat. be overly certain to remove index column
        counts_by_day = csv_data.append(counts_by_day,ignore_index=True)
        counts_by_day[date_col] = pd.to_datetime(counts_by_day[date_col])
        counts_by_day = counts_by_day.reset_index()
        counts_by_day = counts_by_day.dropna()
        counts_by_day = counts_by_day.reset_index(drop=True)
        if site=='StackOverflow':
            counts_by_day = counts_by_day.drop(['index'],axis=1)

        result_protocols = pd.DataFrame(counts_by_day.groupby('protocol').size()).reset_index()
        # ensure each protocol is listed
        counts_by_day2=counts_by_day
        print(result_protocols['protocol'])
        for index, row in protocols.iterrows():
            if row['protocol'] not in result_protocols['protocol']:
                print(row['protocol'])
        #counts_by_day.to_csv("data/output/" + csv_output_name + ".csv",index=False)