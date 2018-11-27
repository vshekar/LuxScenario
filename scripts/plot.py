import json
import matplotlib.pyplot as plt
import pandas as pd

with open('../output/net_dump/lmbd8/traveltime_55_1_28800_57600_8_False.json') as f:
    high_vul_tt = json.load(f)

with open('../output/net_dump/lmbd100/traveltime_1_1_0_0_100_True.json') as f:
    nom_tt = json.load(f)

df1 = pd.DataFrame.from_dict(data=nom_tt, orient="index")
df2 = pd.DataFrame.from_dict(data=high_vul_tt, orient="index")
result = pd.concat([df1, df2], axis=1, join='inner')

plt.hist(result['nom'], bins=10000)
plt.show()