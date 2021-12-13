import threading
import time
import requests 
from datetime import datetime, timedelta
import pandas as pd

now = datetime.fromtimestamp(time.time()).replace(second=0, microsecond=0) + timedelta(hours=-1)

def loop():
  threading.Timer(1.0, loop).start()
  t = float(round(time.time()))-0.5*3600 # - 30 minutes

  klines = requests.get("https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1m&startTime={t}").json()
  df = pd.DataFrame(klines, columns=['Opentime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'qas', 'not', 'tb', 'tq', 'i'])
  df['High'] = pd.to_numeric(df['High'])
  df['Low'] = pd.to_numeric(df['Low'])
  df['Close'] = pd.to_numeric(df['Close'])
  df['Open'] = pd.to_numeric(df['Open'])

  df = df.set_index(df['Opentime'])
  df.index = pd.to_datetime(df.index, unit="ms")

  df = df.drop(columns=['qas', 'not', 'tb', 'tq', 'i', 'Volume', 'Closetime'])
  print(df.iloc[-1]['Close'])
  



  
loop()