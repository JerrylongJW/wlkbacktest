# wlkbacktest
* <font size=3> 基于Python Pandas的轻量级事件驱动回测框架，API类Quantopian,RiceQuant。 </font>       
* <font size=3> 支持多标的、做空、自定义数据，策略统计分析，图形展示等特性。</font>      

---
# 1. 使用说明
* <font size=3> 用户需定义init, algo两个函数，来初始化策略的环境配置和具体的算法逻辑。</font>    
* <font size=3> init函数中的context参数为Context类对象，用户添加context对象的属性值，来初始化策略的基本信息。例如初始资金、订阅标的名、滑点设置。</font>       
* <font size=3> algo函数为策略的算法逻辑，data为订阅标的的历史交易数据，broker为账户对象，可完成下单，标的持仓等事宜，context与init中的为同一对象。</font>      
* <font size=3> 策略若采用N分钟数据，则每N分钟调用一次algo函数，执行交易逻辑。若采用日数据，则每日调用。</font>     

```python
# 策略环境设置函数
def init(context,**kwargs):
    context.start = '20130101'             # 初始日期
    context.end = '20151231'               # 结束日期
    context.cash = 10000000                # 策略资金
    context.minute = 1                     # 回测采用1分钟数据
    context.slippage = 0.2                 # 交易滑点
    context.commision = 0.02               # 万二
    context.securities = ['zz500']         # 订阅标的

# 策略交易逻辑函数
def algo(data,broker,context,**kwargs):
    pass
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
* <font size=3> 交易账户类：提供下单函数功能；记录每日所有标的持仓量、持仓成本、市值信息；记录历史每笔成交记录；未平仓记录  </font>  
* <font size=3>   </font>  
* <font size=3> datahandler提供的数据格式为pandas.Panel，该数据结构类似dict，key为标的名称，value为一个pandas.DataFrame</font>  
* **默认本地数据文件用csv保存，文件名即为证券代码名，如600010.sh.csv,300003.sz.csv,zz500.csv**  
* **默认csv文件内容：列名：date,open,high,low,close,volume,amount。第二行起为数据内容**  
* **默认本地数据文件存储路径为 D:/Data/Daily/xxxx.csv , D:/Data/Minute/X（数字）/xxxx.csv; 日度、分钟数据分开存储**   
