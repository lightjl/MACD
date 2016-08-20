import talib
import numpy as np
import pandas as pd
'''
================================================================================
总体回测前
================================================================================
'''
# 初始化函数，设定要操作的股票、基准等等
# 总体回测前要做的事情
# 注意去掉停牌的数据，算MACD值时
def initialize(context):
    set_params()                             # 设置策略常量
    set_variables()                          # 设置中间变量
    set_backtest()                           # 设置回测条件

#1 
#设置策略参数
def set_params():
    g.tc = 1                                                # 调仓天数
    g.num_stocks = 10                                       # 每次调仓选取的最大股票数量
    g.stocks=get_index_stocks('000300.XSHG')                # 设置沪深300为初始股票池
    g.per = 0.1                                             # EPS增长率不低于0.25
    g.df_hold = pd.DataFrame(columns=['lastdo', 'price'])   # 维护持有df

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
        
        g.feasible_stocks = ['000001.XSHE', '000002.XSHE', '000004.XSHE', '000005.XSHE', '000006.XSHE', '000007.XSHE', '000008.XSHE', '000009.XSHE']
        g.feasible_stocks = set_feasible_stocks(g.stocks,context)
        # g.feasible_stocks = ['000001.XSHE']
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
    st_stocks = list(df_st_info.index[df_st_info.is_st == True])
    # log.info(st_stocks)没有ST的
    unsuspened_stocks = list(df_st_info.index[df_st_info.is_st == False])
    return unsuspened_stocks

# 过滤掉当日停牌的股票
# 输入：initial_stocks为list类型,表示股票列表； context（见API）
# 输出：unsuspened_stocks为list类型，表示当日未停牌的股票
def remove_paused_stock(initial_stocks,context):
    # 判断初始股票池的股票是否停牌，返回list
    paused_info = []
    current_data = get_current_data()
    for i in initial_stocks:
        paused_info.append(current_data[i].paused)
    df_paused_info = pd.DataFrame({'paused_info':paused_info},index = initial_stocks)
    unsuspened_stocks =list(df_paused_info.index[df_paused_info.paused_info == False])
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
        df_can_buy = stocks_can_buy(context, g.feasible_stocks)
        
        '''
        # test 
        df_can_buy = ['000001.XSHE']
        df_list_can_buy = pd.DataFrame(index=list_can_buy,columns=['todo', 'done'])
            index       todo    done
            000001.XSHE buy     notdo
            todo buy, add1, add2, stop, sell
            买，加1，加2，止损，清仓
        df_list_can_buy.loc['000001.XSHE', 'todo'] = 'buy'
        log.info(df_can_buy)
        # 000001.XSHE  buy  NaN
        '''
        # data.drop(n)可以删除第i行
        # 待卖出的股票，list类型
        df_to_sell = stocks_to_sell(context)
        # 需买入的股票
        df_to_buy = pick_buy_df(context, df_can_buy, df_to_sell)
        # df_to_buy = df_can_buy
        # 卖出操作
        
        # 测试
        # list_to_sell = g.df_hold.index
        
        sell_operation(context, df_to_sell)
        # 买入操作
        buy_operation(context, df_to_buy)
        
        
    g.if_trade = False
    
def stocks_can_buy(context, list_stock):
    df_can_buy = pd.DataFrame(columns=['todo', 'done'])
    
    for i in list_stock:
        close_data = attribute_history(i, 100, unit='1d', fields=('close'))
        DIF, DEA, MACD = mmacd(close_data['close'].values)
        open_data = attribute_history(i, 5, unit='1d', fields=('open'))
        # DIF 上穿 0 轴 并且 MACD 红柱发散
        # todo DIF已上穿若干天后，MACD 红柱发散
        # log.info('DIF', DIF, 'MACD', MACD)
        if DIF[-2] < 0 and DIF[-1] > 0 and MACD[-1] > MACD[-2] and MACD[-2] > 0 \
            and close_data['close'][-1] > open_data['open'][-1]:
            buy_list = []
            buy_list.append(i)
            if i in g.df_hold.index and close_data['close'][-1] > g.df_hold.loc[i, 'price']:
                # 买->加1->加2；去掉stop
                if g.df_hold.loc[i,'lastdo'] == 'buy':
                    str_do = 'add1'
                    df_now = pd.DataFrame([[str_do, 'notdo']], index=buy_list, columns=['todo', 'done'])
                    df_can_buy = df_can_buy.append(df_now)
                elif g.df_hold.loc[i,'lastdo'] == 'add1':
                    str_do = 'add2'
                    df_now = pd.DataFrame([[str_do, 'notdo']], index=buy_list, columns=['todo', 'done'])
                    df_can_buy = df_can_buy.append(df_now)
                elif g.df_hold.loc[i,'lastdo'][0:4] == 'stop':
                    str_do = 'fromstop'
                    df_now = pd.DataFrame([[str_do, 'notdo']], index=buy_list, columns=['todo', 'done'])
                    df_can_buy = df_can_buy.append(df_now)
                    
            else:
                df_now = pd.DataFrame([['buy', 'notdo']], index=buy_list, columns=['todo', 'done'])
                df_can_buy = df_can_buy.append(df_now)
        # 加仓
        '''
        elif MACD[-2]<0 and MACD[-1]>0:
            buy_list = []
            if i in g.df_hold.index:
                buy_list.append(i)
                if g.df_hold.loc[i,'lastdo'] == 'buy':
                    str_do = 'add1'
                    df_can_buy = df_can_buy.append(
                        pd.DataFrame([[str_do, 'notdo']], index=buy_list, columns=['todo', 'done'])
                        )
                elif g.df_hold.loc[i,'lastdo'] == 'add1':
                    str_do = 'add2'
                    df_can_buy = df_can_buy.append(
                        pd.DataFrame([[str_do, 'notdo']], index=buy_list, columns=['todo', 'done'])
                        )
                elif g.df_hold.loc[i,'lastdo'][0:4] == 'stop':
                    str_do = 'fromstop'
                    df_now = pd.DataFrame([[str_do, 'notdo']], index=buy_list, columns=['todo', 'done'])
                    df_can_buy = df_can_buy.append(df_now)
        '''
            
    
    return df_can_buy
    
def mmacd(price, fastperiod=12, slowperiod=26, signalperiod=9):
    
    return talib.MACD(price, fastperiod=12, slowperiod=26, signalperiod=9)
    
#8
# 获得卖出信号
# 输入：context（见API文档）, list_to_buy为list类型，代表待买入的股票
# 输出：list_to_sell为list类型，表示待卖出的股票
def stocks_to_sell(context):
    df_to_sell = pd.DataFrame(columns=['todo'])
    
    if g.df_hold.empty:
        return df_to_sell
    
    # 过滤掉当日停牌的股票
    list_can_sell = remove_paused_stock(g.df_hold.index,context)
    
    for i in list_can_sell:
        close_data = attribute_history(i, 100, unit='1d', fields=('close'))
        DIF, DEA, MACD = mmacd(close_data['close'].values)
        
        # 跌5个点止损        
        if g.df_hold.loc[i,'price']*0.95 >= close_data['close'][-1]:
            # 止损条件1
            sell_list = []
            sell_list.append(i)
            # 止损2次清仓 
            if g.df_hold.loc[i, 'lastdo'][0:4] == 'stop':
                df_now = pd.DataFrame([['sell']], index=sell_list, columns=['todo'])
                df_to_sell = df_to_sell.append(df_now)
                #log.info('跌价清仓', df_to_sell)
                
            else:
                df_now = pd.DataFrame([['stop']], index=sell_list, columns=['todo'])
                df_to_sell = df_to_sell.append(df_now)
                #log.info('跌价止损', df_to_sell)
                
            
        if (MACD[-2]>=0 and MACD[-1]<0):
            # 止损条件2 MACD下穿
            sell_list = []
            sell_list.append(i)
            if i in df_to_sell.index:
                # 已达成止损条件1,直接清仓
                df_to_sell.loc[i, 'todo'] = 'sell'
                #log.info('跌价又MACD', df_to_sell)
                continue
            if g.df_hold.loc[i, 'lastdo'][0:4] == 'stop':
                df_now = pd.DataFrame([['sell']], index=sell_list, columns=['todo'])
                df_to_sell = df_to_sell.append(df_now)
                #log.info('MACD清仓', df_to_sell)
                
            else:
                df_now = pd.DataFrame([['stop']], index=sell_list, columns=['todo'])
                df_to_sell = df_to_sell.append(df_now)
                #log.info('MACD止损', df_to_sell)
        
        if context.portfolio.positions[i].avg_cost *0.9 >= close_data['close'][-1]:
            #亏损 10% 清仓
            sell_list = []
            sell_list.append(i)
            if i in df_to_sell.index:
                # 已达成止损条件动作改为清仓
                df_to_sell.loc[i, 'todo'] = 'sell'
                #log.info('跌价又MACD', df_to_sell)
                continue
            df_now = pd.DataFrame([['sell']], index=sell_list, columns=['todo'])
            df_to_sell = df_to_sell.append(df_now)
        #log.info(df_to_sell)
        
    return df_to_sell
    
# 获得买入的list_to_buy
# 输入list_can_buy 为list，可以买的队列
# 输出list_to_buy 为list，买入的队列
def pick_buy_df(context, df_can_buy, df_to_sell):
    df_to_buy = pd.DataFrame(columns=['todo', 'done'])
    # 要买数 = 可持数 - 持仓数 + 要卖数
    # todo 要买数仍要修正
    if len(df_to_sell):
        len_sell = len(df_to_sell.index)
    else:
        len_sell = 0
    buy_num = g.num_stocks - len(context.portfolio.positions.keys()) + len_sell
    if buy_num <= 0:
        return df_to_buy
    # 得到一个dataframe：index为股票代码，data为相应的PEG值
    # 排序--------------------------------------------------------------------------------排序 

    return df_can_buy[0:buy_num]


'''
    全仓买卖
    todo 仓位控制
'''    
#9
# 执行卖出操作
# 输入：list_to_sell为list类型，表示待卖出的股票
# 输出：none
def sell_operation(context, df_to_sell):
    # context.portfolio.positions 当前持有的股票(包含不可卖出的股票), 一个dict, key是股票代码, value是Position对象
    # context.portfolio.positions[stock_sell]
    # total_amount 总持有股票数量, 包含可卖出和不可卖出部分
    # sellable_amount 可卖出数量
    # price 最新价格

    for stock_sell in df_to_sell.index:
        if g.df_hold.loc[stock_sell, 'lastdo'] == 'sell':
            # 清仓上次没清的
            dict_stock = context.portfolio.positions[stock_sell]
            order_now = order_target(stock_sell, 0)
            if not order_now is None:
                if dict_stock.total_amount == dict_stock.sellable_amount:
                    g.df_hold = g.df_hold.drop(stock_sell)
                else:
                    # 没清完，下次清
                    g.df_hold.loc[stock_sell, 'lastdo'] = 'sell'
            continue
            
        if df_to_sell.loc[stock_sell, 'todo'][0:4] == 'stop':
            # 止损
            dict_stock = context.portfolio.positions[stock_sell]
            sell_num = min(dict_stock.total_amount/2, dict_stock.sellable_amount)
            order_now = order_target(stock_sell, sell_num)
            
            if not order_now is None:
                g.df_hold.loc[stock_sell, 'lastdo'] = 'stop' + g.df_hold.loc[stock_sell, 'lastdo']
                g.df_hold.loc[stock_sell, 'price'] = 0
                
        elif df_to_sell.loc[stock_sell, 'todo'][0:4] == 'sell':
            # 清仓
            dict_stock = context.portfolio.positions[stock_sell]
            order_now = order_target(stock_sell, 0)
            if not order_now is None:
                if dict_stock.total_amount == dict_stock.sellable_amount:
                    g.df_hold = g.df_hold.drop(stock_sell)
                else:
                    # 没清完，下次清
                    g.df_hold.loc[stock_sell, 'lastdo'] = 'sell'
                

  
#10
# 执行买入操作
# 输入：context(见API)；list_to_buy为list类型，表示待买入的股票
# 输出：none
def buy_operation(context, df_to_buy):
    
    for stock_buy in df_to_buy.index:
        # 为每个持仓股票分配资金
        g.capital_unit=context.portfolio.portfolio_value/g.num_stocks
        # 买入在"待买股票列表"的股票
        if df_to_buy.loc[stock_buy,'todo'] == 'buy':
            order_now = order_target_value(stock_buy, g.capital_unit)
            if not order_now is None:
                list_now = []
                list_now.append(stock_buy)
                df_now = pd.DataFrame([['buy', order_now.price]], index=list_now, columns=['lastdo', 'price'])
                # price 是买入价，并不是成本价
                g.df_hold = g.df_hold.append(df_now)
                # log.info(g.df_hold)
        elif df_to_buy.loc[stock_buy,'todo'] == 'add1':
            # 加仓
            order_now = order_target_value(stock_buy, g.capital_unit*2)
            if not order_now is None:
                # price 是买入价，并不是成本价
                g.df_hold.loc[stock_buy, 'lastdo'] = 'add1'
                g.df_hold.loc[stock_buy, 'price'] = order_now.price
        elif df_to_buy.loc[stock_buy,'todo'] == 'add2':
            # 加2仓
            order_now = order_target_value(stock_buy, g.capital_unit*2.5)
            if not order_now is None:
                # price 是买入价，并不是成本价
                g.df_hold.loc[stock_buy, 'lastdo'] = 'add2'
                g.df_hold.loc[stock_buy, 'price'] = order_now.price
        elif df_to_buy.loc[stock_buy,'todo'] == 'fromstop':
            #回仓
            dict_stock = context.portfolio.positions[stock_buy]
            g.df_hold.loc[stock_buy, 'lastdo'] = g.df_hold.loc[stock_buy, 'lastdo'][4:]
            order_now = order_target(stock_buy, dict_stock.total_amount*2)
        #log.info(g.df_hold)