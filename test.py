#%%

import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app
from pandas.core.frame import DataFrame
import ta
import numpy as np
from scipy.stats import linregress
from matplotlib import colors, pyplot, markers
import pyodbc


# %%
