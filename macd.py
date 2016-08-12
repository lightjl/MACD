'''
================================================================================
总体回测前
================================================================================
'''
# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    # 000001(股票:平安银行)
    g.security = '000001.XSHE'
    #设定沪深300作为基准
    set_benchmark('000300.XSHG')

    
'''
================================================================================
每天开盘前
================================================================================
'''
#每天开盘前要做的事情
def before_trading_start(context):
    if g.t%g.tc==0:
        g.if_trade=True                       # 每g.tc天，调仓一次
        set_slip_fee(context)                 # 设置手续费与手续费
        # 设置可行股票池
        g.feasible_stocks = set_feasible_stocks(g.stocks,context)
    g.t+=1
    

#5
# 根据不同的时间段设置滑点与手续费
# 输入：context（见API）
# 输出：none
def set_slip_fee(context):
    # 将滑点设置为0
    set_slippage(FixedSlippage(0)) 
    # 根据不同的时间段设置手续费
    dt=context.current_dt
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5)) 
        
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
            
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))
        
'''
================================================================================
每天交易时
================================================================================
'''
# 每天回测时做的事情
def handle_data(context,data):
    if g.if_trade == True:
        # 待买入的g.num_stocks支股票，list类型
        list_can_buy = stocks_to_buy(context)
        # 待卖出的股票，list类型
        list_to_sell = stocks_to_sell(context, list_can_buy)
        # 需买入的股票
        list_to_buy = pick_buy_list(context, list_can_buy)
        # 卖出操作
        sell_operation(list_to_sell)
        # 买入操作
        buy_operation(context, list_to_buy)
    g.if_trade = False