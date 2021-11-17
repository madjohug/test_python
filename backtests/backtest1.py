import flask
import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app
import ta
import numpy as np

client = Client()

def customPrint(msg, value):
  print("----------------- " + msg + " -------------------")
  print(value)

klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1HOUR, "1st September 2021")
datas = pd.DataFrame(klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore'])
datas['High'] = pd.to_numeric(datas['High'])
datas['Low'] = pd.to_numeric(datas['Low'])
datas['Close'] = pd.to_numeric(datas['Close'])
datas['Open'] = pd.to_numeric(datas['Open'])
#Initialisation des variables de tests
wallet = 100

# source = prix de cloture
source = 20

bblength = 20
bbmult = 20

kclength = 20
kcmult = 1.5

usetruerange = True

# - Calculer moyenne mobile (MA)
print("\n")

sma = ta.trend.sma_indicator(datas['Close'], window=bblength)
customPrint("SMA", sma)

print("\n")

# - Calculer Bandes de Bollinger
print("\n")

bb = ta.volatility.BollingerBands(close=datas['Close'], window=bblength, window_dev=2)
upperbb = bb.bollinger_hband()
lowerbb = bb.bollinger_lband()
customPrint("BB", upperbb)

print("\n")

# - Calculer le KC
print('\n')

kc = ta.volatility.KeltnerChannel(high=datas['High'], low=datas['Low'], close=datas['Close'], window=kclength, original_version=usetruerange)
upperkc = kc.keltner_channel_hband()
lowerkc = kc.keltner_channel_lband()
customPrint("KC", upperkc)

print('\n')

# - Calculer le SqzOn, SqzOff, et noSqz
print('\n')

sqzOn = lowerbb > lowerkc and upperbb < upperkc
sqzOff = lowerbb < lowerkc and upperbb > upperkc
noSqz = sqzOn == False and sqzOff == False

print('\n')

# - Calculer le momentum



# length = input(20, title="BB Length")
# mult = input(2.0, title="BB MultFactor")
# source = close
# lengthKC = input(20, title="KC Length")
# multKC = input(1.5, title="KC MultFactor")
# useTrueRange = input(true, title="Use TrueRange (KC)", type=input.bool)


# // Defining MA
# // sma renvoie la moyenne mobile : somme des dernières valeurs y de x, divisée par y
# ma = sma(source, length)


# // Calculate BB
# // stdev = deviation standard
# basis = ma
# dev = mult * stdev(source, length)
# upperBB = basis + dev
# lowerBB = basis - dev


# // Calculate KC
# // tr = gamme réelle. C'est max(haut - bas, abs(haut - proche[1]), abs(bas - proche[1]))
# range = useTrueRange ? tr : high - low
# rangema = sma(range, lengthKC)
# upperKC = ma + rangema * multKC
# lowerKC = ma - rangema * multKC


# // SqzON | SqzOFF | noSqz
# sqzOn = lowerBB > lowerKC and upperBB < upperKC
# sqzOff = lowerBB < lowerKC and upperBB > upperKC
# noSqz = sqzOn == false and sqzOff == false


# // Momentum
# val = linreg(source - avg(avg(highest(high, lengthKC), lowest(low, lengthKC)), sma(close, lengthKC)), lengthKC, 0)


# // Plots
# bcolor = iff(val > 0, iff(val > nz(val[1]), #00FF00, #008000), iff(val < nz(val[1]), #FF0000, #800000))
# scolor = noSqz ? color.blue : sqzOn ? color.black : color.gray
# plot(val, color=bcolor, style=plot.style_histogram, linewidth=4, transp = 50)
# plot(0, color=scolor, style=plot.style_cross, linewidth=2)

# sqzGREY = crossunder(lowerBB, lowerKC) and crossover(upperBB, upperKC)
# plotshape(sqzGREY, style = shape.circle, location = location.bottom, size = size.tiny)