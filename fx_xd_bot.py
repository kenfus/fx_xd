import fxcmpy
import datetime as dt
import backtrader as bt
import getpass

# Is Eric or Vincenzo using this script?
username = getpass.getuser().lower()

###
# Define Parameters here!
token_to_trade = 'EUR/CHF'
time_frame = 'D1'
start_dt = dt.datetime(2019, 1, 1)
stop_dt = dt.datetime(2019, 12, 31)
server_type = 'demo'  # server = 'real' for live
config_file_path = 'fxcm.cfg'
# Define the renaming and which columns to use for this test. Careful, the columns which are not defined or renamed here will be dropped!
renaming = {'bidopen': 'open', 'bidclose': 'close', 'bidhigh': 'high', 'bidlow': 'low', 'tickqty': 'volume'}
timeframe = bt.TimeFrame.Days
cash_amount = 10000
leverage = 50
order_size = 0.02 * cash_amount
commission = 0.001
###

### Connection to FXCM-server and import the config-file
con = fxcmpy.fxcmpy(config_file=config_file_path, server=server_type)
instruments = con.get_instruments()
data = con.get_candles(token_to_trade, period=time_frame, start=start_dt, stop=stop_dt)

con.close()


###

### Define Indicators and signals

class StratVincenzo(bt.Strategy):
    def __init__(self):
        self.atr = bt.ind.AverageTrueRange()
        self.laguerre = bt.ind.LaguerreFilter()
        self.laguerreRSI = bt.ind.LaguerreRSI()

    def next(self):
        if not self.position:  # not in the market
            if self.laguerreRSI > 0.85:
                if self.laguerre < self.data:
                    self.buy(size=order_size)  # enter long

        elif self.laguerreRSI < 0.5:  # in the market & cross to the downside
            self.close()  # close long position

class StratEric(bt.Strategy):
    def __init__(self):

        self.atr = bt.ind.AverageTrueRange(period=14)
        self.laguerre = bt.ind.LaguerreFilter(period=7)
        self.laguerreRSI = bt.ind.LaguerreRSI(period=7)

    def next(self):
        if not self.position:  # not in the market
            if self.laguerreRSI > 0.85:
                if self.laguerre < self.data:
                    self.buy(size=order_size)  # enter long

        elif self.position:
                if self.laguerreRSI < 0.5:  # in the market & cross to the downside
                    self.close()  # close long position

        elif not self.position:  # not in the market
            if self.laguerreRSI < 0.4:
                if self.laguerre > self.data:
                    self.sell(size=order_size)  # enter short
        elif self.position:
            if self.laguerreRSI > 0.5:  # in the market & cross to the downside
                self.close()  # close short position



### Helper Functions
columns_to_keep = []
for key, value in renaming.items():
    columns_to_keep.append(key)

def fxcm_df_to_bt_df(df):
    df = df[columns_to_keep].copy()
    df.rename(columns=renaming, inplace=True)
    return df


###

# Initialize Cerebro:
cerebro = bt.Cerebro()


# Add strategy to cerebro
cerebro.addstrategy(StratEric)

# Add strategy to cerebro. To avoid merge errors, it detectes which strategy to apply
if username.find('vinc') >= 0:
    cerebro.addstrategy(StratVincenzo)
    print('High IQ detected')

elif username.find('eric') >= 0:
    cerebro.addstrategy(StratEric)
    print('Applying strategy for IQ < 80')


# Transform data
dataframe = fxcm_df_to_bt_df(data, renaming)

# Transform and feed data to backtrader and set parameters for the broker
data_to_backtest = bt.feeds.PandasData(dataname=dataframe, timeframe=timeframe, openinterest=None)
cerebro.adddata(data_to_backtest)

# Set our desired cash start
cerebro.broker.setcash(cash_amount)

# Set the commission - 0.1% ... divide by 100 to remove the %
cerebro.broker.setcommission(commission=commission)
# Startingvalue
starting_value = cerebro.broker.getvalue()
print('Starting Portfolio Value: {}'.format(starting_value))

# Gogo gadget cerebro
cerebro.run()

# Value after applying strategy
end_value = cerebro.broker.getvalue()
end_value_leverage = starting_value + (end_value - starting_value) * leverage
print('Final Portfolio Value: {}'.format(end_value_leverage))

# Plot the results
cerebro.plot()
