# encoding = utf-8

__author__ = 'wulinkai'


# 账户类（包含下单函数；每日所有标的持仓量、持仓成本、市值信息；历史每笔成交记录；未平仓记录）
class Broker(object):

    import pandas as pd

    _TRADE_LOG = ['datetime', 'security',
                  'price', 'qty', 'state', 'long_short']
    _UNCLOSED_ORDER = ['price', 'open_qty', 'long_short', 'cost']
    _DAILY_BAL = ['date', 'price', 'holds', 'long_short', 'cost', 'hold_value']

    def __init__(self, data, context):
        '''
        param data:pandas Panel,交易数据
        param context:环境变量类
        '''

        self._cash = context.cash  # 账户可用现金余额
        self._slippage = context.slippage  # 交易滑点
        self._commission = context.commision  # 交易佣金

        self.now = None  # 当前回测时间戳
        self._cash_ts = dict()  # 每日现金余额序列
        self._trade_pl = []  # 每笔交易平仓盈亏序列

        # pandas.Panel;每个标的的每日持仓信息
        self._dailybalance = self._init_daily_bal(data, context.minute)

        # dict,key:security,value:pandas.DataFrame;未平仓标的信息表
        self._unclosed = self._init_unclosed_order(context.securities)

        # pandas.DataFrame;所有成交记录表
        self._tradelog = self.pd.DataFrame(columns=Broker._TRADE_LOG)

#####################################################################
#   Initialize Helper Functions

    # 初始化每个交易日未平仓信息表
    def _init_unclosed_order(self, securities):
        '''
        param securities: 所有订阅的标的，同context.securities

        return res: 字典，key为单标的名，value为pandas dataframe
        '''
        _df = self.pd.DataFrame(columns=Broker._UNCLOSED_ORDER)
        res = {sec: _df.copy() for sec in securities}
        return res

    # 初始化每个标的所有交易日持仓信息表
    def _init_daily_bal(self, data, minute):
        '''
        param data: 所有订阅的标的交易数据
        param minute: 策略数据频率，n分钟或日频数据。

        return res: pandas.Panel
        '''
        _dd = dict()
        tdx = data.major_axis if minute is None else self.pd.DatetimeIndex(
            self.pd.unique(data.major_axis.date))
        for sec in data.items:
            _df = self.pd.DataFrame(columns=Broker._DAILY_BAL)
            _df['date'] = tdx
            _df['holds'] = 0
            _df['cost'] = 0
            _df['hold_value'] = 0
            _df['long_short'] = None
            if minute is None:
                _df['price'] = data[sec]['close'].fillna(method='ffill').values
            else:
                _df['price'] = data[sec].at_time(
                    '15:00')['close'].fillna(method='ffill').values
            _df = _df.set_index('date')
            _dd[sec] = _df
        res = self.pd.Panel(_dd)
        return res
#####################################################################
#   Helper Functions

    # 返回所有标的的总持仓市值序
    def _hold_value_series(self):
        dfs = self._dailybalance.swapaxes('items', 'minor')
        return dfs['hold_value']

    # 记录成交下单
    def _record_trade(self, security, price, qty, direction, long_short):
        '''
        param security: 交易标的
        param price: 成交价格
        param qty: 成交量
        param direction: 开、平
        param long_short: 多、空
        '''
        t = {'price': price, 'qty': abs(qty), 'long_short': long_short,
             'datetime': self.now, 'security': security, 'direction': direction}

        self._tradelog = self._tradelog.append(t, ignore_index=True)

    # 开仓更新：原始持仓量、原始开仓成本加上新的开仓量及开仓成本
    def _open_update(self, security, price, open_qty, long_short):

        # 扣除手续费、及交易成本
        self._cash -= (1 + self._commission * 0.01) * price * open_qty

        df = self._unclosed[security]
        t = {'price': price, 'open_qty': open_qty,
             'long_short': long_short, 'cost': open_qty * price}
        df = df.append(t, ignore_index=True)
        self._unclosed[security] = df

    # 平仓更新：原始持仓量、原始开仓成本减去平仓量，并计算返回现金及盈亏
    def _close_update(self, security, close_price, close_qty, long_short):

        df = self._unclosed[security]
        re_cash_cost = 0  # 返回的成本
        re_cash_pl = 0  # 返回的盈亏

        for i in df.index:
            vol_i = df.at[i, 'open_qty']
            price_i = df.at[i, 'price']
            price_diff = close_price - price_i
            if vol_i < close_qty:
                re_cash_pl += vol_i * price_diff if long_short == 'long' else vol_i * -price_diff
                re_cash_cost += vol_i * price_i
                df.at[i, 'open_qty'] = 0
                df.at[i, 'cost'] = 0
                close_qty -= vol_i
            elif vol_i >= close_qty:
                re_cash_pl += close_qty * \
                    price_diff if long_short == 'long' else close_qty * -price_diff
                re_cash_cost += close_qty * price_i
                df.at[i, 'open_qty'] = vol_i - close_qty
                df.at[i, 'cost'] = (vol_i - close_qty) * price_i
                break

        df = df[df.open_qty != 0]
        df.index = range(len(df))
        self._unclosed[security] = df

        # 添加每笔平仓收益信息
        dd = {'close_date': self.now, 'trade_pl': re_cash_pl, 'cost': re_cash_cost,
              'returns': re_cash_pl / re_cash_cost, 'trade_type': long_short}
        self._trade_pl.append(dd)

        # 减手续费
        self._cash -= self._commission * 0.01 * abs(close_price * close_qty)
        # 更新现金余额
        self._cash += (re_cash_pl + re_cash_cost)

    # 下单能否成交,检查交易方向、金额是否足够，卖出标的量是否足够
    def _valid_order(self, security, price, shares, long_short):
        '''
        param security: 交易标的
        param price: 交易价格
        param shares: 交易量
        param long_short: 多、空
        '''

        # 获取标的的持仓量
        vol = self.curr_sec_hold_volume(security)

        # 有没平仓的交易时，不能做反向开仓交易
        if vol != 0 and self.curr_sec_direction(security) != long_short:
            print("exist reversed order,direction is", self.now, security)
            return False

        # 超过了可平仓量
        if shares < 0 and vol < abs(shares):  # 多平或空平
            print("not enough holding volume", self.now, security)
            return False

        cost = (1 + self._commission * 0.01) * abs(price * shares)  # 交易成本
        # 没有足够的现金开仓
        if shares > 0 and (self._cash < cost):    # 多开或者空开
            print("not enough remaining cash", self.now, security)
            return False

        return True

    # 按滑点更新成交价
    def _real_excute_price(self, order_price, direction, long_short):
        '''
        param order_price: 下单价格
        param direction: 开、平
        param long_short: 多、空
        '''
        real_price = None
        # 多开或者空平，实际成交价大于下单价
        if (direction == 'open' and long_short == 'long') or (direction == 'close' and long_short == 'short'):
            real_price = (1 + self._slippage * 0.01) * order_price
        # 空开或者多平，实际成交价小于下单价
        else:
            real_price = (1 - self._slippage * 0.01) * order_price
        return round(real_price, 2)

    # 更新账户每日持仓量、持仓成本及持仓市值(依据每日收盘价/结算价)
    def update_broker(self, datetime):

        self._cash_ts[datetime] = self._cash

        for sec in self._dailybalance.items:
            df = self._dailybalance[sec]
            open_order = self._unclosed[sec]
            if len(open_order) != 0:
                holds = open_order['open_qty'].sum()
                cost = open_order['cost'].sum()
                ls = open_order['long_short'].iat[-1]
                df.at[datetime, 'holds'] = holds
                df.at[datetime, 'cost'] = cost
                df.at[datetime, 'long_short'] = ls
                cal_value = df.at[datetime, 'price'] * holds
                df.at[
                    datetime, 'hold_value'] = cal_value if ls == 'long' else 2 * cost - cal_value

#####################################################################
# 回测结束后供strategy类调用

    # 获取净值序列
    def get_equity_curve(self):
        pl = self.curr_portfolio()
        return pl

    # 获取每个交易日持仓明细
    def get_daily_balance(self):
        return self._dailybalance

    # 获取成交记录
    def get_trade_record(self):
        return self._tradelog.set_index('datetime')

    # 获取每笔交易盈亏信息
    def get_trade_pl(self):
        tpl = self.pd.DataFrame(self._trade_pl)
        tpl = tpl.set_index('close_date')
        return tpl

#####################################################################
#   可在algo函数中调用

    # 查找标的的最新持仓量
    def curr_sec_hold_volume(self, sec):
        return self._unclosed[sec]['open_qty'].sum()

    # 查找标的的最新持仓市值序列,截止前一交易日
    def curr_sec_hold_value(self, sec):
        v_ts = self._hold_value_series()
        holdval = v_ts.ix[:self.now, sec]
        return holdval[:-1]

    # 查找标的的多空方向
    def curr_sec_direction(self, sec):
        return self._unclosed[sec]['long_short'][0]

    # 查找最近n个交易期标的持仓市值的最大回撤
    def curr_sec_latest_drawdown(self, sec, n):
        '''
        param sec: 标的名
        param n: 往前n个bar期
        '''
        pl = self.curr_sec_hold_value(sec)
        pl = pl[-n:]
        if (pl != 0).all():
            return max(1 - pl / self.pd.expanding_max(pl))

    # 返回有仓位的标的数量
    def curr_hold_nums(self):
        res = 0
        for x in self._unclosed.values():
            if len(x) != 0:
                res += 1
        return res

    # 查找最近n个交易期总持仓市值的最大回撤
    def curr_latest_drawdown(self, n):
        '''
        param sec: 标的名
        param n: 往前n个bar期
        '''
        pl = self._hold_value_series().sum(1)
        pl = pl[-n:]
        if (pl != 0).all():
            return max(1 - pl / self.pd.expanding_max(pl))

    # 查找账户的最新总持仓市值序列,截止上一交易日
    def curr_hold_value(self):
        v_ts = self._hold_value_series().sum(1)
        return v_ts.ix[:self.now].ix[:-1]

    # 查找账户的最新净值序列,截止上一交易日
    def curr_portfolio(self):
        v_ts = self._hold_value_series().sum(1)
        c_ts = self.pd.Series(self._cash_ts)
        p_ts = self.pd.concat([v_ts, c_ts], axis=1).dropna()
        return p_ts.sum(1)

    # 账户下单函数
    # 按量（手）下单
    def order_share(self, security, order_price, shares, long_short='long', real_price=False):
        '''
        param
        -----
        security: str; 标的名称
        order_price: float or int;下单价格
        shares: int; 正数为开仓,负数为平仓
        long_short:str; 'long','short'
        real_price: bool; 是否为按滑点更新后的成交价

        return
        ----
        True：成交
        False:失败 
        '''
        assert(shares != 0)
        assert(long_short in ['long', 'short'])
        # 开平方向
        direction = 'open' if shares > 0 else 'close'

        price = order_price
        if not real_price:  # 获取真实交易价
            price = self._real_excute_price(order_price, direction, long_short)

        if not self._valid_order(security, price, shares, long_short):  # 订单是否有效
            return False

        # 开仓
        if direction == 'open':
            # 更新持仓信息、计算开仓成本
            self._open_update(security, price, shares, long_short)
        # 平仓
        else:
            # 更新未平仓表，计算返回现金，及平仓盈亏
            self._close_update(security, price, abs(shares), long_short)

        # 记录该笔交易
        self._record_trade(security, price, shares, direction, long_short)
        return True

    # 按比例下单
    def order_percent(self, security, order_price, percent, long_short='long'):
        '''
        security: str; 标的名称
        order_price: float or int; 下单价格
        percent: float; 正数为开仓，代表所占的剩余现金的比例；负数为平仓，代表持仓市值的比例
        long_short:str; 'long','short'
        '''
        if percent < -1 or percent > 1:
            raise ValueError("percent must between - 1 to 1")

        direction = 'open' if percent > 0 else 'close'

        price = self._real_excute_price(order_price, direction, long_short)

        if direction == 'open':
            shares = int(self._cash * (1 - self._commission * 0.01)
                         * percent / price)
        elif direction == 'close':
            vol = self.curr_sec_hold_volume(security)
            shares = int(vol * percent)

        self.order_share(security, price, shares, long_short, real_price=True)
