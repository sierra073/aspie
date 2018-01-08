import requests
import json
import pandas as pd

##### Helper functions

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

# return the result of an http request in json format
def get_json(url):
	r = requests.get(url)
	return json.loads(r.text or r.content)

######################## Import input data with Protocols info ########################
protocols = pd.read_csv("data/input/protocols.csv")

protocols['github_repos'] = protocols['github_repos'].apply(lambda x: stringToList(x))
protocols['subreddits'] = protocols['subreddits'].apply(lambda x: stringToList(x))