#%%
from datetime import datetime
from tkinter import BOTH
from binance import  Client, enums
import asyncio
import requests 
from time import time

client = Client("Tr80L4Fnm2g4m8gnI3YlrCGR0XhlW9shMmVw01IYrE6Kjrd5WRdisaFIGguwp1jN",
                "D5GHjiCbJx1eR69hHRGY6Gzc9HGTZF2LpzMuPxzDFvqd9PdWGWsv4oBLGUggAHDH")
symbol = "ETHUSDT"

headers = {
    'X-MBX-APIKEY': "Tr80L4Fnm2g4m8gnI3YlrCGR0XhlW9shMmVw01IYrE6Kjrd5WRdisaFIGguwp1jN"
}
#%%

def test():
  price = float(client.get_symbol_ticker(symbol=symbol)['price'])
  r = requests.post("https://fapi.binance.com/fapi/v1/order", params={
    "symbol": symbol,
    "side": "BUY",
    "positionSide": "SHORT",
    "type": enums.FUTURE_ORDER_TYPE_STOP,
    "timeInForce": enums.TIME_IN_FORCE_GTC,
    "stopPrice": (price - 0.006 * price),
    "quantity": 0.001,
    "reduceOnly": "true",
    "workingType": "MARK_PRICE",
    "timestamp": datetime.now().timestamp()
  }, headers=headers)
  print(r.json())
  # client.futures_create_order(
  #   symbol=symbol,
  #   side=enums.SIDE_SELL,
  #   positionSide="SHORT",
  #   type=enums.FUTURE_ORDER_TYPE_STOP_MARKET,
  #   timeInForce=enums.TIME_IN_FORCE_GTC,
  #   stopPrice=round((price - 0.006 * price), 2),
  #   quantity=0.002,
  # )
  # client.futures_create_order(
  #   symbol=symbol,
  #   side=enums.SIDE_SELL,
  #   positionSide="SHORT",
  #   type=enums.FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
  #   timeInForce=enums.TIME_IN_FORCE_GTC,
  #   stopPrice=round((price + 0.002 * price), 2),
  #   quantity=0.002,
  # )

test()

#%%
# client.futures_change_leverage(symbol=symbol, leverage=1)
# %%
