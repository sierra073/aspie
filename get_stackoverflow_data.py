from initialize_data import *
from access_tokens import *
import pandas as pd

from stackapi import StackAPI
from datetime import datetime

def get_stackoverflow_questions(search_title,max_dt):
	SITE = StackAPI('stackoverflow',key=stackoverflow_key)
	questions = pd.DataFrame([])
	print(search_title)
	# title search
	results_title = SITE.fetch('search', fromdate=datetime.strptime(str(max_dt), '%Y-%m-%d %H:%M:%S'), todate=datetime.now(), sort='creation', intitle=search_title)
	results_title = pd.DataFrame(results_title['items'])
	if not results_title.empty:
		questions['date'] = pd.to_datetime(results_title['creation_date'],unit='s').dt.date
		questions['question_id'] = results_title['question_id']
		questions['view_count'] = results_title['view_count']
	# tag search
	results_tag = SITE.fetch('questions', fromdate=datetime.strptime(str(max_dt), '%Y-%m-%d %H:%M:%S'), todate=datetime.now(), sort='creation', tagged=search_title)
	results_tag = pd.DataFrame(results_tag['items'])
	if not results_tag.empty:
		tagged = pd.DataFrame([])
		tagged['date'] = pd.to_datetime(results_tag['creation_date'],unit='s').dt.date
		tagged['question_id'] = results_tag['question_id']
		tagged['view_count'] = results_tag['view_count']
		questions = questions.append(tagged)
		questions = questions.reset_index()

	# format and group
	if not questions.empty:
		questions_final = questions.groupby('date').question_id.nunique().reset_index()
		questions_final['views'] = questions.groupby(['date','question_id']).sum().reset_index()['view_count']
	else:
		questions['date'] = max_dt
		questions['question_id'] = 0
		questions['views'] = 0
		questions_final = questions

	return(questions_final)

# questions by day for each search term (as tag and title), since Jan 2017
stackoverflow_questions = pd.read_csv("data/output/stackoverflow_questions.csv")
api_wrapper_append(stackoverflow_questions,get_stackoverflow_questions,'StackOverflow',"","",'date',['question_id','views'],True,True,'stackoverflow_questions')
