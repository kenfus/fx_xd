import datetime as dt
import getpass
import os.path
import inspect
import fxcmpy
import pandas as pd

from custom_indicators import *

# Is Eric or Vincenzo using this script?
username = getpass.getuser().lower()

###
# Define Parameters here!
token_to_trade = 'GBP/CHF'
time_frame = 'D1'
start_dt = dt.datetime(2019, 1, 1)
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
              ('conf2_threshold', 0.3),
              ('period_entry', 12),
              ('period_exit', 12),
              ('period_baseline', 12),
              ('period_vol_ind', 12),
              ('period_conf2', 12),
              ('period_conf1', 7),
              # ('volume_ind', 'OBV'),
              ('vol_threshold', 50),
              ('entry_ind', 'SMA'),
              ('conf_ind', 'LRSI'),
              ('conf_ind2', 'VQZL_NORM'),
              ('exit_ind', 'SMA'),
              ('baseline_ind', 'SMA'),
              ('volume_ind', 'SMA'),
              )

    def __init__(self):
        self.startcash = self.broker.getvalue()
        self.threshold_long = self.params.threshold_long
        self.threshold_short = self.params.threshold_short
        self.vol_threshold = self.params.vol_threshold
        self.conf2_threshold = self.p.conf2_threshold
        self.baseline = getattr(bt.ind, self.params.baseline_ind)(period=self.params.period_baseline)
        self.conf_ind = getattr(bt.ind, self.params.conf_ind)(period=self.params.period_conf1)
        self.conf2_ind = getattr(bt.ind, self.params.conf_ind2)(period=self.params.period_conf2)
        # self.volume_ind = getattr(bt.ind, self.params.volume_ind)()
        self.exit_ind = getattr(bt.ind, self.params.exit_ind)(period=self.params.period_exit)

    def next(self):
        if not self.position:  # not in the market
            if self.conf_ind > self.threshold_long:
                if self.baseline < self.data.close:
                    if self.exit_ind > 0:
                        self.buy(size=order_size)  # enter long
        elif self.conf_ind < 0.3:  # in the market & cross to the downside
            self.close()  # close long position


### Define Indicators and signals

class StratVincenzo(bt.Strategy):
    params = (('threshold_long', 0.6),
              ('threshold_short', 0.3),
              ('period', 12),)

    def __init__(self):
        self.startcash = self.broker.getvalue()
        self.threshold_long = self.params.threshold_long
        self.threshold_short = self.params.threshold_short
        self.laguerreRSI = bt.ind.LaguerreRSI()
        self.schaff_cycle = SchaffTrendCycle()
        self.macdh = bt.ind.MACDHisto()
        self.vqzl = VolatilityQualityZeroLine()
        self.kama = bt.ind.AdaptiveMovingAverage()
        self.atr = bt.ind.AverageTrueRange(period=14)

    def next(self):
        if not self.position:  # not in the market
            if self.laguerreRSI[0] > self.threshold_long:
                if self.kama < self.data.close:
                    if self.vqzl[0] < 0.5:
                        print(self.vqzl[0])
                        self.buy(size=order_size)  # enter long
        elif self.schaff_cycle > 0.5:  # in the market & cross to the downside
            self.close()  # close long position


### Helper Functions
columns_to_keep = []
for key, value in renaming.items():
    columns_to_keep.append(key)


def fxcm_df_to_bt_df(df):
    df = df[columns_to_keep].copy()
    df.rename(columns=renaming, inplace=True)
    return df


if __name__ == '__main__':
    # Initialize Cerebro:
    cerebro = bt.Cerebro(optreturn=False)

    # Add strategy to cerebro. To avoid merge errors, it detects which strategy to apply
    if username.find('vinc') >= 0:
        # cerebro.addstrategy(StratVincenzo)
        cerebro.optstrategy(trading_strategy, period_exit=range(10, 13), period_conf1=range(5, 8),
                            period_baseline=range(6, 13), conf2_threshold=0,
                            threshold_long=np.arange(0.3, 0.7, 0.1),
                            vol_threshold=1, exit_ind=['RelativeVigorIndexHisto'],
                            # threshold_short=np.arange(0.5, 0.8, 0.1),
                            entry_ind=['KAMA'], conf_ind=['LRSI'], conf_ind2=['VQZL_NORM'],
                            volume_ind=['OBV'], baseline_ind=['LaguerreFilter', 'EMA'])

        # cerebro.optstrategy(StratVincenzo, period=range(3, 7))
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
            conf_ind = strategy.params.conf_ind
            conf_ind2 = strategy.params.conf_ind2
            exit_ind = strategy.params.exit_ind
            baseline_ind = strategy.params.baseline_ind
            period_conf1 = strategy.params.period_conf1
            threshold_long = round(strategy.params.threshold_long, 2)
            conf2_threshold = round(strategy.params.conf2_threshold, 2)
            period_baseline = strategy.params.period_baseline
            final_results_list.append(
                [PnL, percent_PnL, conf_ind, conf_ind2, exit_ind, baseline_ind,
                 period_conf1, threshold_long, conf2_threshold, period_baseline])

    by_PnL = sorted(final_results_list, key=lambda x: x[1], reverse=True)

    # Print results
    print('Results: Ordered by Profit:')
    for result in by_PnL[:15]:
        print(
            'Final PnL: {}, Final PnL-%: {}, Conf Indicator: {}, Conf2 Indicator: {}, Exit indicator: {}, Baseline indicator: {}'
            ', Period Conf 1: {}, Threshold Long: {}, Period Conf 2 : {} , Baseline Indicator Period: {}'.format(
                result[0], result[1],
                result[2], result[3],
                result[4], result[5],
                result[6], result[7],
                result[8], result[9]))
