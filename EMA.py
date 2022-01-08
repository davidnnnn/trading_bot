from alpha_vantage.techindicators import TechIndicators
import matplotlib.pyplot as plt

class EMA:
	def __init__(self, tech_indicators: TechIndicators, symbol: str, interval: str, time_period: int, series_type="close"):
		# api key imported from a text file, just the key, no letters
        f = open("Alpha_Vantage_premium_key.txt", r)
        apiKey = f.read()
        f.close()
		self.ta = TechIndicators(key=apiKey, output_format="pandas")
		self.data, self.meta = tech_indicators.get_ema(symbol, interval, time_period, series_type)

	def table(self):
		return self.data

	def last_bar_index(self) -> float:
		return len(self.data.index)-1

	def previous_bar(self, current: int):
		time_stamp_index = self.data.index[current+1]
		return self.data.loc[time_stamp_index]

	def current_bar(self, current: int):
		time_stamp_index = self.data.index[current]
		return self.data.loc[time_stamp_index]