import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, roc_curve, auc

#Assign protocol number (for train test split)
global mymap,train_ind
mymap = {'Bitcoin':1, 'Ethereum':2, 'Bitcoin Cash':3, 'EOS':4, 'Filecoin':5, 'Maker':6, 'Monero':7,'Raiblocks':8,'Raiden':9,'Stellar':10,'Tether':11}
train_ind = [1,5,9,4,10,3,6]

def get_change(current, previous):
    if current == previous:
        return 0
    try:
        return ((current - previous)/previous)
    except ZeroDivisionError:
        return 0

#Convert to float
def convert_floats(df):
    for col in df.columns: 
        try:
            df[col] = df[col].astype(float)
        except (ValueError, TypeError):
            print(col + " float conversion failed")
            continue
    return df

#Adding relevant % chg columns and (for binary models) binary variable for outperforming market returns 
def add_shift_metrics(data,model_type,cols):
    tdata = pd.DataFrame([])
    for p in mymap:
        # filter to protocol and index
        data1=data[data.protocol==p].reset_index(drop=True)
        cleandata = data1.set_index('date')
        cleandata = cleandata.sort_index()
        for col in cols:
            cleandata[col + '_chg'] = np.vectorize(get_change)(cleandata[col],cleandata[col].shift(1))

        if model_type=='classification':
            cleandata['alpha_binary'] = np.where(cleandata['price_chg'] > cleandata['index_price_chg'], 1, 0)
            cleandata['alpha_binary_next'] = cleandata['alpha_binary'].shift(-1)
            # cleandata['price_chg_binary'] = np.where(cleandata['price'] > cleandata['price'].shift(1), 1, 0)
            # cleandata['price_chg_binary_next'] = cleandata['price_chg_binary'].shift(-1)
        else:
            cleandata['price_chg_next'] = cleandata['price_chg'].shift(-1)
        cleandata = cleandata.dropna()
        tdata = tdata.append(cleandata)

    tdata = tdata.drop(['protocol','keep','twitter_follower_count','reddit_subscriber_count','price'],axis=1)

    return tdata

#Modeling functions
def build_pipe(model_type,classification_type,**kwargs):
    """* Example for *model_type = 'randomforest'*: ``build_pipe(n_estimators = [50,100,300], class_weight = ['balanced'])``
    """
    if model_type == 'randomforest':
        if classification_type=='classification':
            pipe = Pipeline([("estimator", RandomForestClassifier(random_state=3))])
        else: 
            pipe = Pipeline([("estimator", RandomForestRegressor(random_state=3))])

    if model_type == 'gradientboosting':
        if classification_type=='classification':
            pipe = Pipeline([("estimator", GradientBoostingClassifier(random_state=3))])
        else: 
            pipe = Pipeline([("estimator", GradientBoostingRegressor(random_state=3))])

    params = dict(('estimator__' + name, kwargs[name]) for name in kwargs)

    return pipe, params

def print_score(grid,classification_type,X_train,X_test,y_train,y_test):
    """
    prints accuracy and confusion matrices for a given classification model that indicate performance.
    If regression model, just prints the MSE
    """
    pd.set_option('expand_frame_repr', False)
    for sets in ['train','test']:
        X = eval('X_' + sets)
        y = eval('y_' + sets)
        print "Result for: " + sets
        y_pred = grid.predict(X)

        if classification_type=='classification':
            print accuracy_score(y, y_pred)
            cm = pd.crosstab(y, y_pred, rownames=['True'], colnames=['Predicted'], margins=True)
            print cm
        else:
            print mean_squared_error(y, y_pred)

def print_feature_importances(X_train,grid):
    """
    prints feature importances for a given GridSearchCV model
    """
    tuples = list(zip(X_train.columns, grid.best_estimator_.steps[0][1].feature_importances_))
    feature_importances = pd.DataFrame(tuples, columns=['Feature','Importance'])
    print feature_importances.sort_values('Importance', ascending=False).reset_index(drop=True)

#ROC Curve 
def plot_roc_binary(grid,X_test,y_test):
    y_score = grid.predict(X_test)
    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    fpr, tpr, _ = roc_curve(y_test, y_score)
    roc_auc = auc(fpr, tpr)

    plt.figure()
    lw = 2
    plt.plot(fpr, tpr, color='darkorange',
             lw=lw, label='ROC curve (area = %0.2f)' % roc_auc)
    plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend(loc="lower right")
    plt.show()

#Append predicted variable to test set to analyze (for regression)
def append_y(tdata,X_test,grid):
    X=tdata[~tdata.p_num.isin(train_ind)].reset_index(drop=True)
    X=X[['p_num','alpha_binary_next']].reset_index(drop=True)
    Xr = pd.concat([X_test.reset_index(drop=True),X,pd.Series(grid.predict(X_test)).reset_index(drop=True)],axis=1)
    Xr.columns.values[-1]='y_pred'
    # print np.logical_or(np.logical_and((Xr.y_pred > 0),(Xr.price_chg_next < 0)), 
    #                     np.logical_and((Xr.y_pred < 0),(Xr.price_chg_next > 0))).sum()

    return Xr