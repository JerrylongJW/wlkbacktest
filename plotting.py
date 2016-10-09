# encoding = utf-8

__author__ = 'wulinkai'


import matplotlib.pyplot as plt

plt.style.use('ggplot')
plt.rcParams['savefig.dpi'] = 1.2 * plt.rcParams['savefig.dpi']


# 画出净值曲线
def plot_equity_curve(pl, benchmark, standardize=True):
    """ Plot Equity Curves: Strategy vs (optionally) Benchmark

    param pl: pandas.Series,策略净值曲线
    param benchmark: pandas.DataFrame,含'close'列。

    """
    fig = plt.figure(figsize=(15, 6.5))
    ax1 = fig.add_subplot(111)

    if standardize:
        pl = pl / pl[0]
        ts = benchmark['close'].pct_change()
        ts[0] = 0
        ts = (1 + ts).cumprod()
        pl.plot(label='strategy', c='r')
        ts.plot(label='benchmark', c='k')
        plt.ylabel('Equity Curve', fontsize=13, color='k')
        plt.xlabel('Backtest Periods', fontsize=13, color='k')
    else:
        ax1.plot(pl, label='strategy', c='r')
        ax1.set_ylabel('Portfolio Values', fontsize=13)
        ax1.set_xlabel('Backtest Periods', fontsize=13)
        ax2 = ax1.twinx()  # this is the important function
        ax2.plot(benchmark['close'], label='benchmark', c='k')
        ax2.set_ylabel('Benchmark Time Series', fontsize=13)

    plt.legend(loc='best', fontsize=12)


# 画出策略里各个标的的持仓市值及下单点位
def plot_all(dbal, tlog):
    dxs = 15
    dys = 6.5
    nums = len(dbal.items)
    f, axes = plt.subplots(2 * nums, figsize=(dxs, dys * 2 * nums))
    for i, sec in enumerate(dbal.items):
        x = dbal[sec]['price']
        z = dbal[sec]['hold_value']
        y = tlog[tlog.security == sec]
        l_o = [t for t in y[(y.direction == 'open') &
                            (y.long_short == 'long')].index]
        _l_o = [x.date() for x in l_o]
        s_o = [t for t in y[(y.direction == 'open') &
                            (y.long_short == 'short')].index]
        _s_o = [x.date() for x in s_o]
        l_c = [t for t in y[(y.direction == 'close') &
                            (y.long_short == 'long')].index]
        _l_c = [x.date() for x in l_c]
        s_c = [t for t in y[(y.direction == 'close') &
                            (y.long_short == 'short')].index]
        _s_c = [x.date() for x in s_c]
        axes[2 * i].plot(x.index, x, c='k')
        axes[2 * i].plot(_l_o, y.ix[l_o].price, '^',
                         markersize='7', c='r', label='long_open')
        axes[2 * i].plot(_s_o, y.ix[s_o].price, '^',
                         markersize='7', c='b', label='short_open')
        axes[2 * i].plot(_l_c, y.ix[l_c].price, 'v',
                         markersize='7', c='g', label='long_close')
        axes[2 * i].plot(_s_c, y.ix[s_c].price, 'v',
                         markersize='7', c='y', label='short_close')
        axes[2 * i].set_xlabel(sec, fontsize=13, color='k')
        axes[2 * i].set_ylabel('Price', fontsize=15, color='k')
        axes[2 * i].legend(loc='best', fontsize=11)
        #
        axes[2 * i + 1].plot(z.index, z, c='k')
        axes[2 * i + 1].plot(_l_o, z.ix[_l_o], '^',
                             markersize='7', c='r', label='long_open')
        axes[2 * i + 1].plot(_s_o, z.ix[_s_o], '^',
                             markersize='7', c='b', label='short_open')
        axes[2 * i + 1].plot(_l_c, z.shift(1).ix[_l_c], 'v',
                             markersize='7', c='g', label='long_close')
        axes[2 * i + 1].plot(_s_c, z.shift(1).ix[_s_c], 'v',
                             markersize='7', c='y', label='short_close')
        axes[2 * i + 1].set_xlabel(sec, fontsize=13, color='k')
        axes[2 * i + 1].set_ylabel('Hold Value', fontsize=15, color='k')
        axes[2 * i + 1].legend(loc='best', fontsize=11)
    f.subplots_adjust(hspace=0.2)
