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

symbol = sys.argv[1]
tptaux = float(sys.argv[2])
sltaux = float(sys.argv[3])
levier = float(sys.argv[4])
filename = sys.argv[5]

client = Client("Tr80L4Fnm2g4m8gnI3YlrCGR0XhlW9shMmVw01IYrE6Kjrd5WRdisaFIGguwp1jN",
                "D5GHjiCbJx1eR69hHRGY6Gzc9HGTZF2LpzMuPxzDFvqd9PdWGWsv4oBLGUggAHDH")

client.futures_change_leverage(symbol=symbol, leverage=int(levier))

async def loop(symbol):
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

    orders = client.futures_position_information(symbol=symbol)
    do = pd.DataFrame(orders)
    do["positionAmt"] = pd.to_numeric(do["positionAmt"])
    
    #Si je n'ai aucune position d'ouverte
    if (do["positionAmt"].sum() == 0.0):
        df["SMA"] = ta.trend.sma_indicator(df['Close'], window=smawindow)
        df["SMA_L"] = ta.trend.sma_indicator(df['Close'], window=smalong)
        df["SMA_VL"] = ta.trend.sma_indicator(df['Close'], window=smavlong)

        df["RSI"] = ta.momentum.rsi(df['Close'], window=rsiwindow)

        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=rsiwindow, smooth_window=3)
        df["STOCH_K"] = stoch.stoch()
        df["STOCH_D"] = stoch.stoch_signal()
        df["TREND"] = df.iloc[-smalong]["SMA_L"] - df["SMA_L"]

        if (buyLongCondition(df.iloc[-1], df.iloc[-2])):
          buyPrice = float(client.get_symbol_ticker(symbol=symbol)['price'])
          balance = float(getBalance())

          client.futures_create_order(
            symbol=symbol,
            side="BUY",
            positionSide="LONG",
            type="MARKET",
            quantity=(balance * 0.5) / buyPrice
          )
          await asyncio.sleep(1)
          client.futures_create_order(
            symbol=symbol,
            side="SELL",
            positionSide="LONG",
            type="STOP_MARKET",
            timeInForce="GTC",
            stopPrice=round((buyPrice - sltaux * buyPrice), 2),
            closePosition="true"
          )
          await asyncio.sleep(1)
          client.futures_create_order(
            symbol=symbol,
            side="SELL",
            positionSide="LONG",
            type="TAKE_PROFIT_MARKET",
            timeInForce="GTC",
            stopPrice=round((buyPrice + tptaux * buyPrice), 2),
            closePosition="true"
          )

        elif(buyShortCondition(df.iloc[-1], df.iloc[-2])):
          buyPrice = float(client.get_symbol_ticker(symbol=symbol)['price'])
          balance = float(getBalance())

          client.futures_create_order(
            symbol=symbol,
            side="SELL",
            positionSide="SHORT",
            type="MARKET",
            quantity=(balance * 0.5) / buyPrice
          )
          await asyncio.sleep(1)
          client.futures_create_order(
            symbol=symbol,
            side="BUY",
            positionSide="SHORT",
            type="STOP_MARKET",
            timeInForce="GTC",
            stopPrice=round((buyPrice + sltaux * buyPrice), 2),
            closePosition="true"
          )
          await asyncio.sleep(1)
          client.futures_create_order(
            symbol=symbol,
            side="BUY",
            positionSide="SHORT",
            type="TAKE_PROFIT_MARKET",
            timeInForce="GTC",
            stopPrice=round((buyPrice - tptaux * buyPrice), 2),
            closePosition="true"
          )

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
      if((do[do["positionSide"] == "LONG"]["positionAmt"].sum() != 0.0) and sellLongCondition(df.iloc[-1], df.iloc[-2])):
        sellquantity = do[do["positionSide"] == "LONG"]["positionAmt"]
        client.futures_create_order(
          symbol=symbol,
          side="SELL",
          positionSide="LONG",
          type="MARKET",
          quantity=abs(float(sellquantity)),
        )

      # Vente classique short
      elif((do[do["positionSide"] == "SHORT"]["positionAmt"].sum() != 0.0) and sellShortCondition(df.iloc[-1])):
        sellquantity = do[do["positionSide"] == "SHORT"]["positionAmt"]
        client.futures_create_order(
          symbol=symbol,
          side="BUY",
          positionSide="SHORT",
          type="MARKET",
          quantity=abs(float(sellquantity)),
        )

    threading.Timer(1.0, loop, [symbol]).start()
  except exceptions.BinanceAPIException as e:
    file.write("\nException survenue BinanceAPI")
    client.futures_cancel_all_open_orders(symbol=symbol)
    threading.Timer(1.0, loop, [symbol]).start()
  except requests.exceptions.ConnectionError as e:
    file.write("\nException survenue")
    client.futures_cancel_all_open_orders(symbol=symbol)
    threading.Timer(1.0, loop, [symbol]).start()

file = open(filename, "a")
file.write("\nLancement du bot le : " + now.strftime("%m/%d/%Y, %H:%M:%S"))
file.write("\nDonnées entrées pour ce bot : "+ "\n    Stoploss : "+ str(sltaux)+ "\n    Takeprofit : "+ str(tptaux)+ "\n    Levier : "+ str(levier))
file.write("\nPaire utilisée : " + symbol)

asyncio.run(loop(symbol))