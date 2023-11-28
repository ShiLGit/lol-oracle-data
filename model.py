from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np
import random
import sys
import pprint

pp = pprint.PrettyPrinter(indent=4)

fname = 'data.csv'
if len(sys.argv) == 2:
    fname = sys.argv[1]

# partition into 7:3 training-testing sets
df = pd.read_csv(fname)
print(f"TRAINING ON DATASET {fname}")
train_bound = int(df.shape[0]*0.7)

features = [x for x in df.columns if x != 'outcome']
xtrain = df.loc[:train_bound, df.columns != 'outcome']
ytrain = np.array(df.loc[:train_bound, df.columns ==
                  'outcome']).reshape(xtrain.shape[0])
xtest = df.loc[train_bound + 1:, df.columns != 'outcome']
ytest = np.array(df.loc[train_bound + 1:, df.columns ==
                 'outcome']).reshape(xtest.shape[0])


logreg = LogisticRegression()
rf = RandomForestClassifier(n_estimators=1000)


def traintest(xtrain, xtest, model):
    model.fit(xtrain, ytrain)
    pred_y = model.predict(xtest)
    return accuracy_score(pred_y, ytest)


def delete_poor_features(feature_accuracies):
    models = ['LOGREG', 'RANDFOR']
    for m in models:
        keys = list(feature_accuracies[m].keys())

        for k in keys:
            if feature_accuracies[m][k] < 0.50:
                del feature_accuracies[m][k]


def random_subset(feature_names, size):

    indices = random.sample(range(0, len(feature_names)),
                            min(size, len(feature_names)))
    if len(indices) == 0:
        print(f"Valid features is empty! {feature_names}")
        return []

    subset = [feature_names[i] for i in indices]
    return subset


def main():
    feature_accuracies = {  # keep dict of accuracies per feature to use in feature selection
        'LOGREG': dict(),
        'RANDFOR': dict()
    }
    print("INDIVIDUAL TRAINING: ")
    for x in features:
        feature_accuracies['RANDFOR'][x] = traintest(
            xtrain[[x]], xtest[[x]], rf)
        feature_accuracies['LOGREG'][x] = traintest(
            xtrain[[x]], xtest[[x]], rf)

    pp.pprint(feature_accuracies)
    print("FEATURE PICKING")
    delete_poor_features(feature_accuracies)
    pp.pprint(feature_accuracies)
    for i in range(1, 5):
        subset = random_subset(list(feature_accuracies['RANDFOR'].keys()), i)
        #subset = ['hot_streak', 'rank']
        if len(subset) > 0:
            print(
                f"TRAINING RF ON FEATURES {subset}: {traintest(xtrain[subset], xtest[subset], rf)}")

        subset = random_subset(list(feature_accuracies['LOGREG'].keys()), i)
        if len(subset) > 0:
            print(
                f"TRAINING LOGREG ON FEATURES {subset}: {traintest(xtrain[subset], xtest[subset], logreg)}")


if __name__ == '__main__':
    main()
