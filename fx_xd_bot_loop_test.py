import datetime as dt
import getpass
import os.path
import inspect
import fxcmpy
import pandas as pd
import operator
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
path_to_indicators = 'indicators/'
baseline_indicators = pd.read_csv(path_to_indicators + 'baseline_indicators.csv')
conf_indicators = pd.read_csv(path_to_indicators + 'conf_indicators.csv')


###

### Concat IND-Name and parameter-names to avoid duplicate parameter-names

def concat_name_param(df):
    df['param1_name_org'] = df['param1_name']
    df['param2_name_org'] = df['param2_name']
    df['param3_name_org'] = df['param3_name']
    df['param1_name'] = df['param1_name'] + '_' + df['name']
    df['param2_name'] = df['param2_name'] + '_' + df['name']
    df['param3_name'] = df['param3_name'] + '_' + df['name']
    return df


base_ind_renamed = concat_name_param(baseline_indicators)
conf_ind_renamed = concat_name_param(conf_indicators)

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


### Function which creates a class and helper functions
def create_dict_of_placeholder_params_init(*args):
    params_names, params_values, params_names_with_none, params_values_with_none = [], [], [], []
    for arg in args:
        params_names_with_none.extend([arg['param1_name'], arg['param2_name'], arg['param3_name'], 'th_l', 'th_s'])
        params_values_with_none.extend([arg['param1_value'], arg['param2_value'], arg['param3_value'], 0, 0])

    [params_names.append(param_name) if not pd.isna(param_name) else None for param_name in params_names_with_none]
    [params_values.append(param_value) if not pd.isna(param_value) else None for param_value in params_values_with_none]
    return dict(zip(params_names, params_values))


def create_dict_of_params(*args):
    params_names, params_values, params_names_with_none, params_values_with_none = [], [], [], []
    for arg in args:
        params_names_with_none.extend([arg['param1_name'], arg['param2_name'], arg['param3_name']])
        params_values_with_none.extend([arg['param1_value'], arg['param2_value'], arg['param3_value']])

    [params_names.append(param_name) if not pd.isna(param_name) else None for param_name in params_names_with_none]
    [params_values.append(param_value) if not pd.isna(param_value) else None for param_value in params_values_with_none]
    return dict(zip(params_names, params_values))


def create_dict_of_placeholder_params(self, ind):
    params_org_names_with_none, params_names_with_none, params_org_names, params_names = [], [], [], []

    params_org_names_with_none.extend([ind['param1_name_org'], ind['param2_name_org'], ind['param3_name_org']])
    params_names_with_none.extend([ind['param1_name'], ind['param2_name'], ind['param3_name']])

    [params_org_names.append(param_name) if not pd.isna(param_name) else None for param_name in
     params_org_names_with_none]
    [params_names.append(getattr(self.p, param_name)) if not pd.isna(param_name) else None for param_name in
     params_names_with_none]
    return dict(zip(params_org_names, params_names))


def baseline_th_l(self, baseline):
    if not pd.isna(baseline['th_l']):
        return baseline['th_l']
    else:
        return self.close[0]


def conf_th_l(self, conf):
    if not pd.isna(conf['th_l']):
        return conf['th_l']
    else:
        return self.close[0]


def exec_(ind, logical, th):
    return exec("operator.le(ind, th)")


### Helper Functions
columns_to_keep = []
for key, value in renaming.items():
    columns_to_keep.append(key)


def fxcm_df_to_bt_df(df):
    df = df[columns_to_keep].copy()
    df.rename(columns=renaming, inplace=True)
    return df


for index, baseline in base_ind_renamed.iterrows():
    for index, conf1 in conf_ind_renamed.iterrows():
        for index, conf2 in conf_ind_renamed.iterrows():
            if conf1['name'] == conf2['name']:
                continue
            if __name__ == '__main__':
                # Initialize Cerebro:
                cerebro = bt.Cerebro(optreturn=False)


                # Add strategy to cerebro. To avoid merge errors, it detects which strategy to apply
                class StrategyClass(bt.Strategy):
                    params = create_dict_of_placeholder_params_init(baseline, conf1, conf2)
                    print(params)

                    def __init__(self):
                        self.startcash = self.broker.getvalue()
                        self.conf1 = getattr(bt.ind, conf1['name'])(self.data,
                                                                    **create_dict_of_placeholder_params(self, conf1))
                        self.conf2 = getattr(bt.ind, conf2['name'])(self.data,
                                                                    **create_dict_of_placeholder_params(self, conf2))
                        self.baseline = getattr(bt.ind, baseline['name'])(self.data,
                                                                          **create_dict_of_placeholder_params(self,
                                                                                                              baseline))

                    def next(self):
                        if not self.position:  # not in the market
                            print(self.baseline[0])
                            if exec_(self.baseline[0], conf1['logic_l'], conf_th_l(self, conf1)):
                                if exec_(self.conf1[0], conf1['logic_l'], conf_th_l(self, conf1)):
                                    if exec("self.conf2[0] conf2['logic_l']) conf_th_l(self, conf2)"):
                                        print("lul")
                                        self.buy(size=order_size)  # enter long
                        elif self.baseline > 0.5:  # in the market & cross to the downside
                            self.close()  # close long position


                cerebro.optstrategy(StrategyClass)  # create_dict_of_params(baseline, conf1, conf2)
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
                        print(strategy.params)
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
