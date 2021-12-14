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

datas = datas.drop(columns=['QAV', 'NofTrades', 'tbase', 'tquote', 'ignore', 'Closetime'])

#%%
dcp = datas.copy()

smawindow = 10
rsiwindow = 20

dcp["SMA"] = ta.trend.sma_indicator(dcp['Close'], window=smawindow)
dcp["RSI"] = ta.momentum.rsi(dcp['Close'], window=rsiwindow)

stoch = ta.momentum.StochasticOscillator(dcp['High'], dcp['Low'], dcp['Close'], window=rsiwindow, smooth_window=3)
dcp["STOCH_K"] = stoch.stoch()
dcp["STOCH_D"] = stoch.stoch_signal()
print(dcp)


#BOUCLE
usdt = 1000
startusdt = usdt

taxe = 0.0007

startcoin = ((usdt * taxe) / dcp.iloc[0]['Close'])
coin = 0

maker = 0.0005

sltaux = 0.02
tptaux = 0.1

canbuy = True

result = None
result = pd.DataFrame(columns=['date', 'type', 'price', 'amount', 'coins', 'frais', 'usdt'])

previousrow = dcp.iloc[0]

def buyCondition(row, prev):
  if (row['STOCH_K'] > row['STOCH_D'] and prev['STOCH_K'] < prev['STOCH_D'] and row['STOCH_K'] < 20
    and row["SMA"] > row["Close"]
    and row["RSI"] < 30):
    return True
  else:
    return False

def sellCondition(row, prev):
  if (row["RSI"] > 70):
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

    myrow = {'date': x, 'type': "BUY", 'price': buyprice, 'amount': prevusdt, 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  #StopLoss
  elif (coin > 0 and stoploss > row['Low']):
    sellprice = stoploss

    frais = float(coin * taxe)
    usdt = coin * sellprice
    coin = 0

    canbuy = True

    myrow = {'date': x, 'type': "STOPLOSS", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  # #TakeProfit
  elif (coin > 0 and takeprofit < row['High']):
    sellprice = takeprofit

    frais = float(coin * taxe)
    usdt = coin * sellprice
    coin = 0

    canbuy = True

    myrow = {'date': x, 'type': "TAKEPROFIT", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  # #Vente classique
  elif (canbuy == False and coin > 0 and sellCondition(row, previousrow) == True):
    sellprice = row['Close']

    frais = float(coin * taxe)
    sansfrais = coin * sellprice

    coin = coin - frais
    usdt = coin * sellprice
    coin = 0

    canbuy = True

    myrow = {'date': x, 'type': "SELL", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt}
    result = result.append(myrow, ignore_index=True)

  previousrow = row


print("USDT AU DEBUT : ", startusdt)
print("USDT A LA FIN : ", usdt)

print(result['type'].value_counts())

print(result)
# %%
