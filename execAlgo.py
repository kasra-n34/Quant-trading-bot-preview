#!/bin/bash
import logging, asyncio, csv, nest_asyncio, errno, math, subprocess, sys, os
import pandas_market_calendars as mcal
import ib_insync as ib, mainModules as mm #was imported as ibi
import numpy as np
from datetime import datetime, date, time
from pathlib import Path
from ib_insync import *
from mainModules import clock, info
import dataAnalysis as da
import pandas as pd
import ast
import time as tm
import importlib
import execFunctions as execFunc
nest_asyncio.apply()

#-------------------GLOBAL VARIABLES and SETTINGS-------------------#

global masterList

masterList = []
blank = []
todayList = [date.today()]

bracket_orders = {}

today = str(date.today())

nyse = mcal.get_calendar('NYSE')
y=nyse.valid_days(start_date='{}'.format(today), end_date='{}'.format(today))

# Define the start and end times
start_time = time(9, 30)  # 9:30 AM
end_time = time(15, 55)    # 3:55 PM

# TIMER SET VARIABLE: Binary setting to control program start time.
timerOnOff = 1 #1=ON, 0=OFF
count = 0

file_path = 'tickerCollection.csv'


# Connect to IB servers
ib = IB()
ib.connect('127.0.0.1', 7497, 0)
print('Connected to IB Server')
ib.reqMarketDataType(1) # Set to 1 in order to receive live date
ib.client.setConnectOptions('+PACEAPI') # Limits buy orders frequency to prevent server kicking us out

# Keep track of current time
mm.clock.timerSet()

#--------------------IB Functions-----------#

# Subscribe to the orderStatus event

def scanExecute():
   '''
   Market scanner to determine stocks to track. Determines masterList.
   '''
   async def scanCreate(scanType, wait):

	#CONFIDENTIAL

  
   async def main2():
       tasksList = []
       for types in mm.info.scanType:
           index = mm.info.scanType.index(types)
           globals()['scanTask{0}'.format(index)] = asyncio.create_task(scanCreate(types, 2))
           tasksList.append(globals()['scanTask{0}'.format(index)])
       await asyncio.wait(tasksList)


   asyncio.run(main2())
   
   return masterList

def updateTickerCollection():
    '''
    Runs scanExecute to obtain masterList. Appends masterList to tickerCollection.csv.
    '''
    masterList = scanExecute()
    print("Length of masterList is {} tickers".format(len(masterList)))
    print(masterList)

    # Read the existing CSV file if it exists
    try:
        datesDf = pd.read_csv(file_path, skiprows=[0], header=None)
        datesDf.columns = ['Date'] + [f'Ticker{i}' for i in range(1, 21)]
        dates = list(datesDf['Date'])
    except pd.errors.EmptyDataError:
        dates = []

    # Check if today's date is already in the file
    if str(date.today()) not in dates:
        # Prepare the new row to append
        new_row = [str(date.today())] + blank + masterList
        
        # Append the new row to the CSV file
        with open(file_path, "a", newline="") as f:
            data_handler = csv.writer(f, delimiter=",")
            data_handler.writerow(new_row)
    else:
        print(f"Today's date {date.today()} is already in the CSV file.")

def makePriceLogs():
   '''
Creates csv of priceLogs for each stock in masterList
No return.
   '''
   headers = ["timeID", "Time", "lastPrice", "Volume", "RTVolume", "Halt", "tradeRate", "volumeRate", "Open", "Close", "Low", "High"]
  
   for stock in masterList:
       print("Creating log for", stock)
       with open("dataCollection/{}/{}-PriceLog({}).csv".format(mm.clock.today, stock, today), "w", newline="") as f:
           data_handler = csv.writer(f, delimiter = ",")
       with open("dataCollection/{}/{}-PriceLog({}).csv".format(mm.clock.today, stock, today), "a", newline="") as f:
           data_handler = csv.writer(f, delimiter = ",")
           data_handler.writerow(headers)


def BracketOrder(parentOrderId, childOrderId, quantity: float, limitPrice: float, trailAmount: float):

   '''
Bracket order sets the conditions for the submitted buy/sell orders to be submitted using IB_insync API.

Parameters:
	parentOrderID - requested using API
	childOrderID - requested using API
	quantity - calculated in main
	limitPrice - latest price in price log
	trailAmount - trail amount percentage (determined from purchase code)

Return: A tuple containing the buy order and the corresponding sell order which is set based on a stop-loss value
   '''


   #This will be our parent or BUY order
   parent = Order()
   stoploss = Order()
   parent.orderId = parentOrderId
   parent.action = 'BUY'
   parent.orderType = "LMT"
   parent.totalQuantity = quantity
   parent.lmtPrice = limitPrice
   parent.transmit = False
   parent.usePriceMgmtAlgo = True


   #This will be our child or Stop Loss SELL order
   stoploss = Order()
   stoploss.orderId = childOrderId
   stoploss.action = "SELL"
   stoploss.orderType = "TRAIL"
   stoploss.trailingPercent = trailAmount
   stoploss.totalQuantity = quantity
   stoploss.parentId = parentOrderId
   stoploss.transmit = True


   bracketOrder = [parent, stoploss]
   return bracketOrder

async def placeOrders(tickerName, quantity, price, trailAmount):
    '''
Asynchronously sends the API calls as to not block the main functions asynchronous functionality.

Parameters:
	tickerName - the specific stock ticker which the order is being placed for
	quantity - calculated in main
	price - latest price in price log
	trailAmount - trail amount percentage (determined from purchase code)

No return value
    '''

    parentOrderId = ib.client.getReqId()
    childOrderId = ib.client.getReqId()
    bracket = BracketOrder(parentOrderId, childOrderId, quantity, price, trailAmount)
    contract = Stock(tickerName, 'SMART', 'USD')
    for order in bracket:
        trade = ib.placeOrder(contract, order)
        await asyncio.sleep(0.1)  # Replace ib.sleep with asyncio.sleep
        

def onOrderStatus(trade):
    order_id = trade.order.orderId
    try:
        if trade.orderStatus.status == 'Filled':
            ticker = trade.contract.symbol  # Get the ticker name
            avg_fill_price = trade.orderStatus.avgFillPrice
            filled_quantity = trade.orderStatus.filled

            print(f"Order filled: {trade.order.action} {ticker} @ {avg_fill_price}, quantity: {filled_quantity}")

            if trade.order.action == 'BUY':
                # Store buy order details
                buy_time = execFunc.get_current_time()
                bracket_orders[order_id] = {
                    'ticker': ticker,
                    'buy_time': buy_time,
                    'buy_price': avg_fill_price,
                    'quantity': filled_quantity
                }
                print(f"Buy order filled for order ID {order_id}")

            elif trade.order.action == 'SELL':
                # Retrieve corresponding buy order details
                parent_id = trade.order.parentId
                print(f"Sell order received. Looking for parent ID {parent_id}")
                buy_details = bracket_orders.pop(parent_id, None)
                if buy_details:
                    # Calculate PnL
                    buy_price = buy_details['buy_price']
                    sell_price = avg_fill_price
                    quantity = buy_details['quantity']
                    buy_time = buy_details['buy_time']  # Ensure buy_time is retrieved correctly

                    print(f"Found corresponding buy order for parent ID {parent_id}")

                    # Log buy and sell details to CSV
                    execFunc.log_to_csv(ticker, order_id, buy_time, buy_price, quantity, sell_price)
                    print(f"Sell order filled for order ID {order_id}")
                else:
                    print(f"No corresponding buy order found for sell order ID {order_id} with parent ID {parent_id}")

    except KeyError as ke:
        print(f"KeyError occurred in onOrderStatus: {ke}")
    except Exception as e:
        print(f"Error occurred in onOrderStatus: {e}")



async def updatePriceLogs(tickerName):
    '''
    This function updates the price log for a stock, pulling the current price using Interactive Brokers API.
    Parameter: tickerName - the stock ticker for which the price log is being updated.
    No return, updates priceLog csv with current time and price.
    '''
    # Form the date string once for consistency and reuse
    today = datetime.now().strftime('%Y-%m-%d')
    # Ensure the directory exists
    Path(f'dataCollection/{today}').mkdir(parents=True, exist_ok=True)
    # File path based on the consistent naming
    file_path = f"dataCollection/{today}/{tickerName}-PriceLog({today}).csv"
    
    # Contract and market data request setup
    contract = Stock(tickerName, 'SMART', 'USD')
    ib.reqContractDetails(contract)
    ib.qualifyContracts(contract)
    # These numbers represent the data that we need in statlist (corresponding and in order)
    ticker = ib.reqMktData(contract, "165, 104, 293, 233, 294, 295, 411, 375, 595")
    
    # Sleep to ensure data is fetched
    await asyncio.sleep(1)
    
    # Getting the current time and formatting it
    current_time = datetime.now().time()
    formatted_time = current_time.strftime('%H:%M:%S')

    # Collecting data to be written
    statList = [ticker.last, ticker.volume, ticker.rtVolume, ticker.halted, ticker.tradeRate, ticker.volumeRate, ticker.open, ticker.close, ticker.low, ticker.high]
    data_row = [count, formatted_time] + statList

    # Opening the file in append mode and writing the data
    with open(file_path, "a", newline="") as f:
        data_handler = csv.writer(f, delimiter = ",")
        data_handler.writerow(data_row)


def sellAllOpenTrades():
    '''
    A function to be used at the end of the trading day, ensuring all pending trades are cancelled and sell all current positions.
    '''
    try:
        # Cancel all active trades at the end of the day
        ib.reqGlobalCancel()
        print("Requested global cancel of all active trades.")
        
        # Retrieve all current positions
        positions = ib.positions()
        print(f"Retrieved positions: {positions}")
        
        # Loop through each position and create an order to sell (end of day)
        for position in positions:
            if position.position > 0:  # Check if the position is a long position
                contract = position.contract
                qty = position.position
                order = MarketOrder('SELL', qty)  # Create a market order to sell all shares
                order.transmit = True  # Ensure the order is transmitted immediately
                trade = ib.placeOrder(contract, order)
                print(f"Placing sell order for {qty} of {contract.symbol}")
    except Exception as e:
        print(f"Error in sellAllOpenTrades: {e}")









    
    

#--------------------Main-------------------------#

# Subscribe to the orderStatus event
ib.orderStatusEvent += onOrderStatus


# Getting suggested parameter values from purchase codes to be used for finding buy conditions
movAvgSizes, consecutiveGains, thresholdGains, stopLossValues = execFunc.getBuyConditions()

# MARKET OPEN VERIFIER: Checks to see if current date is an open stock market day, and only runs the program if confirmed
print("Checking market status...")

if y.empty:
   print("MARKET CLOSED")
   sys.exit()
else:
   print("MARKET IS OPEN TODAY")

# Creates a folder in dataCollection
Path('dataCollection/{}'.format(today)).mkdir(parents=True, exist_ok=True)

# Creates a log
logging.basicConfig(level=logging.INFO, filename='dataCollection/{}/{}log.txt'.format(today,today), format='%(asctime)s %(levelname)s %(name)s: %(message)s')

# Startup message
print("Welcome to AY.10")
print("Version 9.0: Kasra (the GOAT) Era")
updateTickerCollection()

print("Number of tickers in masterList:", len(masterList))

print("Making price logs...")
makePriceLogs()

async def dynamic_update_price_logs(tickerName):
    try:
        importlib.reload(execFunc) #THIS LINE AUTO UPDATES EXEC FUNCTIONS WITHOUT STOPS
        await updatePriceLogs(tickerName)
    except Exception as e:
        logging.error(f"Error updating price logs for {tickerName}: {e}")

async def update_and_trade():
    global count
    while True:
        now = datetime.now().time()
        # Checks whether market is open
        if timerOnOff == 0 or start_time <= now <= end_time:
            start = tm.time()  # Start time of the print("Number of tickers in masterList:", len(masterList))


            # Update price logs asynchronously
            taskList = [asyncio.create_task(dynamic_update_price_logs(tickerName)) for tickerName in masterList]
            await asyncio.wait(taskList)
            count += 1
            execFunc.update_current_purchase_id(count)

            # Check trading conditions and place orders
            for tickerName in masterList:
                try:
                    buyNow, trailAmount, price, purchaseID = execFunc.buyNowCheck(
                        #CONDITIONS FOR BUY ARE CONFIDENTIAL)
                    if buyNow:
                        # Calculates quantity of stocks to be bought
                        quantity = round(1000 / price)
                        quantity = min(quantity, 500)
                        # Create order
                        bracket = BracketOrder(ib.client.getReqId(), ib.client.getReqId(), quantity, price, trailAmount)
                        print("About to buy ---------", tickerName)
                        await placeOrders(tickerName, quantity, price, trailAmount)
                except Exception as e:
                    logging.error(f"Error checking buy conditions or placing order for {tickerName}: {e}")

            # Calculate elapsed time and sleep accordingly
            elapsed = tm.time() - start
            await asyncio.sleep(max(0, 15 - elapsed))  # Ensure at least 15 seconds between starts
        else:
            print("NYSE MARKET CLOSED")
            break  # Exit loop if outside market hours

# Entry point for the asyncio program
async def main():
    await update_and_trade()

# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())

sellAllOpenTrades()

# Disconnects socket connection
ib.disconnect()
print('disconnected')

# Post-Analysis
da.analyzeAllStocks(da.movAvgSize, da.thresholdGain, da.consecutiveGains, da.stopLoss, da.cooldownValue)
da.createSimulatedPriceLog()
da.longAnalysis()
da.generateRecommendations()
