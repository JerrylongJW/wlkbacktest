# encoding = utf-8

__author__ = 'wulinkai'


# 获取交易数据类
class DataHandler(object):

    import pandas as pd
    import datetime
    import os

    # 本地交易数据文件地址,包含分钟数据和日频数据
    _DAILY_DATA = "D:/Data/Daily/"
    _MINUTE_DATA = "D:/Data/Minute/"

    def __init__(self, context):
        '''
        param context: 策略环境变量，含有securities,start,end,minute等属性
        '''
        assert(isinstance(context.start, self.datetime.datetime))
        assert(isinstance(context.end, self.datetime.datetime))

        self._start = str(context.start.date())  # str. example:'xxxx-xx-xx'
        self._end = str(context.end.date())
        # list. example: ['600010.SH'], ['zz500','hs300','300010.sz']
        self._secs = context.securities
        self._minute = context.minute  # int or None

    # 获取所有订阅标的交易数据
    def fetch_data(self):
        '''
        return: trading datas,pandas Panel
        '''
        datas = dict()
        for sec in self._secs:
            df = self._fetch_sigle_data(sec)
            datas[sec] = df
        return self.pd.Panel(datas)

    # 订阅单只标的的数据
    def _fetch_sigle_data(self, security):
        '''
        return: trading data,pandas DataFrame timeseries
        '''
        security = security.upper()
        if self._minute is None:
            file_ = self._DAILY_DATA + security + ".csv"
        else:
            file_ = self._MINUTE_DATA + \
                str(self._minute) + "/" + security + ".csv"

        if not self.os.path.exists(file_):
            raise IOError('no local csv file')
        else:
            df = self.pd.read_csv(file_, index_col=0, parse_dates=True)
            return df.ix[self._start:self._end]
