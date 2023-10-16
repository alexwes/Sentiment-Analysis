from firebase_admin import firestore
from tradingview_ta import TA_Handler, Interval, Exchange
import requests
from datetime import datetime, timedelta
from firestore_handler import FirestoreHandler

import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import chart_studio.plotly as py


def add_indicators():
    fire = FirestoreHandler()
    tickers = ["ETHUSD", "BTCUSD", "ADAUSD", "UNIUSD","LINKUSD","DOTUSD"]
    names = ["ethereum", "bitcoin", "cardano", "uniswap", "chainlink", "polkadot"]

    for ticker,name in zip(tickers,names):
        handler = TA_Handler(
            symbol=ticker,
            exchange="binance",
            screener="crypto",
            interval="1d",
            timeout=None)

        analysis = handler.get_analysis()
        indicators = {}
        indicators['RSI'] = analysis.indicators["RSI"]
        indicators['close'] = analysis.indicators["close"]
        indicators['macd.hist'] = analysis.indicators["MACD.macd"]-analysis.indicators["MACD.signal"]
        indicators['50sma'] = analysis.indicators["SMA50"]
        indicators['200sma'] = analysis.indicators["SMA200"]
        indicators['20ema'] = analysis.indicators["EMA20"]
        indicators['stoch.k'] = analysis.indicators["Stoch.K"]
        indicators['stoch.d'] = analysis.indicators["Stoch.D"]
        indicators['volume'] = analysis.indicators['volume']

        fire.add_indicators(name, indicators)

def create_charts():
    
    fire = FirestoreHandler()
    today = datetime.now()
    last_week = today - timedelta(days=30)

    today_iso = today.strftime('%Y-%m-%d')
    last_week_iso = last_week.strftime('%Y-%m-%d')

    tickers = ["ETH-USD", "BTC-USD", "ADA-USD", "UNI-USD", "DOT-USD", "LINK-USD"]
    names = ["Ethereum", "Bitcoin", "Cardano", "Uniswap", "Polkadot", "Chainlink"]
    for ticker, name in zip(tickers,names):
        urls_dict = {}
        response = requests.get(f"https://api.pro.coinbase.com/products/{ticker}/candles/?start={last_week_iso}&end={today_iso}&granularity=86400")
        data = response.json()
        for i in reversed(range(0,31)):
            date = today - timedelta(days=i)
            date_iso = date.strftime('%Y-%m-%d')
            data[i][0]=date_iso
        df = pd.DataFrame(data, columns=['date','low','high','open','close','volume'])

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Candlestick(x=df['date'],
                                            open=df['open'],
                                            high=df['high'],
                                            low=df['low'],
                                            close=df['close'], 
                                            name="Price"
                                            ), secondary_y = False)
        sent_list = fire.get_daily_sent(name.lower())
        fig.add_trace(go.Scatter(x=df['date'], 
                                    y=sent_list, 
                                    name="Sentiment",line=dict(color="#040408")), 
                                    secondary_y = True)
        fig.update_layout(title = f"{name} Price vs Daily Sentiment")
        url = py.plot(fig, filename=f'{name}-chart', auto_open=False)
        url = url[:-1]+".embed?showlink=false"

        urls_dict['Price'] = url

        vol_list = fire.get_daily_vol(name.lower())
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df['date'], 
                                    y=df['volume'], 
                                    name = "Trade Volume"),
                                    secondary_y=False)

        fig2.add_trace(go.Scatter(x=df['date'], 
                                    y=vol_list, 
                                    name="Tweet Volume",line=dict(color="#040408")), 
                                    secondary_y = True)
        fig2.update_layout(title = f"{name} Trade Volume vs Tweet Volume")

        url = py.plot(fig2, filename=f'{name}-vol-chart', auto_open=False)
        url = url[:-1]+".embed?showlink=false"
        urls_dict['Volume'] = url
        # fire.set_graph_urls(name.lower(),urls_dict)

def predictive_function():
    fire = FirestoreHandler()

    tickers = ["ETH-USD", "BTC-USD", "ADA-USD", "UNI-USD", "DOT-USD", "LINK-USD"]
    names = ["Ethereum", "Bitcoin", "Cardano", "Uniswap", "Polkadot", "Chainlink"]
    for ticker, name in zip(tickers, names):
        indicators = fire.db.collection(f'tokens/{name.lower()}/indicators').order_by(u'timestamp', 
                        direction=firestore.Query.DESCENDING).limit(1).get()
        for i in indicators:
            print(i.to_dict())
        break
    


predictive_function()    