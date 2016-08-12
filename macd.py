import talib
import numpy as np
import pandas as pd
'''
================================================================================
总体回测前
================================================================================
'''
# 初始化函数，设定要操作的股票、基准等等
#总体回测前要做的事情
def initialize(context):
    set_params()                             # 设置策略常量
    set_variables()                          # 设置中间变量
    set_backtest()                           # 设置回测条件

#1 
#设置策略参数
def set_params():
    g.tc = 1                                 # 调仓天数
    g.num_stocks = 10                        # 每次调仓选取的最大股票数量
    g.stocks=get_index_stocks('000300.XSHG') # 设置沪深300为初始股票池
    g.per = 0.1                              # EPS增长率不低于0.25

#2
#设置中间变量
def set_variables():
    g.t = 0                                  # 记录回测运行的天数
    g.if_trade = False                       # 当天是否交易

#3
#设置回测条件
def set_backtest():
    set_option('use_real_price',True)        # 用真实价格交易
    log.set_level('order','debug')           # 设置报错等级

    
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
    
#4
# 设置可行股票池：过滤掉当日停牌的股票
# 输入：initial_stocks为list类型,表示初始股票池； context（见API）
# 输出：unsuspened_stocks为list类型，表示当日未停牌的股票池，即：可行股票池
def set_feasible_stocks(initial_stocks,context):
    # 判断初始股票池的股票是否停牌，返回list
    paused_info = []
    current_data = get_current_data()
    for i in initial_stocks:
        paused_info.append(current_data[i].paused)
    df_paused_info = pd.DataFrame({'paused_info':paused_info},index = initial_stocks)
    unsuspened_stocks =list(df_paused_info.index[df_paused_info.paused_info == False])
    
    df_st_info = get_extras('is_st',unsuspened_stocks,start_date=context.current_dt,end_date=context.current_dt)
    df_st_info = df_st_info.T
    df_st_info.rename(columns={df_st_info.columns[0]:'is_st'}, inplace=True)
    unsuspened_stocks = list(df_st_info.index[df_st_info.is_st == False])
    return unsuspened_stocks


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
        list_can_buy = stocks_can_buy(context)
        # 待卖出的股票，list类型
        list_to_sell = stocks_to_sell(context)
        # 需买入的股票
        list_to_buy = pick_buy_list(context, list_can_buy, list_to_sell)
        # 卖出操作
        sell_operation(list_to_sell)
        # 买入操作
        buy_operation(context, list_to_buy)
    g.if_trade = False
    
def stocks_can_buy(context):
    list_to_buy = []
    return list_to_buy
    
#8
# 获得卖出信号
# 输入：context（见API文档）, list_to_buy为list类型，代表待买入的股票
# 输出：list_to_sell为list类型，表示待卖出的股票
def stocks_to_sell(context):
    list_to_sell = []
    return list_to_sell
    
# 获得买入的list_to_buy
# 输入list_can_buy 为list，可以买的队列
# 输出list_to_buy 为list，买入的队列
def pick_buy_list(context, list_can_buy, list_to_sell):
    list_to_buy = []
    # 要买数 = 可持数 - 持仓数 + 要卖数（todo: 有些卖不出）
    buy_num = g.num_stocks - len(context.portfolio.positions.keys()) + len(list_to_sell)
    if buy_num <= 0:
        return list_to_buy
    # 得到一个dataframe：index为股票代码，data为相应的PEG值
    # 排序-------------------------------------------------
    ad_num = 0;
    for i in list_can_buy:
        if i not in context.portfolio.positions.keys():
            list_to_buy.append(i)
            ad_num = ad_num + 1
        if ad_num >= buy_num
            break
    return list_to_buy


'''
    全仓买卖
    todo 仓位控制
'''    
#9
# 执行卖出操作
# 输入：list_to_sell为list类型，表示待卖出的股票
# 输出：none
def sell_operation(list_to_sell):
    for stock_sell in list_to_sell:
        order_target_value(stock_sell, 0)
        
#10
# 执行买入操作
# 输入：context(见API)；list_to_buy为list类型，表示待买入的股票
# 输出：none
def buy_operation(context, list_to_buy):
    for stock_buy in list_to_buy:
        # 为每个持仓股票分配资金
        g.capital_unit=context.portfolio.portfolio_value/g.num_stocks
        # 买入在"待买股票列表"的股票
        order_target_value(stock_buy, g.capital_unit)