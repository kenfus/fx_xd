import fxcmpy
import pandas as pd
import plotly.express as px
import datetime as a
import numpy as np
from pylab import plt
from pandas.plotting import register_matplotlib_converters


con = fxcmpy.fxcmpy(config_file='fxcm.cfg', server='demo') # server = 'real' for live

instruments = con.get_instruments()
print(instruments)

start_dt = dt.datetime(2019, 12, 23)
stop_dt = dt.datetime(2019, 12, 24)

data = con.get_candles('EUR/GBP', period='m1', start = start_dt, stop = stop_dt)  # daily data

data['pandas_SMA_3'] = data["askclose"].rolling(window=3).mean()
data['pandas_SMA_50'] = data["askclose"].rolling(window=50).mean()


register_matplotlib_converters()

plt.style.use('seaborn')
plt.figure(figsize = (10,6))
plt.plot(data['askclose'])
plt.plot(data['pandas_SMA_3'])
plt.plot(data['pandas_SMA_50'])
plt.show

con.subscribe_market_data('EUR/CHF')
con.get_subscribed_symbols()
con.is_subscribed('EUR/CHF')

con.get_last_price('EUR/CHF')