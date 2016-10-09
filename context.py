# encoding = utf-8

__author__ = 'wulinkai'


# 策略配置环境
class Context(object):

    def __init__(self):
        self._cash = 1000000  # 账户初始资金
        self._slippage = 0.246  # 交易滑点
        self._commision = 0.03  # 交易手续费
        self._minute = None  # 用x分钟数据回测，默认None为日频数据

        # 用户必须自己定义策略回测标的，起始日期及结束日期
        self._securities = None  # 标的列表（['zz500'],['hs300','600010.sh'])
        self._start = None  # 策略起始回测日 ('20150101','2015-8-2','2015-08-02')
        self._end = None  # 策略结束回测日

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError('cash must be an number')
        self._cash = value

    @property
    def minute(self):
        return self._minute

    @minute.setter
    def minute(self, value):
        if not isinstance(value, int):
            raise TypeError('minute must be int')
        self._minute = value

    @property
    def slippage(self):
        return self._slippage

    @slippage.setter
    def slippage(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError('slippage must be an number')
        self._slippage = value

    @property
    def commision(self):
        return self._commision

    @commision.setter
    def commision(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError('commision must be an number')
        self._commision = value

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        if isinstance(value, str):
            from dateutil.parser import parse
            start = parse(value)
            self._start = start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        if isinstance(value, str):
            from dateutil.parser import parse
            end = parse(value)
            self._end = end

    @property
    def securities(self):
        return self._securities

    @securities.setter
    def securities(self, securities):
        if not isinstance(securities, list):
            raise TypeError('securities must be list type')
        self._securities = securities
