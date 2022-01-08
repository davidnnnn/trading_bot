from alpha_vantage.timeseries import TimeSeries
import pandas as pd

if __name__ == "__main__":
    ts_csv = TimeSeries(key='40B3GFOZMCHINKCC', output_format="csv")
    data = ts_csv.get_intraday_extended(symbol = "AAPL", interval = "15min", slice = "year1month2")
    for row in data:
        print(row)
