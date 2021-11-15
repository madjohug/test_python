import flask
import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, app

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def getBTCMarket():

  with app.app_context():
    x = jsonify(Client().get_symbol_ticker(symbol="BTCUSDT"))
    x.headers.add("Access-Control-Allow-Origin", "*")

    return x

