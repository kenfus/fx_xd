import fxcmpy
import datetime as dt
import backtrader as bt
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt

#
###
#Define Parameters here!
token_to_trade = 'EUR/GBP'
time_frame = 'D1'
start_dt = dt.datetime(2019, 1, 1)
stop_dt = dt.datetime(2019, 12, 31)
server_type = 'demo' # server = 'real' for live
config_file_path = 'fxcm.cfg'
renaming = {'bidopen': 'open', 'bidclose': 'close', 'bidhigh':'high', 'bidlow':'low', 'tickqty':'volume'}
timeframe = bt.TimeFrame.Minutes
cash_amount = 1000
leverage = 50
cash_trading = cash_amount
order_size = 0.02*cash_trading
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
                self.buy(size = order_size) # enter long


        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position
            

###
class Strat1(bt.Strategy):
  # list of parameters which are configurable for the strategy
  params = dict(
      pfast=20,  # period for the fast moving average
      pslow=30   # period for the slow moving average
  )

  def __init__(self):
      sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
      sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
      self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal
      self.atr = bt.ind.AverageTrueRange(period = 14)
      self.williamsr = bt.ind.WilliamsR(period = 14, upperband = -20, lowerband = -80)
      self.momentum = bt.ind.Momentum(period = 12)
      self.laguerre = bt.ind.LaguerreFilter(period = 1)

  def next(self):
      if not self.position:  # not in the market
            if self.williamsr < -30:  # if fast crosses slow to the upside
                if self.momentum > 0:
                    self.buy(size = order_size) # enter long

      elif self.momentum < -0.03:  # in the market & cross to the downside
          self.close()  # close long position      
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
cerebro.addstrategy(Strat1)

# Transform data
dataframe = transform_data(data)

# Transform and feed data to backtrader and set parameters for the broker
data_to_backtest = bt.feeds.PandasData(dataname=dataframe, timeframe=timeframe, openinterest=None)
cerebro.adddata(data_to_backtest)

# Set our desired cash start
cerebro.broker.setcash(cash_amount)

# Set the commission - 0.1% ... divide by 100 to remove the %
cerebro.broker.setcommission(commission=0.001)
# Startingvalue
starting_value = cerebro.broker.getvalue()
print('Starting Portfolio Value: %.2f' % starting_value)

# Gogo gadget cerebro
cerebro.run()

# Value after applying strategy
end_value = cerebro.broker.getvalue()
end_value_leverage = starting_value + (end_value - starting_value) * leverage
print('Final Portfolio Value: %.2f' % end_value_leverage)

# Plot the results
cerebro.plot(openinterest = None, volume = None)
