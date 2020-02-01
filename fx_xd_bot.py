import fxcmpy
import pandas as pd
import plotly.express as px
import datetime as dt
import numpy as np
from pylab import plt
from pandas.plotting import register_matplotlib_converters
import backtrader as bt
import backtrader.feeds as btfeeds
<<<<<<< HEAD
=======
from fx_xd_helper_functions import fxcm_df_to_bt_df
>>>>>>> 0c94befd74a7fd7fbf00b2913f73ff658808482f



###
#Define Parameters here!
token_to_trade = 'EUR/GBP'
time_frame = 'D1'
start_dt = dt.datetime(2019, 1, 1)
stop_dt = dt.datetime(2019, 12, 24)
server_type = 'demo' # server = 'real' for live
config_file_path = 'fxcm.cfg'
renaming = {'bidopen': 'open', 'bidclose': 'close', 'bidhigh':'high','bidlow':'low', 'tickqty':'volume'}
###

### Connection to FXCM-server and import the config-file
con = fxcmpy.fxcmpy(config_file=config_file_path, server=server_type) 
instruments = con.get_instruments()
data = con.get_candles(token_to_trade, period = time_frame, start = start_dt, stop = stop_dt)  # daily data
###

# Overview and check if data getting was succesful
register_matplotlib_converters()
plt.style.use('seaborn')
plt.figure(figsize = (10,6))
plt.plot(data['askclose'])
plt.show

### Define Indicators and signals
class SmaCross(bt.SignalStrategy):
    def __init__(self):
        sma1, sma2 = bt.ind.SMA(period=10), bt.ind.SMA(period=30)
        self.lines.signal = sma1 - sma2
###
<<<<<<< HEAD
'''
### Start the backtest
=======

### Helper Functions:
def transform_data(df):
    return fxcm_df_to_bt_df(df, start_dt, stop_dt, token_to_trade, time_frame, renaming)
###
# Initialize Cerebro:
>>>>>>> 0c94befd74a7fd7fbf00b2913f73ff658808482f
cerebro = bt.Cerebro()

# Add strategy to cerebro
cerebro.addstrategy(SmaCross)

# Transform data
dataframe = transform_data(data)

# Transform and feed data to backtrader
data_to_backtest = bt.feeds.PandasData(dataname=dataframe)
cerebro.adddata(data_to_backtest)
# Gogo gadget cerebro
cerebro.run()
cerebro.plot()

con.close()