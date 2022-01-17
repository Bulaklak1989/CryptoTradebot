from this import d
from aiohttp import client
from binance import Client


import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna
from ta.volatility import BollingerBands
from ta.volatility import *
import ta

import numpy as np
import time

#######################################
#### PLACE YOUR API KEYS HERE##########
#######################################
api_key = '123124124124124'
api_secret = '124124124124124'

######################################

client = Client(api_key, api_secret)



def getminutedata(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines("CHZUSDT",Client.KLINE_INTERVAL_1MINUTE, "+1 Minute ago"))

    frame = frame.iloc[:,:6]
    frame.columns = ['Time','Open','High','Low','Close','Volume']
    frame = frame.set_index('Time')
    
    #Time stamp is a buggy mess come back to it
    #pd.to_datetime(1575262698000 / 1000, unit='s')
    #frame.index = pd.to_datetime(1575262698000 / 1000, unit='s')
    
    #pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame


df = getminutedata('CHZUSDT','1m','100')
  
    



#Technicals area#

def applytechnicals(df):
    df['%K'] = ta.momentum.stoch(df.High,df.Low,df.Close, window=14, smooth_window=3)
    df['%D'] = df['%K'].rolling(3).mean()
    df['rsi'] = ta.momentum.rsi(df.Close, window=14)
    df['macd'] = ta.trend.macd_diff(df.Close)
    
    df.dropna(inplace=True)

applytechnicals(df)


class Signals:

    def __init__(self,df, lags):
        self.df = df
        self.lags = lags
        
    def gettrigger(self):
        dfx = pd.DataFrame()
        for i in range(self.lags + 1):
            mask = (self.df['%K'].shift(i) < 20) & (self.df['%D'].shift(i) < 20)
            dfx = dfx.append(mask, ignore_index=True)
        return dfx.sum(axis=0)

    def decide(self):
        self.df['trigger'] = np.where(self.gettrigger(), 1, 0)
        self.df['Buy'] = np.where((self.df.trigger) &
    (self.df['%K'].between(20,80)) & (self.df['%D'].between(20,80))
    & (self.df.rsi > 50) & (self.df.macd > 0), 1, 0)

    
ins = Signals(df, 5)

ins.decide()

def strategy(pair, qty, open_position=False):
    df = getminutedata(pair, '1m', '100')
    applytechnicals(df)
    ins = Signals(df, 5)
    ins.decide()
    print(f'Current Close price is '+ str(df.Close.iloc[-1]))
    if df.Buy.iloc[-1]:
        order = client.create_order(symbol=pair, side='Buy', type='MARKET',quantity=qty)
        print(order)
        buyprice = (order['Fills'][0]['price'])
        open_position = True
    while open_position:
        time.sleep(0.5)
        df=getminutedata(pair,'1m','2')
        print(f'current close is' + str(df.Close.iloc[-1]))
        print(f'current target is' + str(buyprice * 1.005))
        print(f'Current stop is '+ str(buyprice * 0.995))

        if df.Close[-1] <= buyprice *0.995 or df.Close[-1] >= 1.005 * buyprice:
            order = client.create_order(symbol=pair, side='SELL', type='MARKET',quantity=qty)
        print(order)
        break

    while True:

        strategy('CHZUSDT', 500)
       #time.sleep(0.5)

    