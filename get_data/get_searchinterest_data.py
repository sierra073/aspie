from initialize_data import *
from access_tokens import *
import pandas as pd
import time
from pytrends.request import TrendReq

pytrends = TrendReq(hl='en-US', tz=360)

def get_searchinterest_data(x,max_dt):
    time.sleep(1)
    pytrends.build_payload([x], cat=0, timeframe='now 1-d', geo='', gprop='')
    data = pytrends.interest_over_time()
    data = data.reset_index()
    data = data.drop(['isPartial'],axis=1)
    data.columns = ['date','search_interest']
    return(data)

searchinterest = get_table_from_db('select * from search_interest;')
api_wrapper_append(searchinterest,get_searchinterest_data,'Search',"","",'date',['search_interest'],None,None,'search_interest')
print("done")


        