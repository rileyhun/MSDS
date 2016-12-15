import pandas as pd

data = pd.read_csv("MSDS Numbers.csv", names=['MSDS Number', 'Locations'])

s = data['Locations'].str.split(',').apply(pd.Series, 1).stack()

s.index = s.index.droplevel(-1)
s.name = 'Sites'
data = data.join(s)
del data['Locations']


data = data.groupby(['Sites'])['MSDS Number'].apply(lambda x: x.tolist())
print(data)



