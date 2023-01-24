from telegram import Update, Bot
import time
import pandas as pd
from datetime import datetime, date, timedelta
from pybit import usdt_perpetual
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
#-1001839931719
from dotenv import dotenv_values
import nest_asyncio
import requests
import threading
import logging

# create a logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# create a file handler
handler = logging.FileHandler('logs.txt')
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handler to the logger
logger.addHandler(handler)

## wait a minute... doesnt this mean i need a database of all the rsi over the last year?


#no. just export to csv.

nest_asyncio.apply()

config = dotenv_values(".env")

apikey = config["TELEGRAM_API_KEY"]
chat_id = config["CHAT_ID_CHANNEL_BETA"]

class TelegramBot:

    def __init__(self, apikey, chat_id):
        self.apikey = apikey
        self.chat_id = chat_id

    started = False
    long_alert = 30
    short_alert = 70
    last_rsi = 0
    bot = None
    eth_1m = pd.DataFrame(data=None, columns=["open_time", "high", "low","open","close","volume","turnover", "date_time"])
        

    async def start(self, update: Update, context: ContextTypes):
        if (self.started is False):
            self.started = True
            await self.bot.send_message(chat_id,'Starting.')
            await self.bot.send_message(chat_id,'Getting Bybit and rsi data...')
            self.assemble_data()
            await self.bot.send_message(chat_id,'Retrieved data. Starting routine, please wait...')
            self.start_routine()
        else: 
            await self.bot.send_message(chat_id, 'Already started.')





    async def long(self, update: Update, context):
        text = update.message.text.replace('/long ', '')
        
        
        if (text == '/long'):
            await update.message.reply_text(f'Must add number.')
            return
        else: 
            await update.message.reply_text(f'Updating long alert to {text}.')
            self.long_alert = int(text)


    async def short(self, update: Update, context):
        text = update.message.text.replace('/short ', '')
        
        
        if (text == '/short'):
            await update.message.reply_text(f'Must add number.')
            return
        else: 
            await update.message.reply_text(f'Updating short alert to {text}.')
            self.short_alert = int(text)

    async def get_current_rsi_message(self, update:Update, context):
        await update.message.reply_text(f"last rsi: {self.last_rsi}, last eth close: {self.eth_1m['close'].iloc[-1]}")

    async def get_short(self, update:Update, context):
        await update.message.reply_text(f'number alert to short: {self.short_alert}')

    async def get_long(self, update:Update, context):
        await update.message.reply_text(f'number alert to long: {self.long_alert}')

    async def list_commands(self, update, context):
        await update.message.reply_text(f"""    commands: 
        /long NUM: change long alert (should be negative)
        /short NUM: change short alert (should be POSITIVE)
        /whatislong: get rsi alert number
        /whatisshort: get rsi alert number
        /help: help
        /startrsi: start
        /rsi: get last rsi

        
        
        """)


    def start_telegram_bots(self):
        app = ApplicationBuilder().bot(Bot(apikey)).build()

        app.add_handler(CommandHandler("startrsi", self.start))
        app.add_handler(CommandHandler("long", self.long))
        app.add_handler(CommandHandler("short", self.short))
        app.add_handler(CommandHandler("whatislong", self.get_long))
        app.add_handler(CommandHandler("whatisshort", self.get_short))

        app.add_handler(CommandHandler("rsi", self.get_current_rsi_message))
        app.add_handler(CommandHandler("help", self.list_commands))
        self.bot = app.bot

        app.run_polling()

    def start_routine(self):
        print('starting routine')
        current_time = pd.Timestamp(datetime.now()).second
        while (current_time != 2):
            time.sleep(1)
            current_time = pd.Timestamp(datetime.now()).second
        try:
            self.get_last_rsi()
        except Exception as e:
            logger.error(e)
        finally:
            self.send_to_telegram('Ready.')
        
    #def get_rsi_and_signal(self, close, long, short, signal):

    def get_rsi(self, df, periods = 14, ema = True):
        """
        Returns a pd.Series with the relative strength index.
        """
        close_delta = df['close'].diff()

        # Make two series: one for lower closes and one for higher closes
        up = close_delta.clip(lower=0)
        down = -1 * close_delta.clip(upper=0)
        
        if ema == True:
            # Use exponential moving average
            ma_up = up.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
            ma_down = down.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
        else:
            # Use simple moving average
            ma_up = up.rolling(window = periods, adjust=False).mean()
            ma_down = down.rolling(window = periods, adjust=False).mean()
            
        rsi = ma_up / ma_down
        rsi = 100 - (100/(1 + rsi))
        return rsi

    def assemble_data(self):
        print('assembling')
        eth_1m = self.get_minutes(5, "ETHUSDT", 200, 1)
        eth_1m['rsi'] = self.get_rsi(eth_1m, 14, False)
        self.eth_1m = eth_1m
        self.last_rsi = eth_1m['rsi'].iloc[-1]
        #eth = eth[eth['date_time'] >= '2020-01-01']

    def get_last_rsi(self):
        try:
            updatedPrice = self.get_minutes(1, "ETHUSDT", 1, 1)
            #new_array = pd.concat([self.eth_1m, updatedPrice])
            new_df = self.eth_1m.append(updatedPrice, ignore_index=True)
            new_df.reset_index(drop=True)
            
            new_df['rsi'] = self.get_rsi(new_df)
            last_rsi = new_df['rsi'].iloc[-1]
            self.last_rsi = last_rsi
            self.eth_1m = new_df
            logger.debug(f"{new_df['date_time'].iloc[-1]}")

            if (last_rsi > self.short_alert or last_rsi < self.long_alert):
                self.send_to_telegram(f"new rsi at {pd.Timestamp(datetime.now())}: {self.last_rsi}; last close: {new_df['close'].iloc[-1]}")

            threading.Timer(60.0, self.get_last_rsi).start()
        except Exception as e:
            logger.error(e)
            return

    

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

    
    def send_to_telegram(self,message):

        apiURL = f'https://api.telegram.org/bot{apikey}/sendMessage'

        try:
            response = requests.post(apiURL, json={'chat_id': chat_id, 'text': message})
            print(response.ok)
        except Exception as e:
            logger.error(e)

try:
    bot = TelegramBot(apikey, chat_id)
    bot.start_telegram_bots()
except Exception as e:
    logger.error(e)