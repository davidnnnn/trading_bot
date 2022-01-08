from account import Account
from stock import Stock
from analyser import Analyser
from EMA import EMA
from MACD import MACD
# ------------------------------------------------------
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
#-------------------------------------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import sys


def strat_EMA(account: Account, data, symbol: str):
    '''
    This startegy uses EMA_fast(timeperiod = 12) and EMA_slow(timeperiod = 26).
    <data> is EMA_fast and EMA_slow concated with a standard stock price table
    Return a dictionary of lookForSelling point and entry point, point = {timestamp: (amount, operation"buy/lookForSell")}
    '''
    # create the dictionary for return
    entry_points = {}
    # look at the earliest recorded bar.
    last_bar_index = len(data.index) - 1
    # Number of buys
    buy_in = 0
    for i in range(last_bar_index - 1, -1, -1):
        # var about current situation
        stock_current_bar = data.iloc[i]["4. close"]
        stock_previous_bar = data.iloc[i + 1]["4. close"]
        EMA_fast_current_bar = data.iloc[i]["EMA_fast"]
        EMA_fast_previous_bar = data.iloc[i + 1]["EMA_fast"]
        EMA_slow_current_bar = data.iloc[i]["EMA_slow"]
        EMA_slow_previous_bar = data.iloc[i + 1]["EMA_slow"]
        # if we have bottom divergence
        if divergence(stock_current_bar, stock_previous_bar, EMA_fast_current_bar, EMA_fast_previous_bar) == "bottom divergence" or\
           divergence(stock_current_bar, stock_previous_bar, EMA_slow_current_bar, EMA_slow_previous_bar) == "bottom divergence" and buy_in < 2:
           # and we have fast crosses bottom from below
            if EMA_fast_current_bar >= EMA_slow_current_bar and EMA_fast_previous_bar <= EMA_slow_previous_bar and buy_in < 2:
                # check how much share I can buy
                share = int(account.get_starting_capital() /
                            2 / stock_current_bar)
                # acutal money spent on buying stock
                spent = share * stock_current_bar
                # add the buying point to the list
                entry_points[data.index[i]] = (spent, "buy")
                # deduct the capital from the bank account
                account.withdraw_captial(spent)
                # add the aquired share to the account
                account.acquire_equity(symbol, quantity=share)
                # note there is 1 buy in
                buy_in += 1
        elif EMA_fast_current_bar <= EMA_slow_current_bar and EMA_fast_previous_bar >= EMA_slow_previous_bar:
            try:
                # lookForSell all shares of this stock under this account
                share = account.forfeit_equity(symbol)
                capital_gained = share * stock_current_bar
                # add the lookForSelling point
                entry_points[data.index[i]] = (share, "lookForSell")
                # store gained capital into the account
                account.deposit_capital(capital_gained)
                # reset buyin
                buy_in = 0
                # print out the current revenue after lookForSelling
                print(data.index[i], account.revenue())
            except KeyError:
                pass
        else:
            pass
    return entry_points


def EMA_cross(data: pd.DataFrame):
    '''
    @return {TimeStamp: (bool, str)}
    '''
    result = {}
    last_item_index = len(data.index) - 1
    for i in range(last_item_index - 1, -1, -1):
        EMA_fast = data.iloc[i]['EMA_fast']
        EMA_slow = data.iloc[i]['EMA_slow']
        EMA_fast_previous = data.iloc[i + 1]['EMA_fast']
        EMA_slow_previous = data.iloc[i + 1]['EMA_slow']
        # print(EMA_fast, EMA_slow, EMA_fast_previous, EMA_slow_previous)
        # When is crossing
        if EMA_fast > EMA_slow and EMA_fast_previous < EMA_slow_previous:
            result[data.index[i]] = (True, "bottom cross")

    return result


def startegy_1(account: Account, symbol: str, data: pd.DataFrame, stop_lost_rate = 0.01, trailing_lost_ratio = 1.5):
    trailing_stop_rate = stop_lost_rate * trailing_lost_ratio
    last_item_index = len(data.index) - 1
    result = {"Operation": ("share", "current_close", "total amount")}
    isDecreasing = False
    isIncreasing = False
    lookForCross = False
    lookForSell = False
    buy = False
    sell = False
    last_purchase = ()
    number_of_local_divergence = 0
    iloc_local_min = []
    iloc_local_max = []
    for i in range(last_item_index - 1, -1, -1):
        current_close = data.iloc[i]['4. close']
        current_MACD_Hist = data.iloc[i]['MACD_Hist']
        current_low = data.iloc[i]['3. low']
        previous_close = data.iloc[i + 1]['4. close']
        previous_MACD_Hist = data.iloc[i + 1]['MACD_Hist']
        previous_low = data.iloc[i + 1]['3. low']
        EMA_fast = data.iloc[i]['EMA_fast']
        EMA_slow = data.iloc[i]['EMA_slow']
        EMA_fast_previous = data.iloc[i + 1]['EMA_fast']
        EMA_slow_previous = data.iloc[i + 1]['EMA_slow']
        # find decreasing trend
        if current_low < previous_low and not lookForCross and not lookForSell:
            isDecreasing = True
        # find divergence
        elif current_low > previous_low and isDecreasing and not lookForCross and not lookForSell:
            isDecreasing = False
            # store the time and the macd_hist value if this is the first one
            if len(iloc_local_min) == 0:
                # stores number index and MACD_Hist
                iloc_local_min.append((i + 1, previous_MACD_Hist))
            # if there is already a recorded minimum
            elif len(iloc_local_min) == 1:
                # check if the second bar's value is lower than the old one
                if data.iloc[iloc_local_min[0][0]]['3. low'] > current_low:
                    # check if the second bar's MACD_Hist value is greater than the previous one
                    if iloc_local_min[0][1] < current_MACD_Hist:
                        # start looking for cross
                        lookForCross = True
                        # append the second point to the iloc min
                        iloc_local_min.append((i + 1, previous_MACD_Hist))
                        # add the decision to result
                        result[data.index[iloc_local_min[0][0] + 1]] = ("divergence_point_1_previous", data.iloc[iloc_local_min[0][0]+1]['3. low'], data.iloc[iloc_local_min[0][0] + 1]["MACD_Hist"])
                        result[data.index[iloc_local_min[0][0]]] = ("divergence_point_1", data.iloc[iloc_local_min[0][0]]['3. low'], iloc_local_min[0][1])
                        result[data.index[iloc_local_min[0][0] - 1]] = ("divergence_point_1_next", data.iloc[iloc_local_min[0][0]-1]['3. low'], data.iloc[iloc_local_min[0][0] - 1]["MACD_Hist"])
                        result[data.index[iloc_local_min[1][0] + 1]] = ("divergence_point_2_previous", data.iloc[iloc_local_min[1][0]+1]['3. low'], data.iloc[iloc_local_min[1][0] + 1]["MACD_Hist"])
                        result[data.index[iloc_local_min[1][0]]] = ("divergence_point_2", data.iloc[iloc_local_min[1][0]]['3. low'], iloc_local_min[1][1])
                        result[data.index[iloc_local_min[1][0] - 1]] = ("divergence_point_2_next", data.iloc[iloc_local_min[1][0]-1]['3. low'], data.iloc[iloc_local_min[1][0] - 1]["MACD_Hist"])
                    else:
                    	# abandon the first local min and use the current one
                    	iloc_local_min[0] = (i + 1, previous_MACD_Hist)
                else:
                    # abandon the first local min and use the current one
                    iloc_local_min[0] = (i + 1, previous_MACD_Hist)
        # look for cross
        elif lookForCross and EMA_fast > EMA_slow and EMA_fast_previous < EMA_slow_previous and not lookForSell:
            lookForCross = False
            result[data.index[i + 2]] = ("cross_previous", EMA_fast, EMA_slow, EMA_fast_previous, EMA_slow_previous)
            result[data.index[i + 1]] = ("cross", EMA_fast, EMA_slow, EMA_fast_previous, EMA_slow_previous)
            result[data.index[i]]     = ("cross_next", EMA_fast, EMA_slow, EMA_fast_previous, EMA_slow_previous)
            # Flag next bar as buy
            buy = True
        # buy at this bar
        elif buy:
            buy = False
            iloc_local_min = []
            # check how much share I can buy
            share = int(account.get_current_capital() / current_close)
            # acutal money spent on buying stock
            spent = share * current_close
            # deduct the capital from the bank account
            account.withdraw_captial(spent)
            # add the aquired share to the account
            account.acquire_equity(symbol, quantity=share)
            result[data.index[i]] = (
                "buy bottom divergence", share, current_close, spent)
            last_purchase = ("buy bottom divergence",
                             share, current_close, spent)
            lookForSell = True
        # stop trailing
        elif lookForSell and account.equity[symbol] * last_purchase[2] * (1 + trailing_stop_rate) <= last_purchase[1] * current_close:
            lookForSell = False
            sell = True
            result[data.index[i]] = ("decide to stop trailing", share, current_close)
       	# stop lost
        elif lookForSell and account.equity[symbol] * last_purchase[2] * (1 - stop_lost_rate) > last_purchase[1] * current_close:
            lookForSell = False
            sell = True
            result[data.index[i]] = ("decide to stop lost", share, current_close)
        # find increasing trend
        elif lookForSell and current_close > previous_close:
            isIncreasing = True
        # find top divergence if there is already a increasing trend
        elif lookForSell and current_close < previous_close and isIncreasing:
            isIncreasing = False
            if len(iloc_local_max) == 0:
                iloc_local_max.append((i + 1, previous_MACD_Hist))
            elif len(iloc_local_max) == 1:
                # check if the second bar's value is greater than the old one
                if data.iloc[iloc_local_max[0][0]]['4. close'] < current_close:
                    # check if the second bar's MACD_Hist value is lower than the previous one
                    if iloc_local_max[0][1] > current_MACD_Hist:
                        # flag next bar as selling
                        sell = True
                        lookForSell = False
                        # append the second point to the iloc min
                        iloc_local_max.append((i + 1, previous_MACD_Hist))
                    else:
                        # abandon the first local min and use the current one
                        iloc_local_max[0] = (i + 1, previous_MACD_Hist)
                else:
                    # abandon the first local min and use the current one
                    iloc_local_max[0] = (i + 1, previous_MACD_Hist)
        # sell at this bar
        elif sell:
            sell = False
            # sell all shares of this stock under this account
            share = account.forfeit_equity(symbol)
            capital_gained = share * current_close
            # add the selling point
            result[data.index[i]] = (
                "sell top divergence", share, current_close, capital_gained)
            # store gained capital into the account
            account.deposit_capital(capital_gained)
            # reset last_purchase
            last_purchase = ()
            # reset iloc_local_max
            iloc_local_max = []
    return result

def get_equity_value(time_series: TimeSeries, holdings: dict):
	values = 0
	for symbol in holdings.keys():
		stock_temp = Stock(ts, symbol, interval = "15min")
		values += stock_temp.data.iloc[0]['4. close'] * holdings[symbol]
	return values

def evaluate(symbol: str, ts: TimeSeries, ta: TechIndicators, stop_lost_rate = 0.01, trailing_lost_ratio = 2.5):
    virtual_account = Account(100000)
    stock = Stock(ts, symbol, interval="15min")
    EMA_fast = EMA(ta, symbol, "15min", time_period=12)
    EMA_slow = EMA(ta, symbol, "15min", time_period=26)
    macd = MACD(ta, symbol, "15min", time_period=9)
    # print(stock.data)
    # print(EMA_fast.data)
    # print(EMA_slow.data)
    # concating tables
    frames = [stock.data, EMA_fast.data]
    result = pd.concat(frames, axis=1, join="inner").rename(
        columns={"EMA": "EMA_fast"})
    result = pd.concat([result, EMA_slow.table()], axis=1,
                       join="inner").rename(columns={"EMA": "EMA_slow"})
    frames = [result, macd.table()]
    result = pd.concat(frames, axis=1, join="inner")
    '''
	# writing result to data base
	conn = sqlite3.connect('testing_data.db')
	c = conn.cursor()
	result.to_sql('EMA+macd', conn, if_exists='replace')
	'''
    print(result)
    # time zone is US Eastern
    print(stock.meta_data)
    # print all the operating points
    points = startegy_1(virtual_account, stock.get_symbol(), result, stop_lost_rate = stop_lost_rate, trailing_lost_ratio = trailing_lost_ratio)
    count = 0
    for key in points.keys():
        print(key, points[key])
        if points[key][0] == "buy bottom divergence":
    	    count += 1
    print(count)
    print("gain: " + str(virtual_account.revenue() + get_equity_value(ts, virtual_account.equity)))

def evaluate_2_year(symbol: str, ts: TimeSeries, ta: TechIndicators, stop_lost_rate = 0.01, trailing_lost_ratio = 2.5):
    virtual_account = Account(100000)
    stock = Stock(ts, symbol, interval="15min")
    stock.get_2_year_data()
    EMA_fast = EMA(stock.data, time_period = 12)
    EMA_fast = EMA_fast.dropna()
    EMA_slow = EMA(stock.data, time_period = 26)
    EMA_slow = EMA_slow.dropna()
    macd = MACD(ta, symbol, "15min", time_period=9)
    # print(stock.data)
    # print(EMA_fast.data)
    # print(EMA_slow.data)
    # concating tables
    frames = [stock.data, EMA_fast.data]
    result = pd.concat(frames, axis=1, join="inner").rename(
        columns={"EMA": "EMA_fast"})
    result = pd.concat([result, EMA_slow.table()], axis=1,
                       join="inner").rename(columns={"EMA": "EMA_slow"})
    frames = [result, macd.table()]
    result = pd.concat(frames, axis=1, join="inner")
    '''
	# writing result to data base
	conn = sqlite3.connect('testing_data.db')
	c = conn.cursor()
	result.to_sql('EMA+macd', conn, if_exists='replace')
	'''
    print(result)
    # time zone is US Eastern
    print(stock.meta_data)
    # print all the operating points
    points = startegy_1(virtual_account, stock.get_symbol(), result, stop_lost_rate = stop_lost_rate, trailing_lost_ratio = trailing_lost_ratio)
    count = 0
    for key in points.keys():
        print(key, points[key])
        if points[key][0] == "buy bottom divergence":
            count += 1
    print(count)
    print("gain: " + str(virtual_account.revenue() + get_equity_value(ts, virtual_account.equity)))

def ave(list_in: list):
	'''
	SMA = (A1+A2+A3...+An)/n
	'''
	total = 0
	result = 0
	for each in list_in:
		total += each
	result = total/len(list_in)
	return result

def EMA_tail_recursive(data, result, index = 0, time_period = 12):
	'''
	data and result have same number of columns, result is empty dataframe with "EMA" as its column name
	calculate the EMA recursively
	'''
	this_bar = np.nan
	print("current index:" + str(index))
	# start from the earlist bar
	if index == len(data.index) - 1 - time_period:
		# create a list to of ignored data
		temp = []
		for i in range(len(data.index) - 1, len(data.index) - 1 - time_period, -1):
			temp.append(data.iloc[i])
		# set ave value to result
		this_bar = ave(temp)
		result.loc[data.index[index], "EMA"] = ave(temp)
	else:
		# set EMA value to result
		multiplier = 2/(time_period+1)
		this_bar = (data.iloc[index]['4. close']) * multiplier + EMA(data, result, index = index + 1, time_period = time_period) * (1 - multiplier)
		result.loc[data.index[index], "EMA"] = this_bar
	# return this bar's EMA value
	return this_bar
'''
def EMA(data, time_period = 12):
	# create empty dataframe
	result = pd.DataFrame(index = data.index, columns = ["EMA"], dtype = float)
	# find the earlist closing price we can use
	first_bar_index = len(data.index) - 1 - time_period
	# apply ave (SMA) to it
	# create a list of earlier bars
	temp = []
	for i in range(len(data.index) - 1, len(data.index) - 1 - time_period, -1):
		temp.append(data.iloc[i]["close"])
	result.iat[first_bar_index, 0] = ave(temp)
	# data is indexed from today to history as 0 to +infinity.
	# calculating from the second avaliable EMA data point
	for i in range(first_bar_index - 1, -1, -1):
		multiplier = 2/(time_period + 1)
		value = (data.iloc[i]['close']) * multiplier + result.iloc[i + 1]["EMA"] * (1 - multiplier)
		result.iat[i, 0] = value
	return result
'''

if __name__ == "__main__":
    # api key imported from a text file, just the key, no letters
    f = open("Alpha_Vantage_premium_key.txt", r)
    apiKey = f.read()
    f.close()
    ts = TimeSeries(key=apiKey, output_format="pandas")
    ta = TechIndicators(key=apiKey, output_format="pandas")
    # pd.options.display.max_rows = 9999
    evaluate("BGFV", ts, ta, stop_lost_rate = 0.02)
    #evaluate("SPCE", ts, ta, stop_lost_rate = 0.002, trailing_lost_ratio = 2.5)
    '''
    virtual_account = Account(100000)
    stock = Stock(ts, "AAPL", interval="15min", extended = True, slice = "year1month1")
    stock.get_2_year_data()
    # stock.get_2_year_data()
    print(stock.data)
    EMA_fast = EMA(stock.data, time_period = 12)
    EMA_fast = EMA_fast.dropna()
    print(EMA_fast)
    '''
    # print(stock.data.iloc[len(stock.data.index)-1])
    #evaluate("AAPL", ts, ta)
    #evaluate("NVDA", ts, ta)
    #evaluate("U", ts, ta, stop_lost_rate = 0.005)