#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 12:56:52 2020

@author: vincenzot
"""
import pandas as pd

def fxcm_df_to_bt_df(df, start_dt, stop_dt, token_to_trade, time_frame, renaming):
    if isinstance(df.index, pd.core.index.MultiIndex):
        df.reset_index(inplace = True)
    df.rename(renaming, axis='index', inplace = True)
    return df