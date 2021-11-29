#%%

import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app
from pandas.core.frame import DataFrame
import ta
import numpy as np
from scipy.stats import linregress
from matplotlib import colors, pyplot, markers
import sched, time

df = pd.DataFrame(columns=["Numero", "Adresse", "Nom", "Prenom"])

row = { "Numero": 1, "Adresse": "Nique", "Nom": "tezzac", "Prenom": "Hugo" }
df = df.append(row, ignore_index=True)

row = { "Numero": 2, "Adresse": "Nique", "Nom": "tyyh", "Prenom": "Hugo" }
df = df.append(row, ignore_index=True)

row = { "Numero": 3, "Adresse": "Nique", "Nom": "erfef", "Prenom": "Hugo" }
df = df.append(row, ignore_index=True)

row = { "Numero": 4, "Adresse": "Nique", "Nom": "Madjour", "Prenom": "Hugo" }
df = df.append(row, ignore_index=True)

df

print(df.iloc[-1]['Nom'])
# %%
