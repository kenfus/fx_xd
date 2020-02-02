import fxcmpy
import datetime as dt
import backtrader as bt


#
###
#Define Parameters here!
token_to_trade = 'EUR/GBP'
time_frame = 'D1'
start_dt = dt.datetime(2017, 1, 1)
stop_dt = dt.datetime(2020, 1, 31)
server_type = 'demo' # server = 'real' for live
config_file_path = 'fxcm.cfg'
# Define the renaming and which columns to use for this test. Careful, the columns which are not defined or renamed here will be dropped!
renaming = {'bidopen': 'open', 'bidclose': 'close', 'bidhigh':'high', 'bidlow':'low', 'tickqty':'volume'}
timeframe = bt.TimeFrame.Days
cash_amount = 10000
leverage = 50
order_size = 0.2 * cash_amount
commission = 0.001
###

### Connection to FXCM-server and import the config-file
con = fxcmpy.fxcmpy(config_file=config_file_path, server=server_type) 
instruments = con.get_instruments()
data = con.get_candles(token_to_trade, period = time_frame, start = start_dt, stop = stop_dt)

con.close()
###

### Define Indicators and signals
class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=20,  # period for the fast moving average
        pslow=30   # period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

    def next(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.order = self.buy(size=order_size)


        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position
            

###
class Strat1(bt.Strategy):
  def __init__(self):
      self.atr = bt.ind.AverageTrueRange(period = 14)
      self.williamsr = bt.ind.WilliamsR(period = 7)
      self.laguerre = bt.ind.LaguerreFilter(period = 7)

  def next(self):
      if not self.position:  # not in the market
            if self.williamsr > -20: 
                if self.laguerre[0] < self.data[0]:
                    print(self.data[0], self.williamsr[0], self.laguerre[0])
                    self.buy(size = order_size) # enter long

      elif self.williamsr < -80:  # in the market & cross to the downside
          self.close()  # close long position  
          
### Helper Functions
columns_to_keep = []
for key, value in renaming.items():
    columns_to_keep.append(key)
    
def transform_data(df):
    return fxcm_df_to_bt_df(df, start_dt, stop_dt, token_to_trade, time_frame, renaming)

def fxcm_df_to_bt_df(df, start_dt, stop_dt, token_to_trade, time_frame, renaming):
    df = df[columns_to_keep].copy()
    df.rename(columns = renaming, inplace = True)
    return df
###

# Initialize Cerebro:
cerebro = bt.Cerebro()

# Add strategy to cerebro
cerebro.addstrategy(Strat1)

# Transform data
dataframe = transform_data(data)
print(dataframe.head())

# Transform and feed data to backtrader and set parameters for the broker
data_to_backtest = bt.feeds.PandasData(dataname=dataframe, timeframe=timeframe, openinterest = None)
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
result = cerebro.plot()
result
