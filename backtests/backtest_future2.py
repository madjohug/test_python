#%%  Imports

import pandas as pd
from binance.client import Client
import ta

#%%
client = Client("Tr80L4Fnm2g4m8gnI3YlrCGR0XhlW9shMmVw01IYrE6Kjrd5WRdisaFIGguwp1jN",
                "D5GHjiCbJx1eR69hHRGY6Gzc9HGTZF2LpzMuPxzDFvqd9PdWGWsv4oBLGUggAHDH")

startdate = "01st December 2021"

klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, start_str=startdate)
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

# def check_haussier(df):
#   ret = True
#   for count, row in df.iterrows():
#     if (row["EMA_500"] >= row["Close"]):
#       ret = False
#   return ret 

# def check_baissier(df):
#   ret = True
#   for count, row in df.iterrows():
#     if (row["EMA_500"] <= row["Close"]):
#       ret = False
#   return ret  

smawindow = 10
rsiwindow = 14
smalong = 20
smavlong = 40
# sma100 = 100

dcp["SMA"] = ta.trend.sma_indicator(dcp['Close'], window=smawindow)
dcp["SMA_L"] = ta.trend.sma_indicator(dcp['Close'], window=smalong)
dcp["SMA_VL"] = ta.trend.sma_indicator(dcp['Close'], window=smavlong)
# dcp["SMA_100"] = ta.trend.sma_indicator(dcp['Close'], window=sma100)

dcp["RSI"] = ta.momentum.rsi(dcp['Close'], window=rsiwindow)

stoch = ta.momentum.StochasticOscillator(dcp['High'], dcp['Low'], dcp['Close'], window=rsiwindow, smooth_window=3)
dcp["STOCH_K"] = stoch.stoch()
dcp["STOCH_D"] = stoch.stoch_signal()

dcp["TREND"] = dcp.iloc[-smalong]["SMA_L"] - dcp["SMA_L"]
# dcp["TREND1"] = dcp.iloc[-smawindow]["SMA"] - dcp["SMA"]
# dcp["TREND2"] = dcp.iloc[-smavlong]["SMA_VL"] - dcp["SMA_VL"]
# dcp["TREND3"] = dcp.iloc[-180]["SMA_100"] - dcp["SMA_100"]

# dcp["HAUSSIER"] = (dcp["TREND"] < 0.0) & (dcp["TREND1"] < 0.0) & (dcp["TREND2"] < 0.0) & (dcp["TREND3"] < 0.0)
# dcp["BAISSIER"] = (dcp["TREND"] > 0.0) & (dcp["TREND1"] > 0.0) & (dcp["TREND2"] > 0.0) & (dcp["TREND3"] > 0.0)

# dcp["EMA_500"] = ta.trend.ema_indicator(dcp['Close'], window=500)
# dcp["HAUSSIER"] = check_haussier(ldcp.tail(50))
# dcp["BAISSIER"] = check_baissier(ldcp.tail(50))

dcp["DMI+"] = ta.trend.adx_pos(dcp["High"], dcp["Low"], dcp["Close"], window=14)
dcp["DMI-"] = ta.trend.adx_neg(dcp["High"], dcp["Low"], dcp["Close"], window=14)
dcp["DMIADX"] = ta.trend.adx(dcp["High"], dcp["Low"], dcp["Close"], window=14)

print(dcp)


#BOUCLE
usdt = 100
startusdt = usdt

taxe = 0.004

startcoin = ((usdt * taxe) / dcp.iloc[0]['Close'])
coin = 0

#ETH
sltaux = 0.004
tptaux = 0.004
levier = 7

# # #BTC
# sltaux = 0.01
# tptaux = 0.005
# levier = 4

canbuy = True
buytype = 0 # 1 pour long et -1 pour short
oldamount = usdt
shortbuyprice = 0

lastbuytime = dcp.iloc[0].index

bontrade = 0
mauvaistrade = 0

result = None
result = pd.DataFrame(columns=['date', 'type', 'price', 'amount', 'coins', 'frais', 'usdt', 'total', 'ope'])

plus_haut = usdt
plus_bas = usdt

previousrow = dcp.iloc[0]

def buyLongCondition(row, prev):
  if (row['STOCH_K'] > row['STOCH_D'] and prev['STOCH_K'] < prev['STOCH_D'] and row['STOCH_K'] < 20
    and row["SMA"] > row["Close"]
    and row["RSI"] < 30
    and row["TREND"] > 0
    # and row["HAUSSIER"] == True
    and row["SMA_L"] < row["SMA_VL"]):
    return True
  else:
    return False

def sellLongCondition(row, prev):
  if (row["RSI"] > 70):
    return True
  else:
    return False

def buyShortCondition(row, prev):
  if (row['STOCH_K'] < row['STOCH_D'] and prev['STOCH_K'] > prev['STOCH_D'] and row['STOCH_K'] > 80
    and row["SMA"] < row["Close"]
    and row["RSI"] > 70
    and row["TREND"] < 0
    # and row["BAISSIER"] == True
    and row["SMA_L"] > row["SMA_VL"]):
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

    lastbuytime = x

    myrow = {'date': x, 'type': "BUY LONG", 'price': buyprice, 'amount': prevusdt, 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt, 'total': oldamount, 'ope': 'buy'}
    result = result.append(myrow, ignore_index=True)

  # Buy short
  if (buyShortCondition(row, previousrow) == True and canbuy == True and usdt > 0):
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

    lastbuytime = x

    myrow = {'date': x, 'type': "BUY SHORT", 'price': buyprice, 'amount': prevusdt, 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt, 'total': oldamount, 'ope': 'buy'}
    result = result.append(myrow, ignore_index=True)

  #StopLoss long
  elif (coin > 0 and buytype == 1 and canbuy == False and stoploss > row['Low']):
    sellprice = stoploss

    percentlost = (1 - (buyprice / sellprice)) * levier

    usdt = oldamount + (percentlost * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    # set le min
    if (usdt < plus_bas):
      plus_bas = usdt

    print("sl long", x, " apr??s avoir achet?? le ", lastbuytime)

    mauvaistrade += 1

    myrow = {'date': x, 'type': "STOPLOSS LONG", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt, 'total': usdt, 'ope': 'sell'}
    result = result.append(myrow, ignore_index=True)
  
  #StopLoss short
  elif (coin > 0 and buytype == -1 and canbuy == False and stoploss < row['Low']):
    sellprice = stoploss

    percentlost = (1 - (sellprice / shortbuyprice)) * levier

    usdt = oldamount + (percentlost * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    # set le min
    if (usdt < plus_bas): 
      plus_bas = usdt
    
    print("sl short", x, " apr??s avoir achet?? le ", lastbuytime)

    mauvaistrade += 1

    myrow = {'date': x, 'type': "STOPLOSS SHORT", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt, 'total': usdt, 'ope': 'sell'}
    result = result.append(myrow, ignore_index=True)

  # TakeProfit long
  elif (coin > 0 and buytype == 1 and canbuy == False and takeprofit < row['High']):
    sellprice = takeprofit

    percentprofit = (1 - (buyprice / sellprice)) * levier

    usdt = oldamount + (percentprofit * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    bontrade += 1
    
    # set le max
    if (usdt > plus_haut): plus_haut = usdt

    myrow = {'date': x, 'type': "TAKEPROFIT LONG", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt, 'total': usdt, 'ope': 'sell'}
    result = result.append(myrow, ignore_index=True)

  # TakeProfit short
  elif (coin > 0 and buytype == -1 and canbuy == False and takeprofit > row['High']):
    sellprice = takeprofit

    percentprofit = (1 - (sellprice / shortbuyprice)) * levier

    usdt =  oldamount + (percentprofit * oldamount)
    coin = 0

    canbuy = True
    buytype = 0

    bontrade += 1

    # set le max
    if (usdt > plus_haut): plus_haut = usdt

    myrow = {'date': x, 'type': "TAKEPROFIT SHORT", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt, 'total': usdt, 'ope': 'sell'}
    result = result.append(myrow, ignore_index=True)

  # Vente classique long
  elif (canbuy == False and coin > 0 and buytype == 1 and sellLongCondition(row, previousrow) == True):
    sellprice = row['Close']

    frais = float(coin * taxe)
    sansfrais = coin * sellprice

    percentprofit = (1 - (buyprice / sellprice)) * levier

    usdt = oldamount + (percentprofit * oldamount)
    coin = 0

    if (usdt >= oldamount): bontrade += 1
    else: mauvaistrade += 1

    canbuy = True
    buytype = 0

    # set le max
    if (usdt > plus_haut): plus_haut = usdt

    # set le min
    if (usdt < plus_bas): plus_bas = usdt

    myrow = {'date': x, 'type': "SELL LONG", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt, 'total': usdt, 'ope': 'sell'}
    result = result.append(myrow, ignore_index=True)

  # Vente classique short
  elif (canbuy == False and coin > 0 and buytype == -1 and sellShortCondition(row) == True):
    sellprice = row['Close']

    frais = float(coin * taxe)
    sansfrais = coin * sellprice

    percentprofit = (1 - (sellprice / shortbuyprice)) * levier

    usdt = oldamount + (percentprofit * oldamount)
    coin = 0

    if (usdt >= oldamount): bontrade += 1
    else: mauvaistrade += 1

    canbuy = True
    buytype = 0

    if (usdt > plus_haut): plus_haut = usdt

    myrow = {'date': x, 'type': "SELL SHORT", 'price': sellprice, 'amount': "", 'coins': coin, 'frais': float("{:.5f}".format(frais)), 'usdt': usdt, 'total': usdt, 'ope': 'sell'}
    result = result.append(myrow, ignore_index=True)
    

  previousrow = row


finalv = usdt
if (bontrade == 0):
  print("\nBon trade ??tait ?? 0")
  bontrade = 1

if (result.iloc[-1]["type"] in ["BUY SHORT", "BUY LONG"]): finalv = result.iloc[-2]["usdt"]
print("\n")
print("------------ BILAN --------------")
print("\nDonn??es entr??es pour ce test : ", "\n    Stoploss : ", sltaux, "\n    Takeprofit : ", tptaux, "\n    Levier : ", levier)
print("\nDate de d??but : ", startdate, "\n\n")
print("USDT AU DEBUT : ", startusdt)
print("USDT A LA FIN : ", finalv)
print("Nombre d'op??rations : ", len(result))
print("\n")
print("POURCENTAGE DE GAIN : ", float("{:.1f}".format(((finalv / startusdt) - 1) * 100)), "%")
print("PLUS HAUT MONTANT ATTEINT : ", plus_haut)
print("PLUS BAS MONTANT ATTEINT : ", plus_bas)
print("\n")
print("BONS TRADES : ", bontrade)
print("MAUVAIS TRADES : ", mauvaistrade)
print("\nWin rate : ", float("{:.1f}".format((1-(mauvaistrade / bontrade)) * 100)), "%")
print("\n")
print(result['type'].value_counts())
print("\n")

result = result[result['ope'] == 'sell']
plot = result.plot(x="date", y="total", kind="line", figsize=(20,10))
print(plot)

print(result)
# %%
