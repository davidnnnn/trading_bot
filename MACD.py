from alpha_vantage.techindicators import TechIndicators

class MACD:
	def __init__(self, tech_indicators: TechIndicators, symbol: str, interval: str, time_period: int, series_type="close"):
		# api key imported from a text file, just the key, no letters
        f = open("Alpha_Vantage_premium_key.txt", r)
        apiKey = f.read()
        f.close()
		self.ta = TechIndicators(key=apiKey, output_format="pandas")
		self.data, self.meta = tech_indicators.get_macd(symbol, interval, time_period, series_type)

	def table(self):
		return self.data