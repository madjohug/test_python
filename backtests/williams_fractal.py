import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app
from pandas.core.frame import DataFrame
import ta
import numpy as np
from scipy.stats import linregress
from matplotlib import colors, pyplot, markers

def wilFractal(df):
  periods = (-2, -1, 1, 2)
  
  bear_fractal = pd.Series(np.logical_and.reduce([
      df['High'] > df['High'].shift(period) for period in periods
  ]), index=df.index)

  bull_fractal = pd.Series(np.logical_and.reduce([
      df['Low'] < df['Low'].shift(period) for period in periods
  ]), index=df.index)

  return bear_fractal, bull_fractal