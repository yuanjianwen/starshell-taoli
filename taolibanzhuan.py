'''backtest
start: 2018-01-01 00:00:00
end: 2018-03-18 11:00:00
period: 1m
exchanges: [{"eid":"Futures_OKCoin","currency":"LTC"}]
'''
import numpy as np

def getPostion(ContractTypeA,directionA,ContractTypeB,directionB):
    exchange.SetContractType(ContractTypeA);
    exchange.SetMarginLevel(10);
    exchange.SetDirection(directionA);
    positionA = exchange.GetPosition();

    exchange.SetContractType(ContractTypeB);
    exchange.SetMarginLevel(10);
    exchange.SetDirection(directionB);
    positionB = exchange.GetPosition();

    return positionA[0].Amount,positionB[0].Amount

    pass

def getPrice(direction,contractType):
    exchange.SetDirection(direction)
    exchange.SetContractType(contractType)
    if direction == 'buy':
        depth = _C(exchange.GetDepth)
        return depth.Bids[1].Price

    if direction == 'sell':
        depth = _C(exchange.GetDepth)
        return depth.Asks[1].Price
    return False

def confirm_order(order_id,amount,ContractType,Direction):
    exchange.SetContractType(ContractType)
    exchange.SetDirection(Direction)

    timestamp = 0
    while True:
        try:
            order = exchange.GetOrder(order_id)
        except:
            try:
                orders = exchange.GetOrders()
                order_id = orders[0].Id
            except:
                return False
                pass
        try:
            order.Status
        except:
            continue
            pass
        #1是已经完成 2是已经取消 0是未完成
        if order.Status == 1 :
            return True
        if timestamp>50:
            Log('单号：'+str(order_id)+' 2秒未成交 撤单')
            exchange.CancelOrder(order_id)
            order = _C(exchange.GetOrder,order_id)
            Log(order)
            if order.Status == 2:
                Log('撤单成功')
                return False
            if order.Status == 1:
                Log('完全成交')
                return True
            Sleep(100)
        Sleep(100)
        timestamp += 1



    pass


def open_buy_order(price,number,direction):
    exchange.SetMarginLevel(10)
    exchange.SetContractType(direction)
    exchange.SetDirection('buy') #设置下单类型为开仓
    buy_open = exchange.Buy(price, number)

    return buy_open

def open_sell_order(price,number,direction):
    exchange.SetMarginLevel(10)
    exchange.SetContractType(direction)
    exchange.SetDirection('sell') #设置下单类型为开仓
    sell_open = exchange.Sell(price, number)

    return sell_open

def close_buy_order(price,number,direction):
    exchange.SetMarginLevel(10)
    exchange.SetContractType(direction)
    exchange.SetDirection('closebuy') #设置下单类型为开仓
    buy_close = exchange.Sell(price, number)

    return buy_close

def close_sell_order(price,number,direction):
    exchange.SetMarginLevel(10)
    exchange.SetContractType(direction)
    exchange.SetDirection('closesell') #设置下单类型为开仓
    sell_close = exchange.Buy(price, number)

    return sell_close






def main():
    timestamp = 0
    trigger_open ='inital'
    trigger_close ='inital'
    threshold_up = 0
    threshold_down = 0
    dif_array = []
    dif_mean = -50
    amount = 1 #合约交易张数，难度乘子
    directionA = 'this_week'
    directionB = 'quarter'
    record = 0
    step_add = 0.3
    upbond = 17
    while True:
        cmd = GetCommand()
        if cmd:
            Log(cmd)
            pass
        timestamp+=1
        position = exchange.GetPosition()
        status = ''
        positionA = 0
        positionB = 0
        try:
            positionA,positionB = getPostion(directionA,'buy',directionB,'sell')

            status+='多头仓位'+str(positionA)+' 空头仓位'+str(positionB) +' 第'+str(timestamp)+'轮询'

        except:
            status+='仓位0 '+' 第'+str(timestamp)+'轮询'
        if positionA != positionB:
                Log('仓位不均衡！！！！！')

        price_buy_directionA = getPrice("buy",directionA)#获取买一价，卖的时候用这个价格
        price_sell_directionA = getPrice("sell",directionA)#获取卖一价，买的时候用这个价格
        price_buy_directionB = getPrice("buy",directionB)#获取买一价，卖的时候用这个价格
        price_sell_directionB = getPrice("sell",directionB)#获取卖一价，买的时候用这个价格

        dif_array.append(price_sell_directionA - price_sell_directionB)


        step_add =  abs(price_sell_directionA - price_buy_directionB)*0.01



        if len(dif_array)>1000:
            del dif_array[0]
            dif_array_np = np.sort(dif_array)
            threshold_down = dif_array_np[int(len(dif_array_np)*0.0382)]#这些都是正数
            threshold_up = dif_array_np[int(len(dif_array_np)*0.9618)]
            dif_mean = dif_array_np[int(len(dif_array_np)*0.5)]
            #dif_mean = np.mean(np.array(dif_array))

        elif len(dif_array)<950:
            Sleep(200)
            continue

        status+=' 开仓监控跨期差价当周-季度= '+str(price_sell_directionA - price_buy_directionB)+' 平仓差价当周-季度= '+str(price_buy_directionA - price_sell_directionB)+' 平衡差价= '+str(dif_mean)+' 开仓需求差价= '+str(threshold_down-positionA*step_add)+' 平仓需求差价= '+str(threshold_up)+' 开仓控制:'+trigger_open+' 平仓控制:'+trigger_close



        #启动开仓，一张张开===================================================
        if  (price_sell_directionA - price_buy_directionB) < threshold_down - positionA*step_add and positionA<upbond:
            #Log('启动开仓'+str(price_sell_directionA - price_buy_directionB)+' '+str(threshold_up)+trigger_open)
            if trigger_open == 'inital' and trigger_close == 'inital':
                Log('启动开仓'+str(price_sell_directionA - price_buy_directionB)+' '+str(threshold_up)+trigger_open)
                resultA = open_buy_order(price_sell_directionA,amount,directionA)
                resultB = open_sell_order(price_buy_directionB,amount,directionB)
                record = price_sell_directionA - price_buy_directionB
                resultA = confirm_order(resultA,amount,directionA,'buy')
                resultB = confirm_order(resultB,amount,directionB,'sell')
                if resultA == False and resultB == True:
                    Log('次周开仓失败')
                    trigger_open = 'openA_fail'
                if resultA == True and resultB == False:
                    Log('季度开仓失败')
                    trigger_open = 'openB_fail'
                continue
            if trigger_open == 'openA_fail':
                resultA = open_buy_order(price_sell_directionA,amount,directionA)
                resultA = confirm_order(resultA,amount,directionA,'buy')
                if resultA == True:
                    trigger_open = 'inital'
            if trigger_open == 'openB_fail':
                resultB = open_sell_order(price_buy_directionB,amount,directionB)
                resultB = confirm_order(resultB,amount,directionB,'sell')
                if resultB == True:
                    trigger_open = 'inital'



        #启动平仓，一张张平===============================================================================
        if  price_buy_directionA - price_sell_directionB > threshold_up and positionA>0:
            #Log('启动平仓'+str(price_buy_directionA - price_sell_directionB)+' '+str(threshold_down)+trigger_close)
            if trigger_close == 'inital' and trigger_open == 'inital':
                Log('启动平仓'+str(price_buy_directionA - price_sell_directionB)+' '+str(threshold_down)+trigger_close)
                resultA = close_buy_order(price_sell_directionA,amount,directionA)
                resultB = close_sell_order(price_buy_directionB,amount,directionB)
                resultA = confirm_order(resultA,amount,directionA,'sell')
                resultB = confirm_order(resultB,amount,directionB,'buy')
                if resultA == False and resultB == True:
                    Log('次周平仓失败')
                    trigger_close = 'closeA_fail'
                if resultA == True and resultB == False:
                    Log('季度平仓失败')
                    trigger_close = 'closeB_fail'
                continue
            if trigger_close == 'closeA_fail':
                resultA = close_buy_order(price_sell_directionA,amount,directionA)
                resultA = confirm_order(resultA,amount,directionA,'sell')
                if resultA == True:
                    trigger_close = 'inital'
            if trigger_close == 'closeB_fail':
                resultB = close_sell_order(price_buy_directionB,amount,directionB)
                resultB = confirm_order(resultB,amount,directionB,'buy')
                if resultB == True:
                    trigger_close = 'inital'

        '''
        #启动开仓，一张张开===================================================
        if  price_buy_directionA - price_sell_directionB < threshold_down :

            if trigger == 'inital':
                resultA = open_buy_order(price_sell_directionA,amount,directionA)
                resultB = open_sell_order(price_buy_directionB,amount,directionB)
                record = price_sell_directionA - price_buy_directionB
                resultA = confirm_order(resultA,amount)
                resultB = confirm_order(resultB,amount)
                if resultA == False and resultB == True:
                    Log('次周开仓失败')
                    trigger = 'openA_fail'
                if resultA == True and resultB == False:
                    Log('季度开仓失败')
                    trigger = 'openB_fail'
                continue
            if trigger == 'openA_fail':
                resultA = open_buy_order(price_sell_directionA,amount,directionA)
                resultA = confirm_order(resultA,amount)
                if resultA == True:
                    trigger = 'inital'
            if trigger == 'openB_fail':
                resultB = open_sell_order(price_buy_directionB,amount,directionB)
                resultB = confirm_order(resultB,amount)
                if resultB == True:
                    trigger = 'inital'



        #启动平仓，一张张平===============================================================================
        if  (price_sell_directionA - price_buy_directionB) > threshold_up and position>0:
            if trigger == 'inital':
                resultA = close_buy_order(price_sell_directionA,amount,directionA)
                resultB = close_sell_order(price_buy_directionB,amount,directionB)
                resultA = confirm_order(resultA,amount)
                resultB = confirm_order(resultB,amount)
                if resultA == False and resultB == True:
                    Log('次周平仓失败')
                    trigger = 'closeA_fail'
                if resultA == True and resultB == False:
                    Log('季度平仓失败')
                    trigger = 'closeB_fail'
                continue
            if trigger == 'closeA_fail':
                resultA = close_buy_order(price_sell_directionA,amount,directionA)
                resultA = confirm_order(resultA,amount)
                if resultA == True:
                    trigger = 'inital'
            if trigger == 'closeB_fail':
                resultB = close_sell_order(price_buy_directionB,amount,directionB)
                resultB = confirm_order(resultB,amount)
                if resultB == True:
                    trigger = 'inital'
        '''
        LogStatus(status)
        #LogProfit(price_sell_this_week - price_buy_next_week)
        Sleep(500)
