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

klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, start_str="15th September 2021")
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

ema_l = 50
ema_m = 100
ema_h = 150

dcwindow = 20
rsiwindow = 14
# - Calculer moyenne mobile exponentielle(MA)

# dcp['EMA_L'] = ta.trend.ema_indicator(dcp['Close'], window=ema_l)
# dcp['EMA_M'] = ta.trend.ema_indicator(dcp['Close'], window=ema_m)
# dcp['EMA_H'] = ta.trend.ema_indicator(dcp['Close'], window=ema_h)


dcp["RSI"] = ta.momentum.RSIIndicator(dcp['Close'], window=rsiwindow).rsi()

stoch = ta.momentum.StochasticOscillator(dcp['High'], dcp['Low'], dcp['Close'], window=rsiwindow, smooth_window=3)
dcp['STOCH_K'] = stoch.stoch()
dcp['STOCH_D'] = stoch.stoch_signal()

donch = ta.volatility.DonchianChannel(dcp['High'], dcp['Low'], dcp['Close'], window=dcwindow)
dcp['DONCH_L'] = donch.donchian_channel_lband()
dcp['DONCH_H'] = donch.donchian_channel_hband()

ulcer = ta.volatility.UlcerIndex(dcp['Close'], 14)
dcp['ULC'] = ulcer.ulcer_index()

sma = ta.trend.SMAIndicator(dcp['ULC'], window=52)
dcp['SMA'] = sma.sma_indicator()

dcp

# %%

#BOUCLE
wallet = 1000
usdt = 10000
startusdt = usdt

taxe = 0.0007

startcoin = ((usdt * taxe) / dcp.iloc[0]['Close'])
coin = 0

lowerOS = 20
upperOS = 80

maker = 0.0005
sltaux = 0.02
tptaux = 0.1

stoploss = 0
# takeprofit = 500000

canbuy = True

result = None
result = pd.DataFrame(columns=['date', 'type', 'price', 'amount', 'sans_frais', 'coins', 'frais', 'usdt'])

previousrow = dcp.iloc[0]
def buyCondition(row, prev):
  # if (row['STOCH_K'] > row['STOCH_D'] and prev['STOCH_K'] < prev['STOCH_D'] and row['STOCH_K'] < upperOS
  #   and row['EMA_L'] > row['EMA_M'] and row['EMA_M'] > row['EMA_H']
  #   and row['Close'] > prev['DONCH_H']
  #   and row['ULC'] < prev['ULC'] and row['ULC'] > 0.5) :
  if (row['ULC'] < prev['ULC'] and row['ULC'] > row['SMA'] and prev['ULC'] > prev['SMA']) :
    return True
  else:
    return False

def sellCondition(row, prev):
  # if (row['STOCH_K'] < row['STOCH_D'] and prev['STOCH_K'] > prev['STOCH_D'] and row['STOCH_K'] > lowerOS
  #   and row['ULC'] > prev['ULC'] and row['ULC'] < 0.5) :
  if (row['ULC'] > prev['ULC'] and row['ULC'] < row['SMA'] and prev['ULC'] < prev['SMA'] and prev['ULC'] < 0.1) :
    return True
  else:
    return False

for x, row in dcp.iterrows():
  #Buy
  if (buyCondition(row, previousrow) == True and canbuy == True and usdt > 0):
    buyprice = row['Close']

    frais = float(usdt * taxe)
    coin = float(usdt / buyprice)
    prevusdt = usdt
    usdt = 0

    stoploss = buyprice - sltaux * buyprice
    takeprofit = buyprice + tptaux * buyprice

    canbuy = False

    myrow = {'date': x, 'type': "BUY", 'price': buyprice, 'amount': prevusdt, 'sans_frais': usdt, 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  #StopLoss
  elif (coin > 0 and stoploss > row['Low']):
    sellprice = stoploss

    frais = float(coin * taxe)
    usdt = coin * sellprice
    coin = 0

    canbuy = True

    myrow = {'date': x, 'type': "STOPLOSS", 'price': sellprice, 'amount': "", 'sans_frais': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  # #TakeProfit
  # elif (coin > 0 and takeprofit < row['High']):
  #   sellprice = takeprofit

  #   frais = float(coin * taxe)
  #   usdt = coin * sellprice
  #   coin = 0

  #   canbuy = True

  #   myrow = {'date': x, 'type': "TAKEPROFIT", 'price': sellprice, 'amount': "", 'sans_frais': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
  #   result = result.append(myrow, ignore_index=True)

  #Vente classique
  elif (canbuy == False and coin > 0 and sellCondition(row, previousrow) == True):
    sellprice = row['Close']

    frais = float(coin * taxe)
    sansfrais = coin * sellprice

    coin = coin - frais
    usdt = coin * sellprice
    coin = 0

    canbuy = True

    myrow = {'date': x, 'type': "SELL", 'price': sellprice, 'amount': "", 'sans_frais': sansfrais, 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  previousrow = row


print("USDT AU DEBUT : ", startusdt)
print("USDT A LA FIN : ", usdt)

print("EN HOLD : ", float("{:.3f}".format(startcoin * dcp.iloc[dcp.shape[0] - 1]['Close'])))
print(result['type'].value_counts())

result
# %%
