import datetime
import math
from ib_insync import *


class IbTrade(object):
    def __init__(self):
        self.absolute_stop = 0.95
        self.absolute_depreciation = 1.05
        self.single_stop = 0.01
        self.valid_signal = 5
        self.max_hold = 10
        self.number = 1
        self.contract = Forex('EURUSD')
        self.slip_point = 0.00001
        self.dormant_time = 1
        self.signal_history = list()
        self.open_difference = 0.1
        self.bar_setting = dict(durationStr='30 D', barSizeSetting='1 hour')
        self.ib = IB()
        self.account = dict()
        self.tick = None
        self.bars = None
    
    def update_account(self):
        for m in self.ib.accountValues():
            self.account[m.tag] = m
        print(self.account)
        
    def get_tick(self):
        self.ib.reqMktData(self.contract, '', False, False)
        self.tick = self.ib.ticker(self.contract)
        print(self.tick)

    def get_historydata(self):
        self.bars = self.ib.reqHistoricalData(self.contract, endDateTime='',
                                              durationStr=self.bar_setting['durationStr'],
                                              barSizeSetting=self.bar_setting['barSizeSetting'], 
                                              whatToShow='MIDPOINT', useRTH=True)
        print(self.bars)

    def stop_loss(self):
        pos = self.ib.positions()[0]
        netliquidation = float(self.account['NetLiquidation'].value)
        tick = self.tick.marketPrice()
        if abs(tick - pos.avgCost) > netliquidation * self.single_stop:
            return True
        return False

    def risk(self):
        netliquidation = float(self.account['NetLiquidation'].value)
        cash_balance = float(self.account['CashBalance'].value)
        print(netliquidation,cash_balance)
        ratio = cash_balance/netliquidation
        if ratio > self.absolute_depreciation or  ratio < self.absolute_stop:
            return True
        return False

    def check_pricemargin(self):
        #return True
        close = self.bars[-1].close
        if abs(close-self.tick.marketPrice()) > self.open_difference:
            return False
        return True

    def check_signal(self):
        #return True
        if not self.signal_history:
            return False
        signal = self.signal_history[-1]
        count=0
        for m in self.signal_history[::-1]:
            if count > self.valid_signal:
                return False
            if signal[0].action != m[0].action:
                return True
            count += 1
            #print(count)

    def check_hold(self):
        pos = self.ib.positions()[0]
        if pos.position > 10:
            return False
        return True

    def algo(self):
        order = MarketOrder('BUY', self.number)
        self.signal_history.append((order,False))

    def place_order(self):
        if self.risk() or self.stop_loss():
            pos = self.ib.positions()[0]
            print(pos)
            order = MarketOrder('SELL', pos.position)
            if pos.position < 0:
                order = MarketOrder('BUY', -pos.position)
            self.ib.placeOrder(pos.contract, order)
        if self.check_signal() and self.check_pricemargin() and self.check_hold():
            #if self.signal_history:
                #return
            #print(self.signal_history)
            signal = self.signal_history[-1]
            trade = self.ib.placeOrder(self.contract, signal[0])
            self.ib.sleep(1)
            print(trade)
        else:
            print('The signal has been ignored!\n')


    def run(self):
        import pandas
        self.ib.connect('127.0.0.1', 7497, clientId=0)
        self.update_account()
        self.get_historydata()
        while True:
            now=datetime.datetime.now()
            if '00' == now.strftime('%M'):
                self.get_historydata()
            self.get_tick()
            if not math.isnan(self.tick.marketPrice()):
                self.algo()
                self.place_order()
            self.ib.sleep(self.dormant_time)
    
    def stop(self):
       self.ib.disconnect()
       exit()

def main():
    ib = IbTrade()
    ib.run()

if __name__=='__main__':
    main()