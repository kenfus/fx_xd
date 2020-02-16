import datetime as dt
import getpass
import os.path
import inspect
import fxcmpy
import pandas as pd
import operator
import ast
import numbers
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
maxcpus = 6
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
    params_names, params_values, params_names_with_none = [], [], []
    for arg in args:
        params_names_with_none.extend([arg['param1_name'], arg['param2_name'], arg['param3_name']])
        if not pd.isna(arg['th_l']):
            params_names_with_none.append('th_l')
        if not pd.isna(arg['th_s']):
            params_names_with_none.append('th_l')

    [params_names.append((param_name)) if not pd.isna(param_name) else None for param_name in params_names_with_none]
    [params_values.append((1)) if not pd.isna(param_name) else None for param_name in params_names_with_none]

    return dict(zip(params_names, params_values))

def create_dict_of_params(*args):
    params_names, params_values, params_names_with_none, params_values_with_none = [], [], [], []
    for arg in args:
        params_names_with_none.extend([arg['param1_name'], arg['param2_name'], arg['param3_name']])
        params_values_with_none.extend([arg['param1_value'], arg['param2_value'], arg['param3_value']])

        if not pd.isna(arg['th_l']):
            params_names_with_none.append('th_l')
            params_values_with_none.append(arg['th_l'])
        if not pd.isna(arg['th_s']):
            params_names_with_none.append('th_l')
            params_values_with_none.append(arg['th_l'])
    [params_names.append((param_name)) if not pd.isna(param_name) else None for param_name in params_names_with_none]

    for param_value in params_values_with_none:
        if not pd.isna(param_value):
            if isinstance(param_value, numbers.Number):
                params_values.append(param_value)
            else:
                params_values.append(eval(param_value))
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


def get_operator_fn(op):
    return {
        '<=': operator.le,
        '>=': operator.ge,
        '<': operator.lt,
        '>': operator.gt,
    }[op]


def get_value_to_compare(self, str):
    if not pd.isna(str):
        th_l = self.params.th_l
    else:
        th_l = self.data.close[0]
    return th_l


def baseline_th_l(self, ind):
    th_l = get_value_to_compare(self, ind['th_l'])
    return get_operator_fn(ind['logic_l'])(self.baseline[0], th_l)


def conf_th_l(self, ind):
    th_l = get_value_to_compare(self, ind['th_l'])
    return get_operator_fn(ind['logic_l'])(self.conf1[0], th_l)


def conf2_th_l(self, ind):
    th_l = get_value_to_compare(self, ind['th_l'])
    return get_operator_fn(ind['logic_l'])(self.conf2[0], th_l)


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
                cerebro = bt.Cerebro(optreturn=False, maxcpus=maxcpus)

                # Add strategy to cerebro. To avoid merge errors, it detects which strategy to apply
                class StrategyClass(bt.Strategy):
                    params = create_dict_of_placeholder_params_init(baseline, conf1, conf2)

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
                            if baseline_th_l(self, baseline):
                                if conf_th_l(self, conf1):
                                    if conf_th_l(self, conf2):
                                        self.buy(size=order_size)  # enter long
                        elif self.baseline > 0.5:  # in the market & cross to the downside
                            self.close()  # close long position


                cerebro.optstrategy(StrategyClass, **create_dict_of_params(baseline, conf1, conf2))  #
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
                        conf_ind = conf1['name']
                        conf_ind2 = conf2['name']
                        baseline_ind = baseline['name']
                        final_results_list.extend(
                            [PnL, percent_PnL, conf_ind, conf_ind2, baseline_ind])
                        desired_output = ['PnL', 'PnL%', 'Conf1 Ind', 'Conf 2 Ind', 'Baseline Ind']
                        for key, value in create_dict_of_params(baseline, conf1, conf2).items():
                            final_results_list.append(getattr(strategy.params, key))
                            desired_output.append(key)
                final_results_dict = dict(zip(desired_output, final_results_list))

                # Print results
                print('Results, unordered')
                print(final_results_dict)
