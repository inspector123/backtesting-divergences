# #1652112000000
# #1652544000000"
# # start = 1652112000000
# # parameters = { "start": int(time2), "end": int(time1), "interval": 5, "symbol": "ETHUSDT" }
# # print(parameters)
# # #urltest = "https://api.bybit.com/derivatives/v3/public/kline?category=linear&symbol=ALGOUSDT&interval=D&start=1652112000000&end=1652544000000"
# # _url = f"https://api.bybit.com/derivatives/v3/public/kline?category=linear&symbol={parameters['symbol']}&interval={parameters['interval']}&start={parameters['start']}&end={parameters['end']}"
# # _response = requests.get(_url)
# # _df = pd.DataFrame(data=_response.json()["result"]["list"], columns=["Timestamp","Open", "high", "low", "close", "volume", "turnover"])
# # print(_df, '\n','last candle: \n', datetime.fromtimestamp(int(_df.iloc[0]["Timestamp"])/1000), '\n', 'current time: \n', datetime.now())

# #ok, what do I wnt this to do? just to get the latest candlestick or to get all data?
# #this function will tell you what the latest time is on the candlesticks (ie if it's time to calculate again))
# # for now i may not need this
# def get_current_candlestick(start, end, interval, symbol):
#     url = f"https://api.bybit.com/derivatives/v3/public/kline?category=linear&symbol={symbol}&interval={interval}&start={start}&end={end}"
#     response = requests.get(url)
#     print(response.json()["result"])
#     df = pd.DataFrame(data=response.json()["result"]["list"], columns=["Timestamp","Open", "high", "low", "close", "volume", "turnover"])
#     latest_candlestick = datetime.fromtimestamp(int(df.iloc[0]["Timestamp"])/1000)
#     print(latest_candlestick)
#     return latest_candlestick