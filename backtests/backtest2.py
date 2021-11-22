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

klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1MINUTE, start_str="1st December 2017")
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
usdt = 100
coin = 0

ema_l = 50
ema_m = 100
ema_h = 150
rsiwindow = 14

lowerOS = 20
upperOS = 80

taxe = 0.1
sltaux = 0.02
tptaux = 0.1

stoploss = 0
takeprofit = 500000

ratiobuy = 0.1
canbuy = True

result = None
result = pd.DataFrame(columns=['date', 'type', 'price', 'amount', 'coins', 'frais', 'newwallet'])

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

previousrow = dcp.iloc[0]

def buyCondition(row, prev):
  if (row['STOCH_K'] > row['STOCH_D'] and prev['STOCH_K'] < prev['STOCH_D'] and prev['STOCH_K'] > lowerOS) :
    return True
  else:
    return False

def sellCondition(row, prev):
  if (row['STOCH_K'] < row['STOCH_D'] and prev['STOCH_K'] > prev['STOCH_D'] and prev['STOCH_K'] < upperOS) :
    return True
  else:
    return False

for x, row in dcp.iterrows():
  #Buy
  if (buyCondition(row, previousrow) == True and canbuy == True and usdt > 0):
    buyprice = row['Close']

    usdtchanged = usdt - usdt * ratiobuy
    usdt = usdt * ratiobuy

    stoploss = buyprice - sltaux * buyprice
    takeprofit = buyprice + tptaux * buyprice

    canbuy = False

    coin = usdtchanged / buyprice - (usdtchanged * buyprice * taxe)
    wallet = usdt

    myrow = {'date': x, 'type': "BUY", 'price': buyprice, 'amount': usdtchanged, 'coins': coin, 'frais': usdtchanged * buyprice * taxe, 'newwallet': wallet}
    result.append(myrow, ignore_index=True)

  #StopLoss
  elif (canbuy == False and coin > 0 and stoploss > row['Low']):
    sellprice = stoploss

    usdt = usdt + (coin * sellprice) - (coin * sellprice * taxe)   

    lastcoinamount = coin
    coin = 0

    canbuy = True
    wallet = usdt

    myrow = {'date': x, 'type': "STOPLOSS", 'price': sellprice, 'amount': lastcoinamount, 'coins': coin, 'frais': lastcoinamount * sellprice * taxe, 'newwallet': wallet}
    result.append(myrow, ignore_index=True)

  #TakeProfit
  elif (canbuy == False and coin > 0 and takeprofit < row['High']):
    sellprice = takeprofit

    usdt = usdt + (coin * sellprice) - (coin * sellprice * taxe)   

    lastcoinamount = coin
    coin = 0

    canbuy = True
    wallet = usdt

    myrow = {'date': x, 'type': "TAKEPROFIT", 'price': sellprice, 'amount': lastcoinamount, 'coins': coin, 'frais': lastcoinamount * sellprice * taxe, 'newwallet': wallet}
    result.append(myrow, ignore_index=True)

  #Vente classique
  elif (canbuy == False and coin > 0 and sellCondition(row, previousrow) == True):
    sellprice = row['Close']
    usdt = usdt + (coin * sellprice) - (coin * sellprice * taxe)

    wallet = usdt

    lastcoinamount = coin
    coin = 0

    canbuy = True

    myrow = {'date': x, 'type': "SELL", 'price': sellprice, 'amount': lastcoinamount, 'coins': coin, 'frais': lastcoinamount * sellprice * taxe, 'newwallet': wallet}
    result.append(myrow, ignore_index=True)

  previousrow = row

# %%
print(result)
# %%
