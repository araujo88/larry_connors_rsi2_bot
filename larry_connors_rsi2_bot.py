# Larry Connors RSI2

import websocket, json, pprint, numpy
import config # config file with Binance API keys
from binance.client import Client
from binance.enums import *
import time
import requests
import win32api

SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_15m" # Binance socket - 15 minute chart
TAAPI_MA5 = "https://api.taapi.io/ma?secret=YOUR_SECRET_KEY&exchange=binance&symbol=ETH/USDT&interval=15m&optInTimePeriod=5" # Socket for 5-period moving average
TAAPI_MA200 = "https://api.taapi.io/ma?secret=YOUR_SECRET_KEY&exchange=binance&symbol=ETH/USDT&interval=15m&optInTimePeriod=200" # Socket for 200-period moving average
TAAPI_RSI = "https://api.taapi.io/rsi?secret=YOUR_SECRET_KEY&exchange=binance&symbol=ETH/USDT&interval=15m&optInTimePeriod=2" # Socket for RSI-2

TRADE_SYMBOL = 'ETHUSDT' # Trading pair
TRADE_QUANTITY = 0.01
FEE = 0.001 # Binance fee
in_position = False

RSI_OVERSOLD = 5
RSI_OVERBOUGHT = 95

client = Client(config.API_KEY, config.API_SECRET)

# Synchronizes Windows clock with Binance
gt = client.get_server_time()
tt=time.gmtime(int((gt["serverTime"])/1000))
win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
	try:
		print("sending order")
		order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
		print(order)
	except Exception as e:
		print("an exception occured - {}".format(e))
		return False

	return True

def on_open(ws):
	print('opened connection')

def on_close(ws):
	print('closed connection')

def on_message(ws, message):
    global in_position	
    #print('received message')	
    json_message = json.loads(message)
    #pprint.pprint(json_message)

    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        print("Candle close: {}".format(close))
        close = float(close)

        r1 = requests.get(url = TAAPI_MA5)
        data1 = r1.json()
        MA5 = data1['value']
        print("MA5: {}".format(MA5))

        r2 = requests.get(url = TAAPI_MA200)
        data2 = r2.json()
        MA200 = data2['value']
        print("MA200: {}".format(MA200))

        r3 = requests.get(url = TAAPI_RSI)
        data3 = r3.json()
        RSI = data3['value']
        print("RSI2: {}".format(RSI))

        if close > float(MA200):
            if close > float(MA5):
                if in_position == True:
                    print("Sell trigger! Sell! Sell! Sell!")

                    timestr = time.strftime("%Y/%m/%d-%H:%M:%S") # Save to file
                    file = open('ETH_bot.txt', 'a')
                    file.write("Sell; " + format(close) + ";" + timestr + ";" + "\n")
                    file.close()

                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY-FEE, TRADE_SYMBOL)
                    if order_succeeded == True:
                        in_position = False

                else:
                    print("Sell trigger, but you don't own any. Nothing to do.")
            if float(RSI) < float(RSI_OVERSOLD):
                if in_position == True:
                    print("Buy trigger, but you already own it. Nothing to do")
                else:
                    print("Buy trigger! Buy! Buy! Buy!")		

                    timestr = time.strftime("%Y/%m/%d-%H:%M:%S") # Save to file
                    file = open('ETH_bot.txt', 'a')
                    file.write("Buy; " + format(close) + ";" + timestr + ";" + "\n")
                    file.close()

                    #put binance buy order logic here
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded == True:
                        in_position = True
        else:
            if float(RSI) > float(RSI_OVERBOUGHT):
                if in_position == True:
                    print("Sell trigger! Sell! Sell! Sell!")
    
                    timestr = time.strftime("%Y/%m/%d-%H:%M:%S") # Save to file
                    file = open('ETH_bot.txt', 'a')
                    file.write("Sell; " + format(close) + ";" + timestr + ";" + "\n")
                    file.close()

                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY-FEE, TRADE_SYMBOL)
                    if order_succeeded == True:
                        in_position = False

                else:
                    print("Sell trigger, but you don't own any. Nothing to do.")
    
            if close < float(MA5):
                if in_position == True:
                    print("Buy trigger, but you already own it. Nothing to do")
                else:
                    print("Buy trigger! Buy! Buy! Buy!")		

                    timestr = time.strftime("%Y/%m/%d-%H:%M:%S") # Save to file
                    file = open('ETH_bot.txt', 'a')
                    file.write("Buy; " + format(close) + ";" + timestr + ";" + "\n")
                    file.close()
    
                    #put binance buy order logic here
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded == True:
                        in_position = True

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
