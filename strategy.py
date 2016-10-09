# encoding = utf-8

__author__ = 'wulinkai'

from .datahandler import DataHandler
from .context import Context
from .broker import Broker
from .plotting import plot_equity_curve, plot_all
from .analyzer import analysis
import pandas as pd

# format data
pd.options.display.float_format = '{:0.4f}'.format


# 策略类(装载交易数据，策略环境变量，执行交易逻辑，获取交易结果)
class Strategy(object):

    def __init__(self, initialize, **kwargs):
        '''
        param initialize: function ,user define
        '''
        # 定义策略环境变量成员
        self._context = Context()

        # 初始化策略环境变量成员
        initialize(self._context, **kwargs)

        # 定义数据获取成员
        self._datahandler = DataHandler(self._context)
        # 获取策略所需标的的历史交易数据
        self._data = self._datahandler.fetch_data()

        # 初始化账户基本信息
        self._broker = Broker(self._data, self._context)

# 执行回测

    def run_backtest(self, algo, **kwargs):
        '''
        param algo: function，策略逻辑,用户自定义
        '''
        # #记录策略耗时
        # import time
        # t0 = time.time()

        # 回测时间戳
        ts_idx = self._data.major_axis  # panel index

        # 按行情序列回测
        for t in ts_idx:
            if t < self._context.start:
                continue

            self._broker.now = t
            # 取该时刻及之前数据
            datas = self._data.ix[:, :t, :]

            # 执行交易逻辑
            algo(datas, self._broker, self._context, **kwargs)

            # 每日交易结束后更新净值(日频每日更新，高频每日15点后更新)
            if self._context.minute is None or t.hour == 15:
                # 转换成日频数据的 Timestamp('20XX-XX-XX 00:00:00')
                if self._context.minute is not None:
                    t = t.replace(hour=0, minute=0, second=0)

                # 更新每日的持仓市值信息
                self._broker.update_broker(t)

        # t1 = time.time()
        # print('the strategy backtesing consuming %f seconds' % (t1 - t0))

    def get_trading_data(self):
        return self._data

    def get_context(self):
        return self._context

    def backtest_result(self):
        pl = self._broker.get_equity_curve()
        dbal = self._broker.get_daily_balance()
        tpl = self._broker.get_trade_pl()
        tlog = self._broker.get_trade_record()
        return pl, dbal, tpl, tlog

    def backtest_analysis(self):
        pl = self._broker.get_equity_curve()
        dbal = self._broker.get_daily_balance()
        tpl = self._broker.get_trade_pl()
        return analysis(pl, dbal, self._context.cash, tpl)

    # 画出策略的净值曲线图
    def show_equity_curve(self, benchmark=None, standardize=True):
        # 高频数据转换为日频
        if benchmark is None:
            secs = self._data.items
            if len(secs) == 1:
                benchmark = self._data[secs[0]]
                if self._context.minute is not None:
                    benchmark = benchmark.at_time('15:00')

        pl = self._broker.get_equity_curve()
        plot_equity_curve(pl, benchmark, standardize)

    # 画出策略里各标的开仓点位及持仓市值信息
    def show_trade_information(self):
        tlog = self._broker.get_trade_record()
        dbal = self._broker.get_daily_balance()
        plot_all(dbal, tlog)
