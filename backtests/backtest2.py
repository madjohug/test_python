#%%  Imports

import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app
from pandas.core.frame import DataFrame
import ta
import numpy as np
from scipy.stats import linregress
from matplotlib import colors, pyplot, markers

#%%
client = Client()

klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1MINUTE, start_str="14th November 2021")
datas = pd.DataFrame(klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore'])
datas['High'] = pd.to_numeric(datas['High'])
datas['Low'] = pd.to_numeric(datas['Low'])
datas['Close'] = pd.to_numeric(datas['Close'])
datas['Open'] = pd.to_numeric(datas['Open'])

datas = datas.set_index(datas['timestamp'])
datas.index = pd.to_datetime(datas.index, unit="ms")

datas = datas.drop(columns=['QAV', 'NofTrades', 'tbase', 'tquote', 'ignore', 'Closetime'])

#%%
dcp = datas.copy()

#Initialisation des variables de tests
wallet = 100
ema_l = 50
ema_m = 100
ema_h = 150
rsiwindow = 14

# - Calculer moyenne mobile exponentielle(MA)

dcp['EMA_L'] = ta.trend.ema_indicator(dcp['Close'], window=ema_l)
dcp['EMA_M'] = ta.trend.ema_indicator(dcp['Close'], window=ema_m)
dcp['EMA_H'] = ta.trend.ema_indicator(dcp['Close'], window=ema_h)


dcp["RSI"] = ta.momentum.RSIIndicator(dcp['Close'], window=rsiwindow).rsi()

stoch = ta.momentum.StochasticOscillator(dcp['High'], dcp['Low'], dcp['Close'], window=rsiwindow, smooth_window=3)
dcp['STOCH_K'] = stoch.stoch()
dcp['STOCH_D'] = stoch.stoch_signal()

print(dcp)

# %%

for x, row in dcp.iterrows():
  print("stoch", row['STOCH_K'])
# %%
