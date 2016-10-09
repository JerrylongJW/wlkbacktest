# encoding = utf-8

__author__ = 'wulinkai'

import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

#####################################################################
# CONSTANTS

TRADING_DAYS_PER_YEAR = 252
TRADING_DAYS_PER_MONTH = 20
TRADING_DAYS_PER_WEEK = 5


#####################################################################
# HELPER FUNCTIONS

def _difference_in_years(start, end):
    """ calculate the number of years between two dates """
    diff = end - start
    diff_in_years = (diff.days + diff.seconds / 86400) / 365.2425
    return diff_in_years


def _pct_change(close, period):
    diff = (close.shift(-period) - close) / close
    diff.dropna(inplace=True)
    return diff


#####################################################################
#   OVERALL RESULTS
#   pl:equity_cureve
#   dbal:holing_state


def _cagr(B, A, n):
    """ calculate compound annual growth rate """
    return np.power(B / A, 1 / n) - 1


def annual_return_rate(pl):
    B = pl[-1]
    A = pl[0]
    n = _difference_in_years(pl.index[0], pl.index[-1])
    return _cagr(B, A, n)


def trading_period(pl):
    diff = relativedelta(pl.index[-1], pl.index[0])
    return '{} 年 {} 月 {} 日'.format(diff.years, diff.months, diff.days)


def _total_days_in_market(dbal):
    dbal = dbal.swapaxes('items', 'minor')
    im = dbal['holds'].sum(1)
    return len(im[im != 0])


def pct_time_in_market(dbal):
    return _total_days_in_market(dbal) / len(dbal.major_axis)


#####################################################################
# DRAWDOWN AND RUNUP


def max_drawdown(pl):
    """ only compare each point to the previous running peak O(N) """
    running_max = pd.expanding_max(pl)
    cur_dd = (pl - running_max) / running_max
    dd_max = min(0, cur_dd.min())
    idx = cur_dd.idxmin()

    dd = pd.Series()
    dd['max_drawdown'] = dd_max * -1
    dd['peak'] = running_max[idx]
    dd['trough'] = pl[idx]
    dd['start_date'] = pl[
        pl == dd['peak']].index[0].strftime('%Y-%m-%d')
    dd['end_date'] = idx.strftime('%Y-%m-%d')
    pl = pl[pl.index > idx]

    rd_mask = pl > dd['peak']
    if rd_mask.any():
        dd['recovery_date'] = pl[rd_mask].index[0].strftime('%Y-%m-%d')
    else:
        dd['recovery_date'] = '还未恢复'
    return dd


def rolling_max_dd(pl, period):
    def max_dd(pl):
        return np.max(1 - pl / pd.expanding_max(pl))

    df = pd.rolling_apply(pl, window=period, func=max_dd)
    return df.dropna()


#####################################################################
# RATIOS


def sharpe_ratio(pl, risk_free=0.00, period=TRADING_DAYS_PER_YEAR):
    """
    summary Returns the daily Sharpe ratio of the returns.
    param rets: 1d numpy array or fund list of daily returns (centered on 0)
    param risk_free: risk free returns, default is 0%
    return Sharpe Ratio, computed off daily returns
    """
    rets = pl.pct_change()
    dev = np.std(rets, axis=0)
    mean = np.mean(rets, axis=0)
    sharpe = (mean * period - risk_free) / (dev * np.sqrt(period))
    return sharpe


def sortino_ratio(pl, risk_free=0.00, period=TRADING_DAYS_PER_YEAR):
    """
    summary Returns the daily Sortino ratio of the returns.
    param rets: 1d numpy array or fund list of daily returns (centered on 0)
    param risk_free: risk free return, default is 0%
    return Sortino Ratio, computed off daily returns
    """
    rets = pl.pct_change()
    mean = np.mean(rets, axis=0)
    negative_rets = rets[rets < 0]
    dev = np.std(negative_rets, axis=0)
    sortino = (mean * period - risk_free) / (dev * np.sqrt(period))
    return sortino


def annual_return_max_drawdown(pl):
    return annual_return_rate(pl) / np.max(1 - pl / pd.expanding_max(pl))

    #####################################################################
    # STATS - this is the primary call used to generate the results


def analysis(pl, dbal, capital, tpl):
    """
    Compute trading stats

    Parameters
    ----------
    pl : Series; 净值序列
    dbal : pandas.Panel; 每交易日各标的持仓信息
    capital: int; 初始资金
    tpl: pandas.DataFrame; 每笔交易盈亏信息

    Returns
    -------
    stats : Series of stats
    """

    stats = pd.Series()

    # OVERALL RESULTS
    stats['起始日'] = pl.index[0].strftime('%Y-%m-%d')
    stats['结束日'] = pl.index[-1].strftime('%Y-%m-%d')
    stats['初始资金'] = capital  # 如果第一日交易，则pl[0]！=初始资金
    stats['结束资金'] = pl[-1]
    stats['总盈亏'] = pl[-1] - pl[0]
    stats['累计收益'] = (pl[-1] - pl[0]) / pl[0]
    stats['年化收益'] = annual_return_rate(pl)
    stats['年化波动率'] = np.std(pl.pct_change()) * np.sqrt(TRADING_DAYS_PER_YEAR)
    stats['交易时长'] = trading_period(pl)
    stats['持仓时间占比'] = pct_time_in_market(dbal)

    # DRAWDOWN
    dd = max_drawdown(pl)
    stats['最大回撤'] = dd['max_drawdown']
    stats['年化收益回撤比'] = annual_return_max_drawdown(pl)
    stats['最大回撤起始期'] = dd['start_date']
    stats['最大回撤结束期'] = dd['end_date']
    stats['最大回撤恢复期'] = dd['recovery_date']
    stats['最大回撤恢复时长'] = _difference_in_years(datetime.strptime(
        dd['start_date'], '%Y-%m-%d'), datetime.strptime(dd['end_date'], '%Y-%m-%d'))

    dd = rolling_max_dd(pl, TRADING_DAYS_PER_YEAR)
    stats['平均年回撤'] = np.average(dd)
    stats['最大年回撤'] = max(dd)
    dd = rolling_max_dd(pl, TRADING_DAYS_PER_MONTH)
    stats['平均月回撤'] = np.average(dd)
    stats['最大月回撤'] = max(dd)
    dd = rolling_max_dd(pl, TRADING_DAYS_PER_WEEK)
    stats['平均周回撤'] = np.average(dd)
    stats['最大周回撤'] = max(dd)
    stats['交易笔数'] = len(tpl)
    tpl_states = tpl.returns.describe()
    stats['平均每笔交易收益'] = tpl_states['mean']
    stats['单笔交易最大盈利'] = tpl_states['max']
    stats['单笔交易最大亏损'] = tpl_states['min']
    stats['盈亏比'] = tpl.returns[tpl.returns > 0].mean(
    ) / abs(tpl.returns[tpl.returns < 0].mean())
    stats['胜率'] = len(tpl.returns[tpl.returns > 0]) / len(tpl)

    # RATIOS
    stats['夏普率'] = sharpe_ratio(pl)
    stats['索提诺比率'] = sortino_ratio(pl)
    res = pd.DataFrame(stats)
    res.columns = ['value']
    res.index.name = "Performance Statistics"
    return res
