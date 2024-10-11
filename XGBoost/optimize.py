import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error as mse
import optuna

# Data import
df = pd.read_csv("../data/finalData2.csv")
df['time'] = pd.to_datetime(df['time'])
df.drop(["Unnamed: 0",'oerlikon'],axis = 1  ,inplace=True)
stop = df['time'].iloc[-1]
start = stop - pd.Timedelta(weeks=1)
timemask = (df['time'] >= start) & (df['time'] <= stop)
time = df['time']
df.drop('time', axis = 1, inplace = True)
X_train = df[timemask == 0].drop('city', axis = 1)
y_train = df[timemask == 0]['city']
X_test = df[timemask].drop('city', axis = 1)
y_test = df[timemask]['city']




def objective(trial):

    param = {
        "verbosity": 0,
        "objective": "reg:squarederror",
        # use exact for small dataset.
        "tree_method": "exact",
        # defines booster, gblinear for linear functions.
        "booster": trial.suggest_categorical("booster", ["gbtree", "gblinear", "dart"]),
        # L2 regularization weight.
        "lambda": trial.suggest_float("lambda", 1e-8, 1.0, log=True),
        # L1 regularization weight.
        "alpha": trial.suggest_float("alpha", 1e-8, 1.0, log=True),
        # sampling ratio for training data.
        "subsample": trial.suggest_float("subsample", 0.2, 1.0),
        # sampling according to each tree.
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.2, 1.0),
        "n_estimators": trial.suggest_int("n_estimators",5,500),
    }

    if param["booster"] in ["gbtree", "dart"]:
        # maximum depth of the tree, signifies complexity of the tree.
        param["max_depth"] = trial.suggest_int("max_depth", 3, 9, step=2)
        # minimum child weight, larger the term more conservative the tree.
        param["min_child_weight"] = trial.suggest_int("min_child_weight", 2, 10)
        param["eta"] = trial.suggest_float("eta", 1e-8, 1.0, log=True)
        # defines how selective algorithm is.
        param["gamma"] = trial.suggest_float("gamma", 1e-8, 1.0, log=True)
        param["grow_policy"] = trial.suggest_categorical("grow_policy", ["depthwise", "lossguide"])

    if param["booster"] == "dart":
        param["sample_type"] = trial.suggest_categorical("sample_type", ["uniform", "weighted"])
        param["normalize_type"] = trial.suggest_categorical("normalize_type", ["tree", "forest"])
        param["rate_drop"] = trial.suggest_float("rate_drop", 1e-8, 1.0, log=True)
        param["skip_drop"] = trial.suggest_float("skip_drop", 1e-8, 1.0, log=True)

    # bst = xgb.train(param, X_train)
    reg = xgb.XGBRegressor(**param)
    reg.fit(X_train, y_train)
    y_pred =  reg.predict(X_test)
    return mse(y_pred, y_test)



study = optuna.create_study(direction="minimize", storage='sqlite:///optuna.db', study_name='XGB-RUN-2-n_estimators')
study.optimize(objective, n_jobs = -1, timeout= 500)

print("Number of finished trials: ", len(study.trials))
print("Best trial:")
trial = study.best_trial

print("  Value: {}".format(trial.value))
print("  Params: ")
for key, value in trial.params.items():
    print("    {}: {}".format(key, value))