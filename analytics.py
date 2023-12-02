from sklearn.manifold import TSNE 
import pandas as pd 
import seaborn as sns 
fname="GOLD_I.csv"
df = pd.read_csv(fname)
df = df.loc[:, ['hot_streak','wr','rank','outcome']]
df = df.dropna()

tsne = TSNE(2)
tsne_res = tsne.fit_transform(df)
tsne_df = pd.DataFrame({'ax1': tsne_res[:,0], 'ax2': tsne_res[:, 1], 'outcome': df['outcome']})
scplot=sns.scatterplot(x='ax1', y='ax2', hue='outcome', data=tsne_df)

scplot.get_figure().savefig('TSNE.png')