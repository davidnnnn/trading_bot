from alpha_vantage.timeseries import TimeSeries
import pandas as pd
'''
-------------------import environment--------------------------
'''
class Stock:

    def __init__(self, time_series: TimeSeries, symbol: str, interval="15min", outputsize="full", extended = False, slice = "year1month1"):
        if extended:
            self.__symbol = symbol
            self.__interval = interval
            self.get_intraday_extended(slice = slice)
        else:
            self.__symbol = symbol
            self.__interval = interval
            self.data, self.meta_data = time_series.get_intraday(symbol, interval, outputsize)

    def get_intraday_extended(self , slice='year1month1'):
        '''
        slice can be year1month1, year1month2.....year2month	12
        set data to the specified time_period
        time_series for intraday_extended can only be .cvs format
        it is not suggesting to put this function in a loop
        '''
        # download the csv
        ticker = self.__symbol
        interval = self.__interval
        date = slice
        # api key imported from a text file, just the key, no letters
        f = open("Alpha_Vantage_premium_key.txt", r)
        apiKey = f.read()
        f.close()
        url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&symbol='+ticker+'&interval='+interval+'&slice='+date+'&apikey='+apiKey+'&datatype=csv&outputsize=full'
        self.data = pd.read_csv(url)
        self.data.set_index('time', inplace = True)

    def get_2_year_data(self):
        num_year = 2
        num_month  = 12
        for year in range(1, num_year+1):
            for month in range(1, num_month+1):
                ticker = self.__symbol
                interval = self.__interval
                date = "year" + str(year) + "month" + str(month)
                # api key imported from a text file, just the key, no letters
                f = open("Alpha_Vantage_premium_key.txt", r)
                apiKey = f.read()
                f.close()
                url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&symbol='+ticker+'&interval='+interval+'&slice='+date+'&apikey='+apiKey+'&datatype=csv&outputsize=full'
                temp_data = pd.read_csv(url)
                temp_data.set_index('time', inplace = True)
                frames = [self.data, temp_data]
                self.data = pd.concat(frames)

    def get_close_column(self):
        return self.data['4. close']

    def get_symbol(self):
        return self.__symbol

    def get_interval(self):
        return self.__interval

    def last_bar_index(self) -> float:
        return len(self.data.index) - 1

    def previous_bar(self, current: int):
        time_stamp_index = self.data.index[current + 1]
        return self.data.loc[time_stamp_index]

    def current_bar(self, current: int):
        time_stamp_index = self.data.index[current]
        return self.data.loc[time_stamp_index]

    def get_time_stamp(self, i: int):
        return self.data.index[i]
