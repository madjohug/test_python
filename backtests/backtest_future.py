#%%  Imports

import pandas as pd
from binance.client import Client
import ta

#%%
client = Client()

klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, start_str="1st December 2021")
datas = pd.DataFrame(klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore'])
datas['High'] = pd.to_numeric(datas['High'])
datas['Low'] = pd.to_numeric(datas['Low'])
datas['Close'] = pd.to_numeric(datas['Close'])
datas['Open'] = pd.to_numeric(datas['Open'])

datas = datas.set_index(datas['timestamp'])
datas.index = pd.to_datetime(datas.index, unit="ms")

datas = datas.drop(columns=['Volume', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore', 'Closetime'])

#%%
dcp = datas.copy()

smalong = 100
smacourt = 14
atrperiod = 10
rsiperiod=14

dcp["SMA_L"] = ta.trend.sma_indicator(dcp['Close'], window=smalong)
dcp["SMA_C"] = ta.trend.sma_indicator(dcp['Close'], window=smacourt)
dcp["RSI"] = ta.momentum.rsi(dcp['Close'], window=rsiperiod)
dcp["ATR"] = ta.volatility.average_true_range(dcp["High"], dcp["Low"], dcp["Close"], window=atrperiod)

dcp["TREND"] = dcp.iloc[-60]["SMA_L"] - dcp["SMA_L"]
print(dcp)


#BOUCLE
usdt = 1000
startusdt = usdt

taxe = 0.004

startcoin = ((usdt * taxe) / dcp.iloc[0]['Close'])
coin = 0

maker = 0.0005

sltaux = 0.02
tptaux = 0.1
levier = 2

canbuy = True
buytype = 0 # 1 pour long et -1 pour short
oldamount = usdt
shortbuyprice = 0

result = None
result = pd.DataFrame(columns=['date', 'type', 'price', 'amount', 'coins', 'frais', 'usdt'])

plus_haut = usdt
previousrow = dcp.iloc[0]

def buyLongCondition(row, prev):
  if (row["ATR"] > 10 and 
      row["SMA_C"] > row["SMA_L"] and
      row["TREND"] < 0 and
      row["RSI"] < 30):
    return True
  else:
    return False

def sellLongCondition(row, prev):
  if (row["RSI"] > 70):
    return True
  else:
    return False

def buyShortCondition(row):
  if (row["ATR"] > 10 and 
      row["SMA_C"] < row["SMA_L"] and
      row["TREND"] > 0 and
      row["RSI"] > 70):
    return True
  else:
    return False

def sellShortCondition(row):
  if (row["RSI"] < 30):
    return True
  else:
    return False

for x, row in dcp.iterrows():
  #Buy long
  if (buyLongCondition(row, previousrow) == True and canbuy == True and usdt > 0):
    buyprice = row['Close']

    frais = float(usdt * taxe)
    coin = float(usdt / buyprice)
    prevusdt = usdt
    usdt = 0

    stoploss = buyprice - sltaux * buyprice
    takeprofit = buyprice + tptaux * buyprice
    oldamount = prevusdt

    canbuy = False
    buytype = 1

    myrow = {'date': x, 'type': "BUY LONG", 'price': buyprice, 'amount': prevusdt, 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  # Buy short
  if (buyShortCondition(row) == True and canbuy == True and usdt > 0):
    buyprice = row['Close']

    frais = float(usdt * taxe)
    coin = float(usdt / buyprice)
    prevusdt = usdt
    usdt = 0

    stoploss = buyprice + sltaux * buyprice
    takeprofit = buyprice - tptaux * buyprice

    canbuy = False
    buytype = -1
    oldamount = prevusdt
    shortbuyprice = buyprice

    myrow = {'date': x, 'type': "BUY SHORT", 'price': buyprice, 'amount': prevusdt, 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  #StopLoss long
  elif (coin > 0 and buytype == 1 and canbuy == False and stoploss > row['Low']):
    sellprice = stoploss

    percentlost = (1 - (buyprice / sellprice)) * levier

    usdt = oldamount + (percentlost * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    myrow = {'date': x, 'type': "STOPLOSS LONG", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)
  
  #StopLoss short
  elif (coin > 0 and buytype == -1 and canbuy == False and stoploss < row['Low']):
    sellprice = stoploss

    percentlost = (1 - (sellprice / shortbuyprice)) * levier

    usdt = oldamount + (percentlost * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    myrow = {'date': x, 'type': "STOPLOSS SHORT", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  # TakeProfit long
  elif (coin > 0 and buytype == 1 and canbuy == False and takeprofit < row['High']):
    sellprice = takeprofit

    percentprofit = (1 - (buyprice / sellprice)) * levier

    usdt = oldamount + (percentprofit * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    # set le max
    if (usdt > plus_haut): plus_haut = usdt

    myrow = {'date': x, 'type': "TAKEPROFIT LONG", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  # TakeProfit short
  elif (coin > 0 and buytype == -1 and canbuy == False and takeprofit > row['High']):
    sellprice = takeprofit

    percentprofit = (1 - (sellprice / shortbuyprice)) * levier

    usdt =  oldamount + (percentprofit * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    # set le max
    if (usdt > plus_haut): plus_haut = usdt

    myrow = {'date': x, 'type': "TAKEPROFIT SHORT", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  # Vente classique long
  elif (canbuy == False and coin > 0 and buytype == 1 and sellLongCondition(row, previousrow) == True):
    sellprice = row['Close']

    frais = float(coin * taxe)
    sansfrais = coin * sellprice

    percentprofit = (1 - (buyprice / sellprice)) * levier

    usdt = oldamount + (percentprofit * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    if (usdt > plus_haut): plus_haut = usdt

    myrow = {'date': x, 'type': "SELL LONG", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  # Vente classique short
  elif (canbuy == False and coin > 0 and buytype == -1 and sellShortCondition(row) == True):
    sellprice = row['Close']

    frais = float(coin * taxe)
    sansfrais = coin * sellprice

    percentprofit = (1 - (sellprice / shortbuyprice)) * levier

    usdt = oldamount + (percentprofit * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    if (usdt > plus_haut): plus_haut = usdt

    myrow = {'date': x, 'type': "SELL SHORT", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)
    

  previousrow = row

print("\n\n")
print("USDT AU DEBUT : ", startusdt)
print("USDT A LA FIN : ", usdt)
print("POURCENTAGE DE GAIN : ", ((usdt / startusdt) - 1) * 100, "%")
print("PLUS HAUT MONTANT ATTEINT : ", plus_haut)
print(result['type'].value_counts())
print("\n\n")

print(result)
# %%
