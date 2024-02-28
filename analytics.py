from sklearn.manifold import TSNE 
from sklearn.decomposition import PCA 
import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt

# VERY IMPORTANT: DO NOT USE PCA ON CATEGORICAL DATA!!!!!!!!!
def fitplot_PCA(df):
    pca = PCA(n_components=2)
    features = [col for col in df.columns if col != 'outcome']
    X = pca.fit_transform(df[features])
    plotdata = pd.DataFrame({"X_0": X[:,0], "X_1": X[:,1], 'label': df['outcome']})
    fig = sns.scatterplot(x="X_0", y="X_1", hue='label', data=plotdata)
    fig.set_yticks(range(int(X[:,1].max()) + 1))

    print(plotdata['X_1'].max())
    
    fig.get_figure().savefig('PCA.png')
    plt.show()

def fitplot_TSNE(df):
    tsne = TSNE(2, random_state=1)
    features = [col for col in df.columns if col != 'outcome']
    tsne_res = tsne.fit_transform(df[features])
    tsne_df = pd.DataFrame({'ax1': tsne_res[:,0], 'ax2': tsne_res[:, 1], 'outcome': df['outcome']})
    fig = sns.scatterplot(x='ax1', y='ax2', hue='outcome', data=tsne_df)
    fig.get_figure().savefig('TSNE.png')

if __name__ == '__main__':
    fname="./data/PLATINUM-II_27-02-2024_z.csv"
    df = pd.read_csv(fname)
    df = df[['hot_streak','wr','rank','outcome']]
    df = df.dropna()

    #fitplot_TSNE(df)
    fitplot_TSNE(df.loc[[i for i in range(100)], ['wr', 'rank', 'outcome']]) #excluded hot_streak since it's categorical


