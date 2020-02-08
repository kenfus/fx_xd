import datetime as dt
import getpass
import os.path

import backtrader as bt
import fxcmpy
import numpy as np
import pandas as pd

# Is Eric or Vincenzo using this script?
username = getpass.getuser().lower()

###
# Define Parameters here!
token_to_trade = 'GBP/CHF'
time_frame = 'D1'
start_dt = dt.datetime(2017, 7, 1)
stop_dt = dt.datetime(2020, 2, 3)
server_type = 'demo'  # server = 'real' for live
config_file_path = 'fxcm.cfg'
# Define the renaming and which columns to use for this test. Careful, the columns which are not defined or renamed here will be dropped!
renaming = {'bidopen': 'open', 'bidclose': 'close', 'bidhigh': 'high', 'bidlow': 'low', 'tickqty': 'volume'}
timeframe = bt.TimeFrame.Days
startcash = 10000
leverage = 50
order_size = 0.2 * startcash
commission = 0.001
# Create File-Name for Forex-Data
path_to_data_folder = 'data/'
token_to_trade_no_slash = token_to_trade.replace('/', '')
file_name = token_to_trade_no_slash + '_' + time_frame + '_' + start_dt.strftime("%Y%m%d") + '_to_' + stop_dt.strftime(
    "%Y%m%d")
path_to_data = 'data/' + file_name + '.csv'
###

### Connection to FXCM-server and import the config-file but only if we don't have the requested data available
if os.path.isfile(path_to_data):
    data = pd.read_csv(path_to_data, index_col='date')
    # Converting the index as date
    data.index = pd.to_datetime(data.index)
else:
    # Connect to fxcm server and get data and save the data locally.
    con = fxcmpy.fxcmpy(config_file=config_file_path, server=server_type)
    instruments = con.get_instruments()
    data = con.get_candles(token_to_trade, period=time_frame, start=start_dt, stop=stop_dt)
    con.close()
    data.to_csv(path_to_data)


### Function which creates a class
class trading_strategy(bt.Strategy):
    params = (('threshold_long', 0.5),
              ('threshold_short', 0.5),
              ('period', 12),
              ('entry_ind', 'SMA'),
              ('conf_ind', 'SMA'),
              ('exit_ind', 'SMA'),
              ('baseline_ind', 'SMA'),
              )

    def __init__(self):
        self.startcash = self.broker.getvalue()
        self.threshold_long = self.params.threshold_long
        self.threshold_short = self.params.threshold_short
        self.baseline = getattr(bt.ind, self.params.baseline_ind)(period=self.params.period)
        self.conf_ind = getattr(bt.ind, self.params.conf_ind)(period=self.params.period)
        self.exit_ind = getattr(bt.ind, self.params.entry_ind)(period=self.params.period)

    def next(self):
        if not self.position:  # not in the market
            if self.conf_ind < self.data.close:
                if self.baseline < self.data.close:
                    self.buy(size=order_size)  # enter long
        elif self.exit_ind > self.data.close:  # in the market & cross to the downside
            self.close()  # close long position


### Define Indicators and signals

class StratVincenzo(bt.Strategy):
    params = (('threshold_long', None),
              ('threshold_short', None),
              ('period', 12),)

    def __init__(self):
        self.startcash = self.broker.getvalue()
        self.threshold_long = self.params.threshold_long
        self.threshold_short = self.params.threshold_short
        self.laguerreRSI = bt.ind.LaguerreRSI()
        self.atr = bt.ind.AverageTrueRange(period=14)

    def next(self):
        if not self.position:  # not in the market
            if self.laguerreRSI[0] > self.threshold_long:
                if self.kama < self.data.close:
                    self.buy(size=order_size)  # enter long
        elif self.laguerreRSI[0] < self.threshold_short:  # in the market & cross to the downside
            self.close()  # close long position


class StratEric(bt.Strategy):
    def __init__(self):
        # Define indicators
        self.atr = bt.ind.AverageTrueRange()
        self.laguerre = bt.ind.LaguerreFilter()
        self.laguerreRSI = bt.ind.LaguerreRSI()
        self.accdescos = bt.ind.AccelerationDecelerationOscillator()
        self.entry_price = None

    def next(self):
        # long entry
        if not self.position:  # not in the market
            if self.laguerreRSI > 0.0:
                if self.laguerre < self.data:
                    self.buy(size=order_size)  # enter long
                    self.entry_price = self.data

        # short entry
        elif not self.position:  # not in the market
            if self.laguerre < self.data:
                self.sell(size=order_size)  # enter short
                self.entry_price = self.data

        # money management
        stop_atr = 1.5 * self.atr
        entry_price = 10
        break_even = False
        # define break even stop loss
        if self.position:
            if self.data >= entry_price + stop_atr:
                break_even = True

            elif self.data <= entry_price - stop_atr and not break_even:
                self.close()

            elif self.data <= entry_price and break_even:
                self.close()

        # long exit
        elif self.position:
            if self.laguerreRSI < 0.5:  # in the market & cross to the downside
                self.close()  # close long position
                break_even = False

        # short exit
        elif self.position:
            if self.laguerre > self.data:  # in the market & cross to the downside
                self.close()  # close short position
                break_even = False


### Helper Functions
columns_to_keep = []
for key, value in renaming.items():
    columns_to_keep.append(key)


def fxcm_df_to_bt_df(df):
    df = df[columns_to_keep].copy()
    df.rename(columns=renaming, inplace=True)
    return df


# Initialize Cerebro:
cerebro = bt.Cerebro(optreturn=False)

# Add strategy to cerebro. To avoid merge errors, it detects which strategy to apply
if username.find('vinc') >= 0:
    # cerebro.addstrategy(StratVincenzo, long_threshold=0.85)
    cerebro.optstrategy(trading_strategy, period=range(3, 7), threshold_long=0.1,
                        threshold_short=0.2, exit_ind=['SMA', 'EMA'], entry_ind=['SMA', 'EMA'],
                        conf_ind=['SMA', 'EMA'], baseline_ind=['SMA', 'EMA'])
    print('High IQ detected')

elif username.find('eric') >= 0:
    cerebro.addstrategy(StratEric)
    print('Applying strategy for IQ < 80')

# Transform data
dataframe = fxcm_df_to_bt_df(data)

# Transform and feed data to backtrader and set parameters for the broker
data_to_backtest = bt.feeds.PandasData(dataname=dataframe, timeframe=timeframe, openinterest=None)
cerebro.adddata(data_to_backtest)

# Set our desired cash start
cerebro.broker.setcash(startcash)

# Set the commission
cerebro.broker.setcommission(commission=commission)

# Run over everything
opt_runs = cerebro.run()
final_results_list = []

# run in opt_run
for run in opt_runs:
    for strategy in run:
        value = round(strategy.broker.get_value(), 2)
        PnL = round(value - startcash, 2)
        percent_PnL = round(PnL / order_size * 100, 2)
        period = strategy.params.period
        threshold_long = round(strategy.params.threshold_long, 2)
        threshold_short = round(strategy.params.threshold_short, 2)
        exit_ind = strategy.params.exit_ind
        entry_ind = strategy.params.entry_ind
        conf_ind = strategy.params.conf_ind
        baseline_ind = strategy.params.baseline_ind
        final_results_list.append(
            [period, threshold_long, threshold_short, PnL, percent_PnL, exit_ind, entry_ind, conf_ind, baseline_ind])

by_PnL = sorted(final_results_list, key=lambda x: x[3], reverse=True)

# Print results
print('Results: Ordered by Profit:')
for result in by_PnL[:30]:
    print(
        'MA Period: {}, lRSI-threshold long: {}. lRSI-threshold short: {}, '
        'Final PnL: {}, Final PnL-%: {}, Exit Indicator: {}, Entry Indicator: {}, Confirmation indicator: {}, Baseline indicator: {}'.format(
            result[0], result[1],
            result[2], result[3],
            result[4], result[5],
            result[6], result[7],
            result[8]))
