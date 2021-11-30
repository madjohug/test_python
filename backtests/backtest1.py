#%%  Imports

import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app
from pandas.core.frame import DataFrame
import ta
import numpy as np
from scipy.stats import linregress
from matplotlib import colors, pyplot, markers
from utils import getSumOfSquared

#%%
client = Client()

klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, start_str="30th November 2021")
datas = pd.DataFrame(klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore'])
datas['High'] = pd.to_numeric(datas['High'])
datas['Low'] = pd.to_numeric(datas['Low'])
datas['Close'] = pd.to_numeric(datas['Close'])
datas['Open'] = pd.to_numeric(datas['Open'])

datas = datas.set_index(datas['timestamp'])
datas.index = pd.to_datetime(datas.index, unit="ms")

datas = datas.drop(columns=['QAV', 'NofTrades', 'tbase', 'tquote', 'ignore', 'Volume', 'Closetime'])

datas


#%%
dcp = datas.copy()

#Initialisation des variables de tests
wallet = 100
mult=2.0
# source = prix de cloture
source = 20

bblength = 20
bbmult = 2.0

kclength = 20
kcmult = 1.5

usetruerange = True


# - Calculer moyenne mobile (MA)


sma = ta.trend.sma_indicator(dcp['Close'], window=bblength)


# ---------------- Calculer Bandes de Bollinger --------------------

bb = ta.volatility.BollingerBands(close=dcp['Close'], window=bblength, window_dev=bbmult)
dcp['BB_H'] = bb.bollinger_hband()
dcp['BB_L'] = bb.bollinger_lband()

# --------------------------------------------------------------------



# ------------ Calculer le KC ------------------

kc = ta.volatility.KeltnerChannel(high=dcp['High'], low=dcp['Low'], close=dcp['Close'], window=kclength, original_version=usetruerange)
dcp['KC_H'] = kc.keltner_channel_hband()
dcp['KC_L'] = kc.keltner_channel_lband()

# ----------------------------------------------



# ------------ Calculer le SqzOn, SqzOff, et NoSqz ------------------

dcp["SqzOn"] = ((dcp["BB_L"] > dcp["KC_L"]) & (dcp["BB_H"] < dcp["KC_H"]))
dcp["SqzOff"] = ((dcp["BB_L"] < dcp["KC_L"]) & (dcp["BB_H"] > dcp["KC_H"]))
dcp["NoSqz"] = ((dcp["SqzOn"] == False) & (dcp["SqzOff"] == False))

# -------------------------------------------------------------------



# ----------------- On calcule la valeur de l'indicateur squeeze ------------------

# val = linreg(source - avg(avg(highest(high, lengthKC), lowest(low, lengthKC)), sma(close, lengthKC)), lengthKC, 0)

# // Pour chaque ligne : linreg(x, y, z) => intercept(x) + pente(x) * (y - 1 - z)

dcp["highest"] = ta.volatility.donchian_channel_hband(high=dcp['High'], low=dcp['Low'], close=dcp['Close'], window=kclength)
dcp['lowest'] = ta.volatility.donchian_channel_lband(high=dcp['High'], low=dcp['Low'], close=dcp['Close'], window=kclength)
dcp["SMA2"] = ta.trend.sma_indicator(dcp['Close'], window=kclength)

dcp["AVG1"] = (dcp["highest"] + dcp["lowest"]) / 2
dcp["AVG2"] = (dcp["AVG1"] + dcp["SMA2"]) / 2

dcp['X'] = dcp['Close'] - dcp['AVG2']

dcp['SClose'] = dcp['X'] * dcp['X']

dcp["SLOPE"] = ( (kclength * dcp['X'].rolling(kclength).sum() - (dcp['X'].rolling(kclength).sum())) 
               / (kclength * dcp['SClose'].rolling(kclength).sum() - (dcp['X'].rolling(kclength).sum() * dcp['X'].rolling(kclength).sum())))

dcp['INT'] = dcp['X'] - dcp['SLOPE']
# dcp["VAL"] = linregress(pd.DataFrame.to_numpy(dcp["Close"].rolling(window=kclength).), pd.DataFrame.to_numpy(dcp["AVG2"].rolling(window=kclength))).intercept
# ---------------------------------------------------------------------------------

slope, intercept, r, p, se = linregress(list(range(1, 20)), dcp.iloc[len(dcp)-kclength:len(dcp)-1]['Close'])

dcp["SQZ"] = dcp['INT'] + dcp['SLOPE'] * kclength

print("sqz", intercept + slope * (kclength - 1 - 0))
print("slope", slope)
print("intercept", intercept)

dcp

# %%
