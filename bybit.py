
from datetime import datetime, timedelta
import pandas as pd

from pybit import usdt_perpetual

n=5
m = 5
result = []
session_unauth = usdt_perpetual.HTTP(
    endpoint="https://api.bybit.com"
)
for i in range(n, 0, -1):
    _time = int(pd.Timestamp(datetime.now()-timedelta(minutes=(m*200*i)), tz='US/Pacific').timestamp())
    res = session_unauth.query_kline(
        symbol="ETHUSDT",
        interval=m,
        from_time=_time
    )["result"]
    result += res

df = pd.DataFrame(data=result, columns=["open_time", "high", "low","open","close","volume","turnover"])

df['open_time'] = df['open_time'].apply(lambda x: datetime.fromtimestamp(x))
#print(result)
print(df['open_time'])