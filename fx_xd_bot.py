import fxcmpy
import pandas as pd
import plotly.express as px
import datetime as dt
import numpy as np
from pylab import plt
from pandas.plotting import register_matplotlib_converters
import backtrader as bt
import backtrader.feeds as btfeeds


###
#Define Parameters here!
token_to_trade = 'EUR/GBP'
time_frame = 'D1'
start_dt = dt.datetime(2019, 1, 1)
stop_dt = dt.datetime(2019, 12, 24)
server_type = 'demo' # server = 'real' for live
config_file_path = 'fxcm.cfg'
renaming = {'bidopen': 'open', 'bidclose': 'close', 'bidhigh':'high', 'bidlow':'low', 'tickqty':'volume'}
timeframe = bt.TimeFrame.Minutes
###

### Connection to FXCM-server and import the config-file
con = fxcmpy.fxcmpy(config_file=config_file_path, server=server_type) 
instruments = con.get_instruments()
data = con.get_candles(token_to_trade, period = time_frame, start = start_dt, stop = stop_dt)
###

# Overview and check if data getting was succesful
register_matplotlib_converters()
plt.style.use('seaborn')
plt.figure(figsize = (10,6))
plt.plot(data['askclose'])
plt.show

### Define Indicators and signals
class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=2,  # period for the fast moving average
        pslow=4   # period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

    def next(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy()  # enter long

        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position
###
        
### Helper Functions:
def transform_data(df):
    return fxcm_df_to_bt_df(df, start_dt, stop_dt, token_to_trade, time_frame, renaming)

def fxcm_df_to_bt_df(df, start_dt, stop_dt, token_to_trade, time_frame, renaming):
    df.rename(columns = renaming, inplace = True)
    return df
###
    
# Initialize Cerebro:
cerebro = bt.Cerebro()

# Add strategy to cerebro
cerebro.addstrategy(SmaCross)

# Transform data
dataframe = transform_data(data)

# Transform and feed data to backtrader and set parameters for the broker
data_to_backtest = bt.feeds.PandasData(dataname=dataframe, timeframe=timeframe, openinterest=None)
cerebro.adddata(data_to_backtest)
# Set our desired cash start
cerebro.broker.setcash(100000.0)

# Set the commission - 0.1% ... divide by 100 to remove the %
cerebro.broker.setcommission(commission=0.001)
# Startingvalue
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Gogo gadget cerebro
cerebro.run()

# Value after applying strategy
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Plot the results
cerebro.plot(openinterest=None, volume = None)

con.close()