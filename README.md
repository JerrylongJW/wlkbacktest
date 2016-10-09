# wlkbacktest
* <font size=3> 基于Python Pandas的轻量级事件驱动回测框架，API类Quantopian,RiceQuant。 </font>       
* <font size=3> 支持多标的、做空、自定义数据，策略统计分析，图形展示等特性。</font>      

---
# 1. 使用说明
* <font size=3> 用户需定义init, algo两个函数，来初始化策略的环境配置和具体的算法逻辑。</font>    
* <font size=3> init函数中的context参数为Context类对象，用户添加context对象的属性值，来初始化策略的基本信息。例如初始资金、订阅标的名、滑点设置。</font>       
* <font size=3> algo函数为策略的算法逻辑，data为订阅标的的历史交易数据，broker为账户对象，可完成下单，标的持仓等事宜，context与init中的为同一对象。</font>      
* <font size=3> 策略若采用N分钟数据，则每N分钟调用一次algo函数，执行交易逻辑。若采用日数据，则每日调用。</font>   
* <font size=3> 简单范例： </font>   

```python
# 策略环境设置函数
def init(context,**kwargs):
    context.start = '20130101'             # 初始日期
    context.end = '20151231'               # 结束日期
    context.cash = 10000000                # 策略资金
    context.minute = 1                     # 回测采用1分钟数据
    context.slippage = 0.2                 # 交易滑点
    context.commision = 0.02               # 手续费万二
    context.securities = ['zz500']         # 订阅标的
    
    context.sec = 'zz500'
    context.holding = False #是否持有
    context.state = None #多空状态

# 策略交易逻辑函数
def algo(data,broker,context):
    df = data[context.sec] #获取中证500标的数据
    now = broker.now #当前bar期
    
    t_close = df['close'][-1] #最新收盘价
    y_close = df['close'][-2] #上跟bar的收盘价
    #策略逻辑
    
    if not context.holding and now < context.end:
        if t_close > 1.02 * y_close:
            if broker.order_percent(context.sec,t_close,1,'long'): #多开
                context.state = 'long'
                context.holding = True
        elif t_close < 0.98 * y_close:
            if broker.order_percent(context.sec,t_close,1,'short'): #空开
                context.state = 'short'
                context.holding = True
    elif context.holding or now >= context.end: 
        if t_close < 0.98 * y_close and context.state = 'long':
            if broker.order_percent(context.sec,t_close,-1,'long'): #多平
                context.state = None
                context.holding = False
        if t_close > 1.02 * y_close and context.state = 'short':
            if broker.order_percent(context.sec,t_close,-1,'short'): #空平
                context.state = None
                context.holding = False
```
* <font size=3> 可参考策略demo.ipynb[]</font>    

---
# 2. 文档说明

### context.py
* <font size=3> 策略的环境变量类，用户在init函数中定义其对象属性值，供Strategy类对象使用 </font>  
* <font size=3> 可定义对象包括:   </font>    
&nbsp;&nbsp;context.cash : 账户资金  
&nbsp;&nbsp;context.slippage : 交易滑点  
&nbsp;&nbsp;context.commission : 交易佣金  
&nbsp;&nbsp;context.minute : 策略所采用的数据频次    
&nbsp;&nbsp;context.securities : 订阅标的列表（必须）&nbsp;&nbsp;&nbsp;格式:['zz500'], ['600010.sh', '300001.SZ']  
&nbsp;&nbsp;context.start : 策略起始时间（必须)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;格式:'2013-1-1', '20130101', '2013-01-01'     
&nbsp;&nbsp;context.end : 策略结束时间（必须）&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;格式:'2013-1-1', '20130101', '2013-01-01'      
* <font size=3> 用户可自行为context添加额外属性变量，方便在algo函数中使用

---

### datahandler.py
* <font size=3> 数据获取类，提供策略所需要的标的历史交易数据，供Strategy类对象使用  </font>  
* <font size=3> 通过context中的 securities，start，end，minute 4个属性值，从本地获取策略所需要的交易数据  </font>  
* <font size=3> datahandler提供的数据格式为pandas.Panel，该数据结构类似dict，key为标的名称，value为一个pandas.DataFrame</font>  
* **默认本地数据文件用csv保存，文件名即为证券代码名，如600010.sh.csv,300003.sz.csv,zz500.csv**  
* **默认csv文件内容：列名：date,open,high,low,close,volume,amount。第二行起为数据内容**  
* **默认本地数据文件存储路径为 D:/Data/Daily/xxxx.csv , D:/Data/Minute/X（数字）/xxxx.csv; 日度、分钟数据分开存储**   



---

###  strategy.py
* <font size=3> 策略类 : 装载交易数据，获取策略环境变量，执行交易逻辑，分析回测结果，展示回测信息) </font>  
* <font size=3> 可调用函数:   </font>  

```python
# 执行算法回测，传入用户编写的algo函数
def run_backtest(self, algo, **kwargs):
    
# 返回策略所需的交易数据
def get_trading_data(self):

# 返回策略的环境变量对象
def get_context(self):

# 获取回测结果，包含净值曲线、每交易日持仓信息、每笔平仓收益信息、所有开平仓记录（执行完 run_backtest 后调用）
def backtest_result(self):

# 获取策略的回测统计信息（执行完 run_backtest 后调用）
def backtest_analysis(self):

# 画出策略的净值曲线图
def show_equity_curve(self, benchmark=None, standardize=True):

# 画出策略里各标的开仓点位及持仓市值信息
def show_trade_information(self):

```

* <font size=3> 使用示例:   </font>  

```python
def init(context,**kwargs):
  context.securities = ['zz500']
  context.start = '20130101'
  context.end = '20130101'
  
  context.sec = 'zz500'

def algo(data,broker,context):
    #策略逻辑
    

strategy = Strategy(init) # 初始化策略，传入init函数
strategy.run_backtest(algo) # 执行策略算法
df = strategy.backtest_analysis() # 获取策略回测统计信息
strategy.show_equity_curve() # 画出净值曲线
strategy.show_trade_information() #展示开平仓点位

```


---


### Broker.py
* <font size=3> 交易账户类：提供下单功能、市值查询等功能；记录持仓信息,成交记录信息,账户净值信息  </font>  
* <font size=3> 每次algo调用完后，更新最新的持仓信息，账户净值、现金余额等信息</font>  
* <font size=3> 提供各类辅助查询等支持函数，供algo函数中的broker对象调用,包括：  </font>  
```python
#   可在algo函数中调用

# 查找某标的的最新持仓量
def curr_sec_hold_volume(self, sec):
    '''
    param sec: 标的名
    '''
    
# 查找某标的最新持仓市值序列,截止前一交易日
def curr_sec_hold_value(self, sec):
    '''
    param sec: 标的名
    '''

# 查找标的的多空方向
def curr_sec_direction(self, sec):
    '''
    param sec: 标的名
    '''

# 查找最近n个交易期某标的持仓市值的最大回撤
def curr_sec_latest_drawdown(self, sec, n):
    '''
    param sec: 标的名
    param n: 往前n个bar期
    '''

# 返回有仓位的标的数量
def curr_hold_nums(self):

# 查找最近n个交易期总持仓市值的最大回撤
def curr_latest_drawdown(self, n):
    '''
    param sec: 标的名
    param n: 往前n个bar期
    '''

# 查找账户的最新总持仓市值序列,截止上一交易日
def curr_hold_value(self):

# 查找账户的最新净值序列,截止上一交易日
def curr_portfolio(self):

########## 账户下单函数
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
    True：成交;False:失败 
    '''

# 按比例下单
def order_percent(self, security, order_price, percent, long_short='long'):
    '''
    security: str; 标的名称
    order_price: float or int; 下单价格
    percent: float; 正数为开仓，代表所占的剩余现金的比例；负数为平仓，代表持仓市值的比例
    long_short:str; 'long','short'
    '''
```  

* <font size=3> 提供给Strategy类回测结果，函数包括：  </font>
```python
#####################################################################
# 回测结束后供strategy类调用

# 获取净值序列
def get_equity_curve(self):

# 获取每个交易日持仓明细
def get_daily_balance(self):

# 获取成交记录
def get_trade_record(self):

# 获取每笔交易盈亏信息
def get_trade_pl(self):
```
---

### analyzer.py
* <font size=3> 回测结果分析模块 </font>  
* <font size=3> 提供完整的回测统计信息，包括 夏普、年化收益、波动率、最大回撤、盈亏比、胜率等常见信息</font>   
* <font size=3> analysis函数以pandas.DataFrame格式返回结果给Strategy调用 </font>   
