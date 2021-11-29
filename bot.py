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
import threading


client = Client()
canBuy = True

def BuyCondition(row, prev):
  if (row['RSI'] < 50 and row['SQZ'] > prev['SQZ'] and row['SQZ'] < 0.0):
    return True
  else:
    return False


def SellCondition(row, prev):
  if (row['RSI'] > 20 and row['SQZ'] < prev['SQZ'] and row['SQZ'] > 0.0):
    return True
  else:
    return False

async def do_something(): 
  wallet = 1000
  coin = 0
  print("APPEL")
  klines = await client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, start_str="29th November 2021")
  datas = pd.DataFrame(klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore'])
  datas = datas.set_index(datas['timestamp'])
  datas.index = pd.to_datetime(datas.index, unit="ms")

  bblength = 20
  bbmult = 2.0

  kclength = 20

  usetruerange = True

  bb = ta.volatility.BollingerBands(close=datas['Close'], window=bblength, window_dev=bbmult)
  datas['BB_H'] = bb.bollinger_hband()
  datas['BB_L'] = bb.bollinger_lband()

  kc = ta.volatility.KeltnerChannel(high=datas['High'], low=datas['Low'], close=datas['Close'], window=kclength, original_version=usetruerange)
  datas['KC_H'] = kc.keltner_channel_hband()
  datas['KC_L'] = kc.keltner_channel_lband()
  print("dpfvn")
  datas['RSI'] = ta.momentum.RSIIndicator(close=datas['Close'], window=14).rsi()
  datas["SqzOn"] = ((datas["BB_L"] > datas["KC_L"]) & (datas["BB_H"] < datas["KC_H"]))
  datas["SqzOff"] = ((datas["BB_L"] < datas["KC_L"]) & (datas["BB_H"] > datas["KC_H"]))
  datas["NoSqz"] = ((datas["SqzOn"] == False) & (datas["SqzOff"] == False))
  datas["highest"] = ta.volatility.donchian_channel_hband(high=datas['High'], low=datas['Low'], close=datas['Close'], window=kclength)
  datas['lowest'] = ta.volatility.donchian_channel_lband(high=datas['High'], low=datas['Low'], close=datas['Close'], window=kclength)
  datas["SMA2"] = ta.trend.sma_indicator(datas['Close'], window=kclength)
  datas["AVG1"] = (datas["highest"].rolling(window=kclength).sum() + datas["lowest"].rolling(window=kclength).sum()) / (2*kclength)
  datas["AVG2"] = (datas["AVG1"].rolling(window=kclength).sum() + datas["SMA2"].rolling(window=kclength).sum()) / (2*kclength)
  datas['X'] = datas['Close'] - datas['AVG2']
  datas['SClose'] = datas['X'] * datas['X']
  datas["SLOPE"] = ( (kclength * datas['X'].rolling(kclength).sum() - (datas['X'].rolling(kclength).sum())) 
                / (kclength * datas['SClose'].rolling(kclength).sum() - (datas['X'].rolling(kclength).sum() * datas['X'].rolling(kclength).sum())))
  datas['INT'] = datas['X'] - datas['SLOPE']
  datas["SQZ"] = datas['INT'] + datas['SLOPE'] * kclength

  if (canBuy == True and wallet > 0 and BuyCondition(datas.iloc[len(datas) - 1], datas.iloc[len(datas) - 2]) == True):
    print("ACHAT AU PRIX DE ", datas.iloc[-1]['Close'], " LE ", datas.iloc[-1]['timestamp'], " D'UN MONTANT DE ", wallet, " USDT")
    coin = float(float(wallet) / float(datas.iloc[-1]['Close']))
    wallet = 0

  elif(canBuy == False and SellCondition(datas.iloc[len(datas) - 1], datas.iloc[len(datas) - 2]) == True):
    print("VENTE AU PRIX DE ", datas.iloc[-1]['Close'], " LE ", datas.iloc[-1]['timestamp'])
    print("NOUVEAU SOLDE : ", (coin * datas.iloc[-1]['Close']))
    coin = 0
    wallet = float(float(coin) * float(datas.iloc[-1]['Close']))

threading.Timer(100, do_something).start()
# %%
