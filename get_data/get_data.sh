#!/bin/bash

echo "$(date)"
cd "/root/aspie/get_data/"
python get_github_data.py &
python get_github_stars.py &
python get_reddit_data.py &
python get_stackoverflow_data.py &
python get_twitter_data.py &
python get_searchinterest_data.py &
python get_marketcap_history.py &
python eth_address_count.py &
python get_hackernews_data.py &
python get_sentiments.py &
wait
python kpi.py &&
python get_token_txn_hist.py &&
echo "Done!"
