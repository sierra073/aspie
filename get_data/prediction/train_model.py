from initialize_data import * 
from modeling_helpers import *
import seaborn as sns
from sklearn.grid_search import GridSearchCV
#%matplotlib inline

queryfile=open('get_daily_features.sql', 'r')
query = queryfile.read()
queryfile.close()

data = get_table_from_db(query)

#Ethereum patching
eth_sub = data[data.protocol=='Ethereum'].reset_index(drop=True)

j=0
for i in range(29,38):
    j+=1
    eth_sub.iloc[i,7] = 374869 + (404.33*j)

data.ix[data.protocol=='Ethereum', 'twitter_follower_count'] = eth_sub['twitter_follower_count'].values

#Convert date to datetime
data['date'] = pd.to_datetime(data['date'])

#Filter out EOS before social data tracked
data['keep'] = np.where(np.logical_or((data.protocol != 'EOS'),np.logical_and(data.protocol == 'EOS', data.date > pd.to_datetime('2018-02-26'))),1,0)
data = data[data.keep==1]

#Convert search count and activity score to %
data['search_count'] = data['search_count']/100
data['activity_score'] = data['activity_score']/100

#Protocol number
data['p_num'] = data['protocol'].map(lambda s: mymap.get(s) if s in mymap else s)

#Columns to add % change to
cols = ['star_count','reddit_post_count',
       'reddit_subscriber_count', 'twitter_follower_count','search_count', 'price', 'index_price','activity_score']
data[cols] = data[cols].astype('float')

tdata = add_shift_metrics(data,'classification',cols)
tdata = convert_floats(tdata)

#train test split -- make it depend on option arg for 'regression' (add if else to lines 76,77,80,81)
X_train = tdata[tdata.p_num.isin(train_ind)].reset_index(drop=True)
y_train = X_train['alpha_binary_next'].values
X_train = X_train.drop(['p_num','alpha_binary_next'],axis = 1)

X_test = tdata[~tdata.p_num.isin(train_ind)].reset_index(drop=True)
y_test = X_test['alpha_binary_next'].values
X_test = X_test.drop(['p_num','alpha_binary_next'],axis = 1)

print X_train.shape
print X_test.shape
print tdata.shape
print X_train.columns

# corr = tdata.corr()
# sns.heatmap(corr)

pipe, params = build_pipe('gradientboosting','classification',n_estimators = [60,80,100], learning_rate = [0.05], max_depth = [3,7,15], max_features = ["sqrt","log2"], warm_start=[True,False])
grid_gb = GridSearchCV(pipe, params, cv=2, verbose=1,n_jobs=-1)

grid_gb.fit(X_train,y_train)
print_score(grid_gb,'classification',X_train,X_test,y_train,y_test)
print_feature_importances(X_train,grid_gb)

print grid_gb.best_estimator_

Xr = append_y(tdata,X_test,grid_gb)

plot_roc_binary(grid_gb,X_test,y_test)