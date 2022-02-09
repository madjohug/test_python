import threading
import time
import requests 
from datetime import datetime, timedelta
import pandas as pd
import ta
import sys
from binance import exceptions, Client, enums
import asyncio

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

def getBalance():
  e = client.futures_account_balance()
  df = pd.DataFrame(e, columns=["alias", "asset", "balance", "withdrawAvailable", "updatetime"])
  df = df[df["asset"] == "USDT"]
  return df.iloc[0].balance

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

client = Client("Tr80L4Fnm2g4m8gnI3YlrCGR0XhlW9shMmVw01IYrE6Kjrd5WRdisaFIGguwp1jN",
                "D5GHjiCbJx1eR69hHRGY6Gzc9HGTZF2LpzMuPxzDFvqd9PdWGWsv4oBLGUggAHDH")

client.futures_change_leverage(symbol=symbol, leverage=int(levier))

def wait(n, t, s, b, sl, tp, w, pb):
  asyncio.run(loop(n, t, s, b, sl, tp, w, pb))

async def loop(savedTime, canBuy, symbol, buytype, stoploss, takeprofit, wallet, pricebought):
  
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
          buyPrice = await client.get_symbol_ticker(symbol=symbol)['price']
          await client.futures_create_order(
            symbol=symbol,
            side=enums.SIDE_BUY,
            positionSide="LONG",
            type=enums.ORDER_TYPE_LIMIT,
            timeInForce=enums.TIME_IN_FORCE_IOC,
            price=buyPrice,
            quantity=0.001
          )
          await client.futures_create_order(
            symbol=symbol,
            side=enums.SIDE_SELL,
            positionSide="LONG",
            type=enums.FUTURE_ORDER_TYPE_STOP,
            timeInForce=enums.TIME_IN_FORCE_GTC,
            stopPrice=(buyPrice - sltaux * buyPrice),
            quantity=0.001
          )
          await client.futures_create_order(
            symbol=symbol,
            side=enums.SIDE_SELL,
            positionSide="LONG",
            type=enums.FUTURE_ORDER_TYPE_TAKE_PROFIT,
            timeInForce=enums.TIME_IN_FORCE_GTC,
            stopPrice=(buyPrice + tptaux * buyPrice),
            quantity=0.001
          )
          buytype = 2
          canBuy = False

        elif(buyShortCondition(df.iloc[-1], df.iloc[-2])):
          buyPrice = await client.get_symbol_ticker(symbol=symbol)['price']
          await client.futures_create_order(
            symbol=symbol,
            side=enums.SIDE_BUY,
            positionSide="SHORT",
            type=enums.ORDER_TYPE_LIMIT,
            timeInForce=enums.TIME_IN_FORCE_IOC,
            price=buyPrice,
            quantity=0.001
          )
          await client.futures_create_order(
            symbol=symbol,
            side=enums.SIDE_SELL,
            positionSide="SHORT",
            type=enums.FUTURE_ORDER_TYPE_STOP,
            timeInForce=enums.TIME_IN_FORCE_GTC,
            stopPrice=(buyPrice - sltaux * buyPrice),
            quantity=0.001
          )
          await client.futures_create_order(
            symbol=symbol,
            side=enums.SIDE_SELL,
            positionSide="SHORT",
            type=enums.FUTURE_ORDER_TYPE_TAKE_PROFIT,
            timeInForce=enums.TIME_IN_FORCE_GTC,
            stopPrice=(buyPrice + tptaux * buyPrice),
            quantity=0.001
          )
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

      # Vente classique long
      if(buytype == 2 and sellLongCondition(df.iloc[-1], df.iloc[-2])):
        sellPrice = await client.get_symbol_ticker(symbol=symbol)['price']
        await client.futures_create_order(
          symbol=symbol,
          side=enums.SIDE_SELL,
          positionSide="LONG",
          type=enums.FUTURE_ORDER_TYPE_LIMIT,
          timeInForce=enums.TIME_IN_FORCE_GTC,
          quantity=0.001,
          price=sellPrice
        )
        buytype = 0
        canBuy = True

      # Vente classique short
      elif(buytype == -2 and sellShortCondition(df.iloc[-1])):
        sellPrice = await client.get_symbol_ticker(symbol=symbol)['price']
        await client.futures_create_order(
          symbol=symbol,
          side=enums.SIDE_SELL,
          positionSide="SHORT",
          type=enums.FUTURE_ORDER_TYPE_LIMIT,
          timeInForce=enums.TIME_IN_FORCE_GTC,
          quantity=0.001,
          price=sellPrice
        )
        buytype = 0
        canBuy = True

    savedTime = df.index[len(df) - 1]
    threading.Timer(1.0, wait, [savedTime, canBuy, symbol, buytype, stoploss, takeprofit, wallet, pricebought]).start()
  except exceptions.BinanceAPIException as e:
    file.write("\nException survenue : \nCode : " + e.status_code + "\nMessage : " + e.message)
    threading.Timer(1.0, wait, [savedTime, canBuy, symbol, buytype, stoploss, takeprofit, wallet, pricebought]).start()
  except requests.exceptions.ConnectionError as e:
    file.write("\nException survenue")
    threading.Timer(1.0, wait, [savedTime, canBuy, symbol, buytype, stoploss, takeprofit, wallet, pricebought]).start()

file = open(filename, "a")
file.write("\nLancement du bot le : " + now.strftime("%m/%d/%Y, %H:%M:%S"))
file.write("\nDonnées entrées pour ce bot : "+ "\n    Stoploss : "+ str(sltaux)+ "\n    Takeprofit : "+ str(tptaux)+ "\n    Levier : "+ str(levier))
file.write("\nPaire utilisée : " + symbol)
file.write("\nSolde de départ : " + str(wallet))
file.close()

asyncio.run(wait(now, True, symbol, buytype, stoploss, takeprofit, wallet, pricebought))