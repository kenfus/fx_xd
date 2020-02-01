#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 12:56:52 2020

@author: vincenzot, der smarte
"""


class PandasData(feed.DataBase):
    '''
    The ``dataname`` parameter inherited from ``feed.DataBase`` is the pandas
    DataFrame
    '''
    if 'datetime' not in df or isinstance(df.index, pandas.core.index.MultiIndex):
    self.feed.DataBase['datetime'] = self.feed.DataBase.index
    self.feed.DataBase = self.feed.DataBase[self.feed.DataBase.columns.get_level_values(0)]
    self.feed.DataBase.reset_index(inplace = True)
    ### bidopen 	bidclose 	bidhigh 	bidlow 	askopen 	askclose 	askhigh 	asklow 	tickqty
    params = (
        # Possible values for datetime (must always be present)
        #  None : datetime is the "index" in the Pandas Dataframe
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('datetime', None),

        # Possible values below:
        #  None : column not present
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
    )
    