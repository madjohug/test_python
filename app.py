#%%
import flask
import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app
import ta


apikey = "Tr80L4Fnm2g4m8gnI3YlrCGR0XhlW9shMmVw01IYrE6Kjrd5WRdisaFIGguwp1jN"
secret = "D5GHjiCbJx1eR69hHRGY6Gzc9HGTZF2LpzMuPxzDFvqd9PdWGWsv4oBLGUggAHDH"

client = Client(apikey, secret)

symbol = "ETHUSDT"

klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1MINUTE, start_str="15th January 2022")
datas = pd.DataFrame(klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore'])
datas['High'] = pd.to_numeric(datas['High'])
datas['Low'] = pd.to_numeric(datas['Low'])
datas['Close'] = pd.to_numeric(datas['Close'])
datas['Open'] = pd.to_numeric(datas['Open'])
datas = datas.set_index(datas['timestamp'])
datas.index = pd.to_datetime(datas.index, unit="ms")
datas = datas.drop(columns=['Volume', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore', 'Closetime'])

#%%
def check_haussier(df):
  ret = True
  for count, row in df.iterrows():
    if (row["EMA_300"] <= row["Close"]):
      ret = False
  return ret  
    
dcp = datas.copy()
dcp["EMA_300"] = ta.trend.ema_indicator(dcp['Close'], window=500)
print(dcp)

test = check_haussier(dcp.tail(300))
print("test", test)



#EMA 500, regarder sur les 200/300 dernières bougies si je suis en tendance haussiere/baissiere
# -> toujours ema > close : tendance baissiere, je fais que du short
# sinon je fais que du long
# %%
