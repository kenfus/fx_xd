import fxcmpy
import datetime as dt
import backtrader as bt
import getpass
import numpy as np
import pandas as pd
import os.path


###
# Define Parameters here!
token_to_trade = 'GBP/CHF' # 'AUD/NZD'
time_frame = 'D1'
start_dt = dt.datetime(2019, 1, 1)
stop_dt = dt.datetime(2019, 12, 31)
server_type = 'demo'  # server = 'real' for live
config_file_path = 'fxcm.cfg'
# Define the renaming and which columns to use for this test. Careful, the columns which are not defined or renamed here will be dropped!
renaming = {'bidopen': 'open', 'bidclose': 'close', 'bidhigh': 'high', 'bidlow': 'low', 'tickqty': 'volume'}
timeframe = bt.TimeFrame.Days
startcash = 1000
leverage = 50
# order_size = 0.2 * startcash
commission = 0.001
atr_stop_loss = 1.5
atr_take_profit_1 = 2 * atr_stop_loss
atr_take_profit_2 = 4 * atr_stop_loss
atr_take_profit_3 = 6 * atr_stop_loss
aroon_period = 4
percentage_to_trade = 0.02

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
        self.laguerreRSI = bt.ind.LaguerreRSI(plot = False)
        self.accdescos = bt.ind.AccelerationDecelerationOscillator(plot = False)
        self.aroon_down = bt.ind.AroonDown(period = aroon_period,plot = False)
        self.aroon_up = bt.ind.AroonUp(period = aroon_period,plot = False)
        self.cross_over = bt.ind.CrossOver(self.data, self.laguerre, plot = False)
        self.cross_over_aroon = bt.ind.CrossOver(self.aroon_up, self.aroon_down, plot = False)
        self.rsi = bt.ind.RelativeStrengthIndex()
        self.rsi_long = bt.ind.CrossOver(self.rsi, 30,plot = False)
        self.rsi_short = bt.ind.CrossOver(self.rsi, 70,plot = False)
        self.rmi = bt.ind.RelativeMomentumIndex(plot = False) # volume indicator
        self.aroon = bt.ind.AroonUpDown()

        # define variables for money management
        self.break_even = False
        self.take_profit_1 = False # Take Profit level 1
        self.take_profit_2 = False  # Take Profit level 2
        self.take_profit_3 = False  # Take Profit level 3
        self.is_long = False
        self.is_short = False

    def next(self):
        # use percentage of current cash amount for trading
        order_size = percentage_to_trade * self.broker.getvalue()
        self.current_price = self.data[0]
        # long entry
        if not self.position and not self.is_long and not self.is_short:  # not in the market
            if self.rmi > 50:# and self.accdescos > 0:
                if self.cross_over == 1: #self.rsi_long == 1
                    self.buy(size=order_size)  # enter long
                    self.entry_price = self.data[0]
                    self.stop_atr_long = self.entry_price - atr_stop_loss * self.atr
                    self.is_long = True
                    print("Entering long")
                    print(self.data[0])
                    print("Stop loss long: ", self.stop_atr_long)

        # short entry
        if not self.position and not self.is_long and not self.is_short:  # not in the market
            if self.rmi > 50:# and self.accdescos > 0:
                if self.cross_over == -1: #self.rsi_short: == -1
                    self.sell(size=order_size)  # enter short
                    self.entry_price = self.data[0]
                    self.stop_atr_short = self.entry_price + atr_stop_loss * self.atr
                    self.is_short = True
                    print("Entering short")
                    print(self.data[0])
                    print("Stop loss short: ", self.stop_atr_short)


        # long exit
        if self.position.size > 0:
            if self.cross_over_aroon == 1:  # in the market & cross to the downside
                self.close()  # close long position
                self.is_long = False
                print("Exiting long")
                print(self.data[0])

        # short exit
        if self.position.size < 0:
            if self.cross_over_aroon == -1:  # in the market & cross to the upside
                self.close()  # close short position
                self.is_short = False
                print("Exiting short")
                print(self.data[0])

        # define stop loss and take profit 1, 2 and 3
        #stop loss long
        if self.is_long:
            if self.data <= self.stop_atr_long:
                self.close()
                self.is_long = False
                print("Long stop loss hit", self.data[0])

        # stop loss short
        if self.is_short:
            if self.data >= self.stop_atr_short:
                self.close()
                self.is_short = False
                print("Short stop loss hit", self.data[0])

        # take profit 1 long
        if self.is_long and self.entry_price + atr_take_profit_1 and not self.take_profit_1:
            self.sell(size=order_size / 4)
            self.take_profit_1 = True
            self.stop_atr_long = self.data[0]
            print("Profit long 1")
        # take profit 2 long
        if self.is_long and self.entry_price + atr_take_profit_2 and not self.take_profit_1 and not self.take_profit_2:
            self.sell(size=order_size / 4)
            self.take_profit_2 = True
            self.stop_atr_long = self.data[0]
            print("Profit long 2")
        # take profit 3 long
        if self.is_long and self.entry_price + atr_take_profit_3 and not self.take_profit_1 and not self.take_profit_2 and not self.take_profit_3:
            self.sell(size=order_size / 4)
            self.take_profit_3 = True
            self.stop_atr_long = self.data[0]
            print("Profit long 3")

        # take profit 1 short
        if self.is_short and self.entry_price - atr_take_profit_1 and not self.take_profit_1:
            self.sell(size=order_size / 4)
            self.take_profit_1 = True
            self.stop_atr_short = self.data[0]
            print("Profit short 1")
        # take profit 2 short
        if self.is_short and self.entry_price - atr_take_profit_2 and not self.take_profit_1 and not self.take_profit_2:
            self.sell(size=order_size / 4)
            self.take_profit_1 = True
            self.stop_atr_short = self.data[0]
            print("Profit short 2")
        # take profit 3 short
        if self.is_short and self.entry_price - atr_take_profit_3 and not self.take_profit_1 and not self.take_profit_2 and not self.take_profit_3:
            self.sell(size=order_size / 4)
            self.take_profit_1 = True
            self.stop_atr_short = self.data[0]
            print("Profit short 3")

            def next(self):
                # use percentage of current cash amount for trading
                order_size = percentage_to_trade * self.broker.getvalue()
                self.current_price = self.data[0]
                # long entry
                if not self.position and not self.is_long and not self.is_short:  # not in the market
                    if self.rmi > 50:  # and self.accdescos > 0:
                        if self.cross_over == 1:  # self.rsi_long == 1
                            self.buy(size=order_size)  # enter long
                            self.entry_price = self.data[0]
                            self.stop_atr_long = self.entry_price - atr_stop_loss * self.atr
                            self.is_long = True
                            print("Entering long")
                            print(self.data[0])
                            print("Stop loss long: ", self.stop_atr_long)

                # short entry
                if not self.position and not self.is_long and not self.is_short:  # not in the market
                    if self.rmi > 50:  # and self.accdescos > 0:
                        if self.cross_over == -1:  # self.rsi_short: == -1
                            self.sell(size=order_size)  # enter short
                            self.entry_price = self.data[0]
                            self.stop_atr_short = self.entry_price + atr_stop_loss * self.atr
                            self.is_short = True
                            print("Entering short")
                            print(self.data[0])
                            print("Stop loss short: ", self.stop_atr_short)

                # long exit
                if self.position.size > 0:
                    if self.cross_over_aroon == 1:  # in the market & cross to the downside
                        self.close()  # close long position
                        self.is_long = False
                        print("Exiting long")
                        print(self.data[0])

                # short exit
                if self.position.size < 0:
                    if self.cross_over_aroon == -1:  # in the market & cross to the upside
                        self.close()  # close short position
                        self.is_short = False
                        print("Exiting short")
                        print(self.data[0])

                # define stop loss and take profit 1, 2 and 3
                # stop loss long
                if self.is_long:
                    if self.data <= self.stop_atr_long:
                        self.close()
                        self.is_long = False
                        print("Long stop loss hit", self.data[0])

                # stop loss short
                if self.is_short:
                    if self.data >= self.stop_atr_short:
                        self.close()
                        self.is_short = False
                        print("Short stop loss hit", self.data[0])

                # take profit 1 long
                if self.is_long and self.entry_price + atr_take_profit_1 and not self.take_profit_1:
                    self.sell(size=order_size / 4)
                    self.take_profit_1 = True
                    self.stop_atr_long = self.data[0]
                    print("Profit long 1")
                # take profit 2 long
                if self.is_long and self.entry_price + atr_take_profit_2 and not self.take_profit_1 and not self.take_profit_2:
                    self.sell(size=order_size / 4)
                    self.take_profit_2 = True
                    self.stop_atr_long = self.data[0]
                    print("Profit long 2")
                # take profit 3 long
                if self.is_long and self.entry_price + atr_take_profit_3 and not self.take_profit_1 and not self.take_profit_2 and not self.take_profit_3:
                    self.sell(size=order_size / 4)
                    self.take_profit_3 = True
                    self.stop_atr_long = self.data[0]
                    print("Profit long 3")

                # take profit 1 short
                if self.is_short and self.entry_price - atr_take_profit_1 and not self.take_profit_1:
                    self.sell(size=order_size / 4)
                    self.take_profit_1 = True
                    self.stop_atr_short = self.data[0]
                    print("Profit short 1")
                # take profit 2 short
                if self.is_short and self.entry_price - atr_take_profit_2 and not self.take_profit_1 and not self.take_profit_2:
                    self.sell(size=order_size / 4)
                    self.take_profit_1 = True
                    self.stop_atr_short = self.data[0]
                    print("Profit short 2")
                # take profit 3 short
                if self.is_short and self.entry_price - atr_take_profit_3 and not self.take_profit_1 and not self.take_profit_2 and not self.take_profit_3:
                    self.sell(size=order_size / 4)
                    self.take_profit_1 = True
                    self.stop_atr_short = self.data[0]
                    print("Profit short 3")


### Helper Functions
columns_to_keep = []
for key, value in renaming.items():
    columns_to_keep.append(key)

def fxcm_df_to_bt_df(df):
    df = df[columns_to_keep].copy()
    df.rename(columns=renaming, inplace=True)
    return df


# Initialize Cerebro:
cerebro = bt.Cerebro(optreturn=False, cheat_on_open=True)

# Add strategy to cerebro. To avoid merge errors, it detects which strategy to apply


cerebro.addstrategy(StratEric)

#optimize strategy
#cerebro.optstrategy(StratEric, aroon_period=range(2, 14))

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
print("percent profit with leverage: ", round(earnings / starting_cash * 100, 2), "%")
print("Per Month: ", earnings / 12)
print("Per Week: ", earnings / 52)
print("Per Day: ", earnings / 365)
cerebro.plot(style='candlestick', barup='green', bardown='red')
