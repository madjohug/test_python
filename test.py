#%%
from inspect import getblock
from binance import  Client, enums, exceptions
import requests 
from time import time
import pandas as pd
import hmac
import hashlib
import codecs
import asyncio

apikey = "Tr80L4Fnm2g4m8gnI3YlrCGR0XhlW9shMmVw01IYrE6Kjrd5WRdisaFIGguwp1jN"
secret = "D5GHjiCbJx1eR69hHRGY6Gzc9HGTZF2LpzMuPxzDFvqd9PdWGWsv4oBLGUggAHDH"

client = Client(apikey, secret)

symbol = "ETHUSDT"

headers = {
    'X-MBX-APIKEY': apikey,
    "Content-Type": "application/x-www-form-urlencoded"
}
#%%

def getBalance():
  e = client.futures_account_balance()
  df = pd.DataFrame(e, columns=["alias", "asset", "balance", "withdrawAvailable", "updatetime"])
  df = df[df["asset"] == "USDT"]
  return df.iloc[0].balance

async def test():
  price = float(client.get_symbol_ticker(symbol=symbol)['price'])
  print("price : ", price)
  # totalParams = "symbol="+symbol+"&side=SELL&timestamp="+str(int(time()*1000))+"&positionSide=SHORT&type=STOP_LOSS&timeInForce=GTC&stopPrice="+str(round(float(price)-0.006*float(price), 2))+"&quantity="+str(0.001)+"&workingType=MARK_PRICE"
  # signature = hmac.new(codecs.encode(secret), codecs.encode(totalParams),hashlib.sha256).hexdigest()
  # print(signature)

  # data = {
  #   "symbol": symbol,
  #   "side": "SELL",
  #   "timestamp": int(time()*1000),
  #   "positionSide": "SHORT",
  #   "type": "STOP_LOSS",
  #   "timeInForce": "GTC",
  #   "stopPrice": round(float(price) - 0.006 * float(price), 2),
  #   "quantity": 0.001,
  #   "workingType": "MARK_PRICE",
  #   "signature": signature
  # }

  # r = requests.post("https://fapi.binance.com/fapi/v1/order", data=data, headers=headers)
  # print(r.json())
  try:

    # print(buy)

    # await asyncio.sleep(0.5)

    buyPrice = float(client.get_symbol_ticker(symbol=symbol)['price'])
    balance = float(getBalance())
    print(round((balance * 0.5) / buyPrice, 3))

    client.futures_create_order(
      symbol=symbol,
      side="SELL",
      positionSide="SHORT",
      type="MARKET",
      quantity=round((balance * 0.5) / buyPrice, 3)
    )

    # await asyncio.sleep(1)
    # stop = client.futures_create_order(
    #   newClientOrderId=symbol,
    #   symbol=symbol,
    #   side="BUY",
    #   positionSide="SHORT",
    #   type="STOP_MARKET",
    #   timeInForce="GTC",
    #   stopPrice=round((price + 0.006 * price), 2),
    #   closePosition="true"
    # )

    # await asyncio.sleep(1)
    # profit = client.futures_create_order(
    #   symbol=symbol,
    #   side="BUY",
    #   positionSide="SHORT",
    #   type="TAKE_PROFIT_MARKET",
    #   timeInForce="GTC",
    #   stopPrice=round((price - 0.002 * price), 2),
    #   quantity=0.002,
    #   closePosition="true"
    # )

  except exceptions.BinanceAPIException as e:
    client.futures_cancel_all_open_orders(symbol=symbol)
    print(e)
  except requests.exceptions.ConnectionError as e:
    client.futures_cancel_all_open_orders(symbol=symbol)
    print(e)



asyncio.run(test())

# %%
