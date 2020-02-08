import fxcmpy
import datetime as dt
import backtrader as bt
import getpass
import numpy as np
import pandas as pd
import os.path


###
# Define Parameters here!
token_to_trade = 'AUD/NZD'
time_frame = 'D1'
start_dt = dt.datetime(2019, 1, 1)
stop_dt = dt.datetime(2019, 12, 31)
server_type = 'demo'  # server = 'real' for live
config_file_path = 'fxcm.cfg'
# Define the renaming and which columns to use for this test. Careful, the columns which are not defined or renamed here will be dropped!
renaming = {'bidopen': 'open', 'bidclose': 'close', 'bidhigh': 'high', 'bidlow': 'low', 'tickqty': 'volume'}
timeframe = bt.TimeFrame.Days
startcash = 10000
leverage = 50
order_size = 0.2 * startcash
commission = 0.001
atr_stop_loss = 1
atr_take_profit_1 = atr_stop_loss + 0.3
atr_take_profit_2 = atr_stop_loss + 0.6
atr_take_profit_3 = atr_stop_loss + 0.9

# Create File-Name for Forex-Data
path_to_data_folder = 'data/'
token_to_trade_no_slash = token_to_trade.replace('/', '')
file_name = token_to_trade_no_slash + '_' + time_frame + '_' + start_dt.strftime("%Y%m%d") + '_to_' + stop_dt.strftime(
    "%Y%m%d")
path_to_data = 'data/' + file_name + '.csv'

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

class StratEric(bt.Strategy):
    def __init__(self):
        # Define indicators
        self.atr = bt.ind.AverageTrueRange(plot = False)
        self.laguerre = bt.ind.LaguerreFilter()
        self.laguerreRSI = bt.ind.LaguerreRSI()
        self.accdescos = bt.ind.AccelerationDecelerationOscillator()
        self.aroon_down = bt.ind.AroonDown(plot = False)
        self.aroon_up = bt.ind.AroonUp(plot = False)
        self.cross_over = bt.ind.CrossOver(self.data, self.laguerre, plot = False)
        self.cross_over_aroon = bt.ind.CrossOver(self.aroon_up, self.aroon_down, plot = False)
        self.rmi = bt.ind.RelativeMomentumIndex()
        self.aroon = bt.ind.AroonUpDown()

        # define variables for money management
        self.break_even = False
        self.tp_1 = False # Take Profit level 1
        self.tp_2 = False  # Take Profit level 2
        self.tp_3 = False  # Take Profit level 3
        self.is_long = False
        self.is_short = False
        #self.stop_atr = 1.5 * self.atr

    def next(self):
        # long entry
        if not self.position:  # not in the market
            if self.rmi > 50:# and self.accdescos > 0:
                if self.cross_over == 1:
                    self.buy(size=order_size)  # enter long
                    self.entry_price = self.data
                    self.stop_atr = atr_stop_loss * self.atr
                    print("Entering long")
                    print(self.data[0])
                    print("Stop loss long: ", self.entry_price + self.stop_atr)
                    self.tp_1 = False
                    self.tp_2 = False
                    self.tp_3 = False

        # short entry
        if not self.position:  # not in the market
            print("pos size lmao", self.position.size)
            if self.rmi > 50:# and self.accdescos > 0:
                if self.cross_over == -1:
                    self.sell(size=order_size)  # enter short
                    self.entry_price = self.data
                    self.stop_atr = atr_stop_loss * self.atr
                    print("Entering short")
                    print(self.data[0])
                    print("Stop loss short: ", self.entry_price - self.stop_atr)
                    self.tp_1 = False
                    self.tp_2 = False
                    self.tp_3 = False



        # long exit
        if self.position and self.position.size > 0:
            if self.cross_over_aroon == 1:  # in the market & cross to the downside
                self.close()  # close long position
                self.break_even = False
                print("Exiting long")
                print(self.data[0])
                self.tp_1 = False
                self.tp_2 = False
                self.tp_3 = False

        # short exit
        if self.position and self.position.size < 0:
            if self.cross_over_aroon == -1:  # in the market & cross to the upside
                self.close()  # close short position
                self.break_even = False
                print("Exiting short")
                print(self.data[0])
                print("pos size", self.position.size)
                self.tp_1 = False
                self.tp_2 = False
                self.tp_3 = False

        # define break even stop loss
        # stop loss for long
        if self.position and not self.break_even and self.position.size > 0:
            if self.data > self.entry_price + self.stop_atr:
                self.break_even = True
                print("Moving long stop loss to break even")
                print(self.data[0])

            elif self.data <= self.entry_price - self.stop_atr and not self.break_even:
                self.close()
                print("Long Stop loss hit")
                print(self.data[0])
                self.tp_1 = False
                self.tp_2 = False
                self.tp_3 = False

            elif self.data <= self.entry_price and self.break_even:
                self.close()
                print("Break even stop loss hit")
                print(self.data[0])
                self.tp_1 = False
                self.tp_2 = False
                self.tp_3 = False

        # stop loss for short
        if self.position and not self.break_even and self.position.size < 0:
            if self.data > self.entry_price - self.stop_atr:
                self.break_even = True
                print("Moving short stop loss to break even")
                print(self.data[0])

            elif self.data >= self.entry_price + self.stop_atr and not self.break_even:
                self.close()
                print("Short Stop loss hit")
                print(self.data[0])
                self.tp_1 = False
                self.tp_2 = False
                self.tp_3 = False

            elif self.data <= self.entry_price and self.break_even:
                self.close()
                print("Break even stop loss hit")
                print(self.data[0])
                self.tp_1 = False
                self.tp_2 = False
                self.tp_3 = False

        '''# take profit in 3 levels
        # long
        if self.position and self.position.size > 0:
            #level 1
            if self.data > self.entry_price + atr_take_profit_1 and not self.tp_1:
                self.sell(size=order_size / 4)
                self.tp_1 = True
                print("tp long 1")
            #level 2
            elif self.data > self.entry_price + atr_take_profit_2 and not self.tp_2:
                self.sell(size=order_size / 4)
                self.tp_2 = True
                print("tp long 2")
            #level 3
            elif self.data > self.entry_price + atr_take_profit_3 and not self.tp_3:
                self.sell(size=order_size / 4)
                self.tp_3 = True
                print("tp long 3")

        # short
        if self.position and self.position.size < 0:
            #level 1
            if self.data < self.entry_price + atr_take_profit_1 and not self.tp_1:
                self.buy(size=order_size / 4)
                self.tp_1 = True
                print("tp short 1")
            #level 2
            elif self.data < self.entry_price - atr_take_profit_2 and not self.tp_2:
                self.buy(size=order_size / 4)
                self.tp_2 = True
                print("tp short 2")
            #level 3
            elif self.data < self.entry_price - atr_take_profit_3 and not self.tp_3:
                self.buy(size=order_size / 4)
                self.tp_3 = True
                print("tp short 3")'''


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


cerebro.addstrategy(StratEric)

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
starting_cash = cerebro.broker.getvalue()
print("Cash before running: ", starting_cash)
cerebro.run()
earnings = (cerebro.broker.getvalue() - starting_cash) * leverage
print("Cash after running: ", cerebro.broker.getvalue())
print("Earnings with leverage: ", earnings)
print("Per Month: ", earnings / 12)
print("Per Week: ", earnings / 52)
print("Per Day: ", earnings / 365)
cerebro.plot() #style='candlestick', barup='green', bardown='red'
