from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pandas as pd
import numpy as np

# partition into 7:3 training-testing sets
df = pd.read_csv('GOLD_II.csv')
train_bound = int(df.shape[0]*0.7)
xtrain = df.loc[:train_bound, df.columns != 'outcome']
ytrain = np.array(df.loc[:train_bound, df.columns ==
                  'outcome']).reshape(xtrain.shape[0])

xtest = df.loc[train_bound + 1:, df.columns != 'outcome']
ytest = np.array(df.loc[train_bound + 1:, df.columns ==
                 'outcome']).reshape(xtest.shape[0])


logreg = LogisticRegression()


def traintest(xtrain, xtest):
    logreg.fit(xtrain, ytrain)
    pred_y = logreg.predict(xtest)
    return accuracy_score(pred_y, ytest)


def main():
    for x in df.columns:
        if x == 'outcome':
            continue

        print(f"{x}: {traintest(xtrain[[x]], xtest[[x]])}")


if __name__ == '__main__':
    main()
