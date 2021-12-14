import threading
import time
import requests 
from datetime import datetime, timedelta
import pandas as pd
import ta


def buyCondition(row, prev):
  if (row['STOCH_K'] > row['STOCH_D'] and prev['STOCH_K'] < prev['STOCH_D'] and row['STOCH_K'] < 20
    and row["SMA"] > row["Close"]
    and row["RSI"] < 30):
    return True
  else:
    return False

def sellCondition(row):
  if (row["RSI"] > 70):
    return True
  else:
    return False

now = datetime.fromtimestamp(time.time()).replace(second=0, microsecond=0) + timedelta(hours=-1)

def loop(savedTime, canBuy):

  t = float(round(time.time()))-0.5*3600 # - 30 minutes

  klines = requests.get("https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1m&startTime={t}").json()
  df = pd.DataFrame(klines, columns=['Opentime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'qas', 'not', 'tb', 'tq', 'i'])
  df['High'] = pd.to_numeric(df['High'])
  df['Low'] = pd.to_numeric(df['Low'])
  df['Close'] = pd.to_numeric(df['Close'])
  df['Open'] = pd.to_numeric(df['Open'])

  df = df.set_index(df['Opentime'])
  df.index = pd.to_datetime(df.index, unit="ms")

  smawindow = 10
  rsiwindow = 20


  print(df.iloc[-1]['Close'])

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
        print("ACHAT A LA DATE : ", df.index[len(df) - 1], "AU PRIX : ", df.iloc[-1]["Close"])
        canBuy = False

  else:
    df["SMA"] = ta.trend.sma_indicator(df['Close'], window=smawindow)
    df["RSI"] = ta.momentum.rsi(df['Close'], window=rsiwindow)

    stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=rsiwindow, smooth_window=3)
    df["STOCH_K"] = stoch.stoch()
    df["STOCH_D"] = stoch.stoch_signal()

  # Si j'ai un ordre en cours, je check chaque seconde si je dois vendre
    if (sellCondition(df.iloc[-1])):
      print("VENTE A LA DATE : ", df.index[len(df) - 1], "AU PRIX : ", df.iloc[-1]["Close"])
      canBuy == True

  savedTime = df.index[len(df) - 1]
  
  threading.Timer(1.0, loop, [savedTime, canBuy]).start()

  
loop(now, False)