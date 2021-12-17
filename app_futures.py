import threading
import time
import requests 
from datetime import datetime, timedelta
import pandas as pd
import ta
import sys

def buyCondition(row, prev):
  if (row['STOCH_K'] > row['STOCH_D'] and prev['STOCH_K'] < prev['STOCH_D'] and row['STOCH_K'] < 20
    and row["SMA"] > row["Close"]
    and row["RSI"] < 30):
    return True
  else:
    return False

def sellCondition(row, prev):
  if (row["RSI"] > 70 and prev["RSI"] <= 70):
    return True
  else:
    return False

def writeInFile(filename, message):
  file = open(filename, "a")
  file.write("\n" + message)
  file.close()

now = datetime.fromtimestamp(time.time()).replace(second=0, microsecond=0) + timedelta(hours=-1)

def loop(savedTime, canBuy, symbol):
  threading.Timer(60.0, loop, [savedTime, canBuy, symbol]).start()
  
  t = float(round(time.time()))-0.5*3600 # - 30 minutes

  url = ("https://fapi.binance.com/fapi/v1/klines?symbol=" + symbol + "&interval=1m&startTime=" + str(t))
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


  print(df.iloc[-1]['Close'], " à : ", df.index[len(df) - 1].strftime("%H:%M:%S"))

  # Sinon, je check si je peux acheter, si je suis à une nouvelle minute
  if (canBuy == True):
    # Si je suis à une nouvelle minute, je fais le check, sinon je passe
    if (df.index[len(df) - 1] != savedTime): 
      df["SMA"] = ta.trend.sma_indicator(df['Close'], window=smawindow)
      df["RSI"] = ta.momentum.rsi(df['Close'], window=rsiwindow)

      stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=rsiwindow, smooth_window=3)
      df["STOCH_K"] = stoch.stoch()
      df["STOCH_D"] = stoch.stoch_signal()
      if (buyCondition(df.iloc[-1], df.iloc[-2])):
        writeInFile("log.txt", "Achat le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") +  " à : " + str(df.iloc[-1]["Close"]))
        canBuy = False

  else:
    df["SMA"] = ta.trend.sma_indicator(df['Close'], window=smawindow)
    df["RSI"] = ta.momentum.rsi(df['Close'], window=rsiwindow)

    stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=rsiwindow, smooth_window=3)
    df["STOCH_K"] = stoch.stoch()
    df["STOCH_D"] = stoch.stoch_signal()

  # Si j'ai un ordre en cours, je check chaque seconde si je dois vendre
    if (sellCondition(df.iloc[-1], df.iloc[-2])):
      writeInFile("log.txt", "Vente le : " + df.index[len(df) - 1].strftime("%m/%d/%Y, %H:%M:%S") + " à : " + str(df.iloc[-1]["Close"]))
      canBuy == True

  savedTime = df.index[len(df) - 1]

symbol = sys.argv[1]
file = open("log.txt", "a")
file.write("\nLancement du bot le : " + now.strftime("%m/%d/%Y, %H:%M:%S"))
file.write("\nPaire utilisée : " + symbol)
file.close()

loop(now, True, symbol)

# STRATEGIE A TESTER :

# ATR PERIODE 10 SUR SMA
# RSI CLASSIQUE
# SMA PERIODE 100 POUR LA TENDANCE
# A VOIR AVEC SMA 14
# SI ATR > 5 (OU 4) ET TENDANCE BAISSIERE ET RSI > 70 (ET SMA 14 EN DESSOUS DE SMA 100): SHORT
# SI ATR > 5 (OU 4) ET TENDANCE HAUSSIERE ET RSI < 30 (ET SMA 14 AU DESSUS DE SMA 100): LONG