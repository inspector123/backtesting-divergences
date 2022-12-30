from telegram import Update, Bot
import time
import pandas as pd
from datetime import datetime, date, timedelta
from pybit import usdt_perpetual
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
#-1001839931719
from dotenv import dotenv_values
import nest_asyncio

## wait a minute... doesnt this mean i need a database of all the TSI over the last year?


#no. just export to csv.

nest_asyncio.apply()

config = dotenv_values(".env")

apikey = config["TELEGRAM_API_KEY"]
chat_id = config["CHAT_ID_CHANNEL_BETA"]

class TelegramBot:
    
    long_alert = -60
    short_alert = 60
    last_tsi = 0
    bot = None
    eth_1m = pd.DataFrame(data=None, columns=["open_time", "high", "low","open","close","volume","turnover", "date_time"])
        

    async def start(self, update: Update, context: ContextTypes):

        await self.bot.send_message(chat_id,'Starting.')
        await self.bot.send_message(chat_id,'Getting Bybit and TSI data...')
        self.assemble_data()
        await self.bot.send_message(chat_id, 'Data retrieved. Starting routine')
        await self.start_routine()
        # await update.message.reply_text
        #self.start_routine()





    async def long(update: Update, context):
        await update.message.reply_text(f'Updating long alert to {update.message.text}.')


    async def short(update: Update, context):
        await update.message.reply_text(f'Updating short alert to {update.message.text}.')
        print(update)
        print(context)

    async def get_last_tsi(self, update:Update, context):
        await update.message.reply_text(f'last tsi: {self.tsi}')

    def start_telegram_bots(self):
        app = ApplicationBuilder().bot(Bot(apikey)).build()

        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("long", self.long))
        app.add_handler(CommandHandler("short", self.short))
        app.add_handler(CommandHandler("lasttsi", self.get_last_tsi))
        self.bot = app.bot

        app.run_polling()

    async def start_routine(self):
        print('starting routine')
        
        while True:
            time.sleep(1)
            current_time = pd.Timestamp(datetime.now()).second
            if current_time == 0:

                await self.get_last_tsi()

    def check_tsi_1m(self):
        print('check tsi')

    def get_tsi_and_signal(self, close, long, short, signal):
        diff = close - close.shift(1)
        abs_diff = abs(diff)
        
        diff_smoothed = diff.ewm(span = long, adjust = False).mean()
        diff_double_smoothed = diff_smoothed.ewm(span = short, adjust = False).mean()
        abs_diff_smoothed = abs_diff.ewm(span = long, adjust = False).mean()
        abs_diff_double_smoothed = abs_diff_smoothed.ewm(span = short, adjust = False).mean()
        
        tsi = (diff_double_smoothed / abs_diff_double_smoothed) * 100
        signal = tsi.ewm(span = signal, adjust = False).mean()
        #tsi = tsi[tsi.index >= '2020-01-01'].dropna()
        #signal = signal[signal.index >= '2020-01-01'].dropna()
        
        return tsi, signal

    def assemble_data(self):
        print('assembling')
        eth_1m = self.get_minutes(10, "ETHUSDT", 200, 1)
        eth_1m['tsi'], eth_1m['signal_line'] = self.get_tsi_and_signal(eth_1m['close'], 25, 13, 12)
        self.eth_1m = eth_1m
        self.last_tsi = eth_1m['tsi'][::-1]
        #eth = eth[eth['date_time'] >= '2020-01-01']
        eth_1m.tail(1)

    async def get_last_tsi(self):
        updatedPrice = self.get_minutes(1, "ETHUSDT", 1, 1)
        new_array = pd.concat([self.eth_1m, updatedPrice])
        new_array['tsi'], new_array['signal_line'] = self.get_tsi_and_signal(new_array['close'], 25, 13, 12)
        self.last_tsi = new_array['tsi'][-1]
        self.eth_1m = new_array

        await self.bot.send_message(chat_id, f'new tsi at {pd.Timestamp(datetime.now())}: {self.last_tsi}')


    def get_minutes(self, iterations, symbol, number_of_records, minutes_interval):
        result = []
        session_unauth = usdt_perpetual.HTTP(
            endpoint="https://api.bybit.com"
        )
        j = 0
        for i in range(iterations, 0, -1):
            _time = int(pd.Timestamp(datetime.now()-timedelta(minutes=(minutes_interval*number_of_records*i)), tz='US/Pacific').timestamp())
            res = session_unauth.query_kline(
                symbol=symbol,
                interval=minutes_interval,
                from_time=_time
            )["result"]
            j += 1
            print(f'processed {j} of {iterations}')
            result += res

        df = pd.DataFrame(data=result, columns=["open_time", "high", "low","open","close","volume","turnover", "date_time"])

        df['date_time'] = df['open_time'].apply(lambda x: datetime.fromtimestamp(x))
        df.set_index('date_time').astype(float)
        return df

bot = TelegramBot()
bot.start_telegram_bots()