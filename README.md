# Crypto Dashboard
<table>
<tr>
<td>
  A webapp to track and visualize trends in social, development and marketplace activity for a set of crypto protocols. It helps in judging and predicting a protocol's growth and price appreciation.
  The <b>individual</b> tab helps zone in on protocols one at a time, and the <b>compare</b> tab helps compare protocols simultaneously.
</td>
</tr>
</table>

## Working Live Demos 
* http://dash.ethsimple.com/
* http://dashboard.soulelabs.com/ 
* http://parachain.capital/
* http://recursion.capital/ 

## Contents
- [Built With](#built-with)
- [Installation](#installation)
  * [Requirements](#requirements)
  * [Live data collection](#live-data-collection)
  * [Serving the dashboard](#serving-the-dashboard)
- [Data Collection](#data-collection)
  * [Social](#social)
  * [Development](#development)
  * [Marketplace](#marketplace)
  * [Aggregated and Other Metrics](#aggregated-and-other-metrics)
  * [Sentiment Analysis](#sentiment-analysis)
- [Predictive Model--under development](#predictive-model--under-development)
- [Usage](#usage)
- [To-do](#to-do)

## Built With 

- Python + [Bokeh](https://bokeh.pydata.org/en/latest/) - a Python interactive visualization library 
- Machine Learning: [scikit-learn](http://scikit-learn.org/stable/), [Keras](https://keras.io/), [Tensorflow](https://www.tensorflow.org/)
- More

## Installation

### Requirements
* Unix-based system
* Python 2.7 and up
* [PostgreSQL](https://www.postgresql.org/download/)

`$ pip install -r requirements.txt`

### Live data collection
A [cronjob](https://help.ubuntu.com/community/CronHowto) runs [getdata.sh](https://github.com/sierra073/aspie/blob/master/get_data/get_data.sh) every 4 hours. Edit the path to the `aspie` directory on line 4 if needed.

### Serving the dashboard
1. Reverse Proxy setup: utilizes [Nginx](https://bokeh.pydata.org/en/latest/docs/user_guide/server.html#nginx)
2. Run the following command from the `aspie` directory, replacing the host(s) in `--allow-websocket-origin=`: 
```bash
bokeh serve individual.py compare.py --port 5100 --num-procs 0 --allow-websocket-origin=159.89.155.200 --allow-websocket-origin=dash.ethsimple.com --allow-websocket-origin=dashboard.soulelabs.com --allow-websocket-origin=parachain.capital --allow-websocket-origin=recursion.capital
```

## Data Collection
All python scripts to collect the following metrics found in the `get_data/` folder. All data gets populated into PostgreSQL tables.
### Social
#### Reddit posts and subscribers
* [get_reddit_data.py](https://github.com/sierra073/aspie/blob/master/get_data/get_reddit_data.py):
  * If more than one subreddit is provided for a protocol, all metrics are summed over all subreddits every day
  * Posts are scraped directly from the _new_ posts for every subreddit, and subscribers are pulled using the [Reddit API](https://www.reddit.com/dev/api/#GET_r_{subreddit}_about) 
  * Since the Bitcoin reddit is very active and problematic, we track posts per day from [here](https://www.cryptocompare.com/api/data/socialstats/?id=1182)
#### Twitter followers
* [get_twitter_data.py](https://github.com/sierra073/aspie/blob/master/get_data/get_twitter_data.py):
  * Number of followers scraped directly from each protocol's twitter page every day. Tracked starting 2018.
#### Google search interest
* [get_searchinterest_data.py](https://github.com/sierra073/aspie/blob/master/get_data/get_searchinterest_data.py):
  * Utilizes [pytrends](https://github.com/GeneralMills/pytrends) to get the Google Trends _search interest_ metric (number out of 100) for each search term provided in the input data and averages them for each protocol. Tracked starting 2018.
#### Hacker News stories
* [get_hackernews_data.py](https://github.com/sierra073/aspie/blob/master/get_data/get_hackernews_data.py):
  * Utilizes the [haxor](https://github.com/avinassh/haxor) package to pull the top 200 Hacker News stories and count the number of times each protocol name is mentioned in a story title. Tracked starting 2018.
### Development
#### GitHub
* Utilizes the [GitHub API](https://developer.github.com/v3/) directly
* If more than one repo is provided for a protocol, all metrics are summed over all repos
* Stars ([get_github_stars.py](https://github.com/sierra073/aspie/blob/master/get_data/get_github_stars.py)) are tracked on a daily basis since the repo(s)'s earliest creation date
* Commits ([get_github_data.py](https://github.com/sierra073/aspie/blob/master/get_data/get_github_data.py)) are only available at a _weekly basis_ for the last 12 months, hence why the data starts end of January 2017
  * _"Total commits"_ thus truly means all commits since January 2017 or since the first repo was created if after January 2017 (except for some protocols tracked after January 2018)
#### StackOverflow
* [get_stackoverflow_data.py](https://github.com/sierra073/aspie/blob/master/get_data/get_stackoverflow_data.py):
  * Utilizes [StackAPI](http://stackapi.readthedocs.io/en/latest/)
  * Questions are counted since January 2017. Questions are aggregated by protocol by searching for those that contain the term(s) specified in our input data in their title OR for those tagged as the term(s). Thus, it's possible for questions to be double counted if the term is contained in the question title AND question tag, but highly unlikely based on the data observed.
### Marketplace
#### CoinMarketCap
* Tracked since January 2017.
#### Coinbase Index Fund
* Tracked since January 2015.
### Aggregated and Other Metrics
#### Activity Score
#### CryptoCompare
#### Ethereum address count
* CSV pulled directly from [here](https://etherscan.io/chart/address?output=csv') and loaded into Postgres every day.
### Sentiment Analysis

## Predictive Model--under development

## Usage

* To add a new protocol to track in the dashboard, please fill out [protocols.csv](https://github.com/sierra073/aspie/blob/master/data/input/protocols.csv) under `data/input/protocols.csv`
  * To get the cryptocompare id (`id_cc`) for a protocol, please do a ctrl-f on this page for its ticker symbol and retrieve the "Id":
https://min-api.cryptocompare.com/data/all/coinlist 

## To-do
- Streamline the process for adding new protocols
- Build navigable website utilizing `flask` instead of just `bokeh`  
- Continued improvement of visuals, interactivity and layout
- Finish developing an LTSM (Deep Learning) model to predict daily price appreciation leveraging all of the metrics tracked


