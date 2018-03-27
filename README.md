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
All python scripts to collect the following metrics found in the `get_data/` folder. All data gets populated into PostgreSQL tables (except [coin snapshot data](#cryptocompare)). Except for [GitHub stars](#github), [Marketplace](#marketplace) data and [Ethereum address count](#ethereum-address-count) which are pulled from scratch each time, all other data is appended to the tables as it is collected so that we only pull one day's worth of data. 
### Social
#### Reddit posts and subscribers
* [get_reddit_data.py](https://github.com/sierra073/aspie/blob/master/get_data/get_reddit_data.py):
  * If more than one subreddit is provided for a protocol, all metrics are summed over all subreddits every day
  * Posts are scraped directly from the _new_ posts for every subreddit, and subscribers are pulled using the [Reddit API](https://www.reddit.com/dev/api/#GET_r_{subreddit}_about) 
  * Since the Bitcoin reddit is very active and problematic, we track posts per day from [here](https://www.cryptocompare.com/api/data/socialstats/?id=1182)
  * Tracked starting 2018.
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
* [get_marketcap_history.py](https://github.com/sierra073/aspie/blob/master/get_data/get_marketcap_history.py):
  * Pulls data market capitalization and price data for protocols listed on [CoinMarketCap](https://coinmarketcap.com/), leveraging [this script](https://github.com/jhogan4288/coinmarketcap-history/blob/master/coinmarketcap_usd_history.py). Tracked since January 2017.
#### Coinbase Index Fund
* [get_cbi_data.py](https://github.com/sierra073/aspie/blob/master/get_data/get_cbi_data.py):
  * Scrapes directly from [here](https://am.coinbase.com/index) every day. Tracked since January 2015.
### Aggregated and Other Metrics
#### Activity Score
* [kpi.py](https://github.com/sierra073/aspie/blob/master/get_data/kpi.py) and [kpi.sql](https://github.com/sierra073/aspie/blob/master/get_data/kpi.sql):
  * Aggregates all Social and Development data into a single score between 0 and 100 - computed daily since 2/12/18 when all data was avaiable. **Very much a heuristic.**
    * Overall explanation: 
      * Each metric is transformed into a *percentile rank* (among all protocols) for that day. Reddit and twitter followers are represented as the *change in followers from the previous day*.
      * The score is an average of 3 components which are themselves averages (and multiplied by 100): (1) Social Score, an average of the reddit post rank, reddit subscriber rank, twitter follower rank and Hacker News rank; (2) Developer Score, an average of the GitHub commit count rank, GitHub star count rank and StackOverflow question count rank; (3) Search Score which is just the [Google Trends search interest metric](#google-search-interest) for the day.
    * Patching and exceptions: 
      * Since GitHub commits are only available weekly, we compute the daily value as the average of the weekly value for the week the day falls into.
      * There were problems collecting Bitcoin reddit post counts before 3/1/18, so we patch the reddit post count prior to 3/1/18 as the *average reddit posts per day since 3/1/18*. Definitely not ideal.
#### CryptoCompare
* [coinsnapshot.py](https://github.com/sierra073/aspie/blob/master/get_data/coinsnapshot.py)
  * Leverages the CryptoCompare API "[coin snapshot](https://www.cryptocompare.com/api/#-api-data-coinsnapshot-)". Runs live from the **individual** dashboard tab.
#### Ethereum address count
* [eth_address_count.py](https://github.com/sierra073/aspie/blob/master/get_data/eth_address_count.py):
  * CSV pulled directly from [here](https://etherscan.io/chart/address?output=csv') and loaded into Postgres every day.
### Sentiment Analysis
* [get_sentiments.py](https://github.com/sierra073/aspie/blob/master/get_data/get_sentiments.py):
  * Computes a sentiment score between -1 and 1 (1 being the most positive) leveraging [Haven OnDemand](https://dev.havenondemand.com/apis/analyzesentiment#overview) for (1) and [TextBlob](http://textblob.readthedocs.io/en/dev/index.html) for (2) and (3):
    * (1) Using the first page of the protocol's subreddit(s), computes the average sentiment score
    * (2) If any of the keywords provided for the protocol in the input data are found in the top 200 *hot* posts of [r/CryptoCurrency](https://www.reddit.com/r/CryptoCurrency/), returns the average sentiment score
    * (3) Searches twitter for the top 100 results (statuses containing each keyword for each protocol) and returns the average sentiment score
    * The final sentiment score is highly weighted towards the twitter score `85%(90% in case (2) is not found)*(3), + 10%*(1) + 5%*(2)`

## Predictive Model--under development

## Usage

* To add a new protocol to track in the dashboard, please fill out [protocols.csv](https://github.com/sierra073/aspie/blob/master/data/input/protocols.csv) under `data/input/protocols.csv`
  * To get the cryptocompare id (`id_cc`) for a protocol, please do a ctrl-f on this page for its ticker symbol and retrieve the "Id":
https://min-api.cryptocompare.com/data/all/coinlist 

## To-do
- Streamline the process for adding new protocols
- Build navigable website utilizing `flask` instead of just `bokeh`  
- Continued improvement of visuals, interactivity and layout
- Finish developing an LTSM (Deep Learning) model to predict daily price appreciation leveraging all of the metrics tracked, and deploy on the website


