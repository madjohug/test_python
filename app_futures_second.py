# -*- coding: utf-8 -*-

import threading
import time
import requests 
from datetime import datetime, timedelta
import pandas as pd
import ta
import sys
from binance import exceptions

def buyLongCondition(row, prev):
  if (row['STOCH_K'] > row['STOCH_D'] and prev['STOCH_K'] < prev['STOCH_D'] and row['STOCH_K'] < 20
    and row["SMA"] > row["Close"]
    and row["RSI"] < 30
    and row["TREND"] > 0
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
    and row["SMA_L"] > row["SMA_VL"]):
    return True
  else:
    return False

def sellShortCondition(row):
  if (row["RSI"] < 30):
    return True
  else:
    return False

def writeInFile(filename, message):
  file = open(filename, "a")
  file.write("\n" + message)
  file.close()

now = datetime.fromtimestamp(time.time()).replace(second=0, microsecond=0) + timedelta(hours=-1)

buytype = 0
stoploss = 0
takeprofit = 100000
wallet = 100
pricebought = 1

symbol = sys.argv[1]
tptaux = float(sys.argv[2])
sltaux = float(sys.argv[3])
levier = float(sys.argv[4])
filename = sys.argv[5]

def loop(savedTime, canBuy, symbol, buytype, stoploss, takeprofit, wallet, pricebought):
  
  t = float(round(time.time()))-0.75*3600 # - 45 minutes

  url = ("https://fapi.binance.com/fapi/v1/klines?symbol=" + symbol + "&interval=1m&startTime=" + str(t))
  try: 
    klines = requests.get(url).json()
    df = pd.DataFrame(klines, columns=['Opentime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'qas', 'not', 'tb', 'tq', 'i'])
    df['High'] = pd.to_numeric(df['High'])
    df['Low'] = pd.to_numeric(df['Low'])
    df['Close'] = pd.to_numeric(df['Close'])
    df['Open'] = pd.to_numeric(df['Open'])

    df = df.set_index(df['Opentime'])
    df.index = pd.to_datetime(df.index, unit="ms")

    smawindow = 10
    rsiwindow = 14
    smalong = 20
    smavlong = 40

    print(df.iloc[-1]['Close'], " à : ", df.index[len(df) - 1].strftime("%H:%M:%S"))

    # Sinon, je check si je peux acheter, si je suis à une nouvelle minute
    if (canBuy == True):
        df["SMA"] = ta.trend.sma_indicator(df['Close'], window=smawindow)
        df["SMA_L"] = ta.trend.sma_indicator(df['Close'], window=smalong)
        df["SMA_VL"] = ta.trend.sma_indicator(df['Close'], window=smavlong)

        df["RSI"] = ta.momentum.rsi(df['Close'], window=rsiwindow)

        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=rsiwindow, smooth_window=3)
        df["STOCH_K"] = stoch.stoch()
        df["STOCH_D"] = stoch.stoch_signal()
        df["TREND"] = df.iloc[-smalong]["SMA_L"] - df["SMA_L"]

        if (buyLongCondition(df.iloc[-1], df.iloc[-2])):
          buyprice = df.iloc[-1]['Close']
          pricebought = buyprice
          stoploss = buyprice - sltaux * buyprice
          takeprofit = buyprice + tptaux * buyprice
          writeInFile(filename, "Achat long le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") +  " à : " + str(buyprice))
          buytype = 2
          canBuy = False

        elif(buyShortCondition(df.iloc[-1], df.iloc[-2])):
          buyprice = df.iloc[-1]['Close']
          pricebought = buyprice
          stoploss = buyprice + sltaux * buyprice
          takeprofit = buyprice - tptaux * buyprice
          writeInFile(filename, "Achat short le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") +  " à : " + str(buyprice))
          buytype = -2
          canBuy = False

    else:
      df["SMA"] = ta.trend.sma_indicator(df['Close'], window=smawindow)
      df["SMA_L"] = ta.trend.sma_indicator(df['Close'], window=smalong)
      df["SMA_VL"] = ta.trend.sma_indicator(df['Close'], window=smavlong)

      df["RSI"] = ta.momentum.rsi(df['Close'], window=rsiwindow)

      stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=rsiwindow, smooth_window=3)
      df["STOCH_K"] = stoch.stoch()
      df["STOCH_D"] = stoch.stoch_signal()
      df["TREND"] = df.iloc[-smalong]["SMA_L"] - df["SMA_L"]

      closeprice = df.iloc[-1]["Close"]
      # Si j'ai un ordre en cours, je check chaque seconde si je dois vendre
      # StopLoss long
      if(buytype == 2 and closeprice < stoploss):
        pricesold = df.iloc[-1]["Close"]
        writeInFile(filename, "Stoploss long le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") +  " à : " + str(pricesold))
        buytype = 0
        percent = (1 - (pricebought / pricesold)) * levier
        wallet = wallet + (wallet * percent)
        writeInFile(filename, "Nouveau solde : " + str(wallet) + "\n")
        canBuy = True
    
      # StopLoss short
      elif(buytype == -2 and closeprice > stoploss):
        pricesold = df.iloc[-1]["Close"]
        writeInFile(filename, "Stoploss short le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") +  " à : " + str(pricesold))
        buytype = 0      
        percent = (1 - (pricesold / pricebought)) * levier
        wallet = wallet + (wallet * percent)
        writeInFile(filename, "Nouveau solde : " + str(wallet) + "\n")
        canBuy = True

    # TakeProfit long
      elif(buytype == 2 and closeprice > takeprofit):
        pricesold = df.iloc[-1]["Close"]
        writeInFile(filename, "Takeprofit long le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") +  " à : " + str(pricesold))
        buytype = 0
        percent = (1 - (pricebought / pricesold)) * levier
        wallet = wallet + (wallet * percent)
        writeInFile(filename, "Nouveau solde : " + str(wallet) + "\n")
        canBuy = True

    # TakeProfit short
      elif(buytype == -2 and closeprice < takeprofit):
        pricesold = df.iloc[-1]["Close"]
        writeInFile(filename, "Takeprofit short le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") +  " à : " + str(pricesold))
        buytype = 0
        percent = (1 - (pricesold / pricebought)) * levier
        wallet = wallet + (wallet * percent)
        writeInFile(filename, "Nouveau solde : " + str(wallet) + "\n")
        canBuy = True

    # Vente classique long
      elif(buytype == 2 and sellLongCondition(df.iloc[-1], df.iloc[-2])):
        pricesold = df.iloc[-1]["Close"]
        writeInFile(filename, "Vente long le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") +  " à : " + str(pricesold))
        buytype = 0
        percent = (1 - (pricebought / pricesold)) * levier
        wallet = wallet + (wallet * percent)
        writeInFile(filename, "Nouveau solde : " + str(wallet) + "\n")
        canBuy = True

    # Vente classique short
      elif(buytype == -2 and sellShortCondition(df.iloc[-1])):
        pricesold = df.iloc[-1]["Close"]
        writeInFile(filename, "Vente short le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") +  " à : " + str(pricesold))
        buytype = 0
        percent = (1 - (pricesold / pricebought)) * levier
        wallet = wallet + (wallet * percent)
        writeInFile(filename, "Nouveau solde : " + str(wallet) + "\n")
        canBuy = True

    savedTime = df.index[len(df) - 1]
    threading.Timer(1.0, loop, [savedTime, canBuy, symbol, buytype, stoploss, takeprofit, wallet, pricebought]).start()
  except exceptions.BinanceAPIException as e:
    file.write("\nException survenue : \nCode : " + e.status_code + "\nMessage : " + e.message)
    threading.Timer(1.0, loop, [savedTime, canBuy, symbol, buytype, stoploss, takeprofit, wallet, pricebought]).start()
  except requests.exceptions.ConnectionError as e:
    file.write("\nException de Connection survenue")
    threading.Timer(1.0, loop, [savedTime, canBuy, symbol, buytype, stoploss, takeprofit, wallet, pricebought]).start()

file = open(filename, "a")
file.write("\nLancement du bot le : " + now.strftime("%m/%d/%Y, %H:%M:%S"))
file.write("\nDonnées entrées pour ce bot : "+ "\n    Stoploss : "+ str(sltaux)+ "\n    Takeprofit : "+ str(tptaux)+ "\n    Levier : "+ str(levier))
file.write("\nPaire utilisée : " + symbol)
file.write("\nSolde de départ : " + str(wallet))
file.close()

loop(now, True, symbol, buytype, stoploss, takeprofit, wallet, pricebought)

# STRATEGIE A TESTER :

# ATR PERIODE 10 SUR SMA
# RSI CLASSIQUE
# SMA PERIODE 100 POUR LA TENDANCE
# A VOIR AVEC SMA 14
# SI ATR > 5 (OU 4) ET TENDANCE BAISSIERE ET RSI > 70 (ET SMA 14 EN DESSOUS DE SMA 100): SHORT
# SI ATR > 5 (OU 4) ET TENDANCE HAUSSIERE ET RSI < 30 (ET SMA 14 AU DESSUS DE SMA 100): LONG