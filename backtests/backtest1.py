import flask
import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app
import ta
import numpy as np

client = Client()

def getAvg(entries):
  return sum(entries) / len(entries)

klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1HOUR, "1st September 2021")
datas = pd.DataFrame(klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore'])
datas['High'] = pd.to_numeric(datas['High'])
datas['Low'] = pd.to_numeric(datas['Low'])
datas['Close'] = pd.to_numeric(datas['Close'])
datas['Open'] = pd.to_numeric(datas['Open'])

datas = datas.set_index(datas['timestamp'])
datas.index = pd.to_datetime(datas.index, unit="ms")

datas = datas.drop(columns=['QAV', 'NofTrades', 'tbase', 'tquote', 'ignore'])
dataCp = datas.copy()

#Initialisation des variables de tests
wallet = 100
mult=2.0
# source = prix de cloture
source = 20

bblength = 20
bbmult = 2.0

kclength = 20
kcmult = 1.5

usetruerange = True


# - Calculer moyenne mobile (MA)


sma = ta.trend.sma_indicator(dataCp['Close'], window=bblength)


# ---------------- Calculer Bandes de Bollinger --------------------

bb = ta.volatility.BollingerBands(close=dataCp['Close'], window=bblength, window_dev=bbmult)
dataCp['BB_H'] = bb.bollinger_hband()
dataCp['BB_L'] = bb.bollinger_lband()

# --------------------------------------------------------------------



# ------------ Calculer le KC ------------------

kc = ta.volatility.KeltnerChannel(high=dataCp['High'], low=dataCp['Low'], close=dataCp['Close'], window=kclength, original_version=usetruerange)
dataCp['KC_H'] = kc.keltner_channel_hband()
dataCp['KC_L'] = kc.keltner_channel_lband()

# ----------------------------------------------



# ------------ Calculer le SqzOn, SqzOff, et NoSqz ------------------

dataCp["SqzOn"] = ((dataCp["BB_L"] > dataCp["KC_L"]) & (dataCp["BB_H"] < dataCp["KC_H"]))
dataCp["SqzOff"] = ((dataCp["BB_L"] < dataCp["KC_L"]) & (dataCp["BB_H"] > dataCp["KC_H"]))
dataCp["NoSqz"] = ((dataCp["SqzOn"] == False) & (dataCp["SqzOff"] == False))

# -------------------------------------------------------------------



# ----------------- On calcule la valeur de l'indicateur squeeze ------------------

# val = linreg(source - avg(avg(highest(high, lengthKC), lowest(low, lengthKC)), sma(close, lengthKC)), lengthKC, 0)

# // Pour chaque ligne : linreg(x, y, z) => intercept + pente * (longueur - 1 - décalage) avec longueur = y, décalage = z, intercept et pentes calculées avec x

dataCp["highest"] = ta.volatility.donchian_channel_hband(high=dataCp['High'], low=dataCp['Low'], close=dataCp['Close'], window=kclength)
dataCp['lowest'] = ta.volatility.donchian_channel_lband(high=dataCp['High'], low=dataCp['Low'], close=dataCp['Close'], window=kclength)
dataCp["SMA2"] = ta.trend.sma_indicator(dataCp['Close'], window=kclength)
dataCp["AVG1"] = 
# ---------------------------------------------------------------------------------

print(dataCp)