import fxcmpy
import datetime as dt
import backtrader as bt
import getpass
import numpy as np
import pandas as pd
import os.path

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


### Define Indicators and signals

class StratVincenzo(bt.Strategy):
    params = (('threshold_long', None),
              ('threshold_short', None),
              ('period', 12),)

    def __init__(self):
        self.startcash = self.broker.getvalue()
        self.threshold_long = self.params.threshold_long
        self.threshold_short = self.params.threshold_short
        self.kama = bt.ind.MovingAverageSimple(self.datas[0], period=self.params.period)
        self.laguerreRSI = bt.ind.LaguerreRSI()
        self.atr = bt.ind.AverageTrueRange(period = 14)

    def next(self):
        if not self.position:  # not in the market
            if self.laguerreRSI[0] > self.threshold_long:
                if self.kama[0] < self.data.close[0]:
                    self.buy(size=order_size)  # enter long
        elif self.laguerreRSI[0] < self.threshold_short:  # in the market & cross to the downside
            self.close()  # close long position

    # def stop(self):
    #     pnl = round(self.broker.getvalue() - self.startcash, 2)
    #     print('Laguerre Filter Period: {}, lRSI-threshold: {}. Final PnL: {}'.format(
    #         self.params.period, self.params.threshold_long, pnl))


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
    cerebro.optstrategy(StratVincenzo, period=range(3, 18), threshold_long=np.arange(0.2, 0.8, 0.05),
                        threshold_short=np.arange(0.1, 0.7, 0.05))
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
    print(run)
    for strategy in run:
        value = round(strategy.broker.get_value(), 2)
        PnL = round(value - startcash, 2)
        percent_PnL = round(PnL/order_size*100, 2)
        period = strategy.params.period
        threshold_long = round(strategy.params.threshold_long, 2)
        threshold_short = round(strategy.params.threshold_short, 2)
        final_results_list.append([period, threshold_long, threshold_short, PnL, percent_PnL])

by_PnL = sorted(final_results_list, key=lambda x: x[3], reverse=True)

# Print results
print('Results: Ordered by Profit:')
for result in by_PnL[:5]:
    print(
        'Kama Period: {}, lRSI-threshold long: {}. lRSI-threshold short: {}, '
        'Final PnL: {}, Final PnL-%: {}'.format(result[0], result[1], result[2], result[3], result[4]))

