from binance import exceptions, Client
import json
import pandas as pd

client = Client("Tr80L4Fnm2g4m8gnI3YlrCGR0XhlW9shMmVw01IYrE6Kjrd5WRdisaFIGguwp1jN",
                "D5GHjiCbJx1eR69hHRGY6Gzc9HGTZF2LpzMuPxzDFvqd9PdWGWsv4oBLGUggAHDH")

def test():
  e = client.futures_account_balance()
  df = pd.DataFrame(e, columns=["alias", "asset", "balance", "withdrawAvailable", "updatetime"])
  df = df[df["asset"] == "USDT"]
  value = df.iloc[0].balance
  return float(value) * 0.1

print(test())