import flask
import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app
import ta

client = Client()

klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1HOUR, "1st January 2020")
dataframe = pd.DataFrame(klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Closetime', 'QAV', 'NofTrades', 'tbase', 'tquote', 'ignore'])
dataframe.drop(['ignore', 'open', 'high', 'close', 'low'])

print(dataframe)

#Initialisation des variables de tests
wallet = 100

# - Calculer moyenne (MA)

# - Calculer Bandes de Bollinger

# - Calculer le KC

# - Calculer le SqzOn, SqzOff, et noSqz

# - Calculer le momentum



# length = input(20, title="BB Length")
# mult = input(2.0, title="BB MultFactor")
# source = close
# lengthKC = input(20, title="KC Length")
# multKC = input(1.5, title="KC MultFactor")
# useTrueRange = input(true, title="Use TrueRange (KC)", type=input.bool)

# // Defining MA
# ma = sma(source, length)

# // Calculate BB
# basis = ma
# dev = mult * stdev(source, length)
# upperBB = basis + dev
# lowerBB = basis - dev

# // Calculate KC
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