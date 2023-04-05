# encoding: utf-8

#import alpaca_trade_api as tradeapi

import sys, os, time, pytz
import tulipy as ti
import pandas as pd
import yfinance as yf
from logger import *
import gvars

from datetime import datetime, timedelta
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit
from math import ceil
from enum import Enum


class Trader:
    def __init__(self,ticker,api):
        lg.info('Trader initialized with ticker %s' % ticker)
        self.ticker = ticker
        self.api = api

    def is_tradable(self,ticker):
        # ask the broker/API if "ticker" is tradable
            # IN: ticker (string)
            # OUT: True (tradable) / False (not tradable)
        try:
            # ticker = get ticker from alpaca wrapper (.tradable)
            if not ticker.tradable:
                lg.info('The ticker %s is not tradable' % ticker)
                return False
            else:
                lg.info('The ticker %s is tradable!' % ticker)
                return True
        except:
            lg.error('The ticker %s is not ansering well' % ticker)
            return False

    def set_stoploss(self,entryPrice,trend):
        # takes an entry price and sets the stoploss (trend)
            # IN: entry price, trend (long/short)
            # OUT: stop loss ($)

        try:
            if trend == 'long':
                # example: 10 - (10*0.05) = 9.5
                stopLoss = entryPrice - (entryPrice * gvars.stopLossMargin)
                lg.info('Stop loss set for long at %.2f' % stopLoss)
                return stopLoss
            elif trend == 'short':
                # example: 10 + (10*0.05) = 10.5
                stopLoss = entryPrice + (entryPrice * gvars.stopLossMargin)
                lg.info('Stop loss set for long at %.2f' % stopLoss)
                return stopLoss
            else:
                raise ValueError

        except Exception as e:
            lg.error('The trend value is not understood: %s' % str(trend))
            sys.exit()

    def set_takeprofit(self,entryPrice,trend):
        # takes a price as an input and sets the takeprofit
            # IN: entry price, trend (long/short)
            # OUT: take profit ($)

        try:
            if trend == 'long':
                # example: 10 + (10*0.1) = 11$
                takeProfit = entryPrice + (entryPrice * gvars.takeProfitMargin)
                lg.info('Take profit set for long at %.2f' % takeProfit)
                return takeProfit
            elif trend == 'short':
                # example: 10 - (10*0.1) = 9$
                takeProfit = entryPrice - (entryPrice * gvars.takeProfitMargin)
                lg.info('Take profit set for short at %.2f' % takeProfit)
                return takeProfit
            else:
                raise ValueError

        except Exception as e:
            lg.error('The trend value is not understood: %s' % str(trend))
            sys.exit()

    def load_historical_data(self,ticker,interval,period):
        # load historical stock data
            # IN: ticker, interval (aggregation), api, entries limit
            # OUT: array with stock data (OHCL)

        try:
            ticker = yf.Ticker(ticker)
            data = ticker.history(period,interval)

        except Exception as e:
            lg.error('Something happened while loading historical data')
            lg.error(e)
            sys.exit()

        return data

    def get_open_positions(self,assetId):
        # get open positions
            # IN: assetId (unique identifier)
            # OUT: boolean (True = already open, False = not open)

        # positions = ask alpaca wrapper for the list of open positions
        for position in positions:
            if position.symbol == assetId:
                return True
            else:
                return False

    def submit_order(self,type,trend,ticker,sharesQty,currentPrice,exit=False):
        # IN: order data (number of shares, order type)
        # OUT: boolean (True = order went through, False = order did not)

        lg.info('Submitting %s order for %s' % (trend,ticker))

        if trend == 'long' and not exit:
            side = 'buy'
            limitPrice = round(currentPrice + currentPrice*gvars.maxVar,2)
        elif trend == 'short' and not exit:
            side = 'sell'
            limitPrice = round(currentPrice - currentPrice*gvars.maxVar,2)
        elif trend == 'long' and exit:
            side = 'sell'
        elif trend == 'short' and exit:
            side = 'buy'
        else:
            lg.error('Trend was not understood')
            sys.exit()

        try:

            if type == 'limit':
                lg.info('Current price: %.2f // Limit price: %.2f' % (currentPrice,limitPrice))
                order = self.api.submit_order(
                    symbol=ticker,
                    qty=sharesQty,
                    side=side,
                    type=type,
                    time_in_force='gtc',
                    limit_price=limitPrice
                )

            elif type == 'market':
                lg.info('Current price: %.2f' % currentPrice)
                order = self.api.submit_order(
                    symbol=ticker,
                    qty=sharesQty,
                    side=side,
                    type=type,
                    time_in_force='gtc'
                )

            else:
                lg.error('Type of order was not undersood')
                sys.exit()

            self.orderId = order.id

            lg.info('%s order submitted correctly!' % trend)
            lg.info('%d shares %s for %s' % (sharesQty,side,ticker))
            lg.info('Client order ID: %s' % self.orderId)
            return True

        except Exception as e:
            lg.error('Something happend when submitting order')
            lg.error(e)
            sys.exit()

    def cancel_pending_order(self,ticker):
        # cancel order: cancels our order (retry)
            # IN: order id
            # OUT: boolean (True = order cancelled, False = order not cancelled)
        lg.info('Cancelling order %s for %s' % (self.orderId,ticker))
        attempt = 1

        while attempt <= gvars.maxAttemptsCPO:
            try:
                self.api.cancel_order(self.orderId)
                lg.info('Order %s cancelled correctly' % self.orderId)
                return True
            except:
                lg.info('Order could not be cancelled, retrying...')
                time.sleep(gvars.sleepTimeCPO) # wait 5 seconds and retry
                attempt += 1

        lg.error('The order could not be cancelled, cancelling all orders...')
        lg.info('Client order ID: %s' % self.orderId)
        self.api.cancel_all_orders()
        sys.exit()

    def check_position(self,ticker,doNotFind=False):
        # check whether the position exists or not
            # IN: ticker, doNotFind (means that I dont want to find)
            # OUT: boolean (True = order is there, False = order not there)
        attempt = 1
        time.sleep(gvars.sleepTimeCP)

        while attempt <= gvars.maxAttemptsCP:
            try:
                position = self.api.get_position(ticker)
                currentPrice = float(position.current_price)
                lg.info('The position was found. Current price is: %.2f' % currentPrice)
                return True
            except Exception as e:
                if doNotFind:
                    lg.info('Position not found, this is good!')
                    return False

                lg.info('Exception: %s' % e)
                lg.info('Position not found, waiting for it...')
                time.sleep(gvars.sleepTimeCP) # wait 5 seconds and retry
                attempt += 1

        lg.info('Position not found for %s, not waiting any more' % ticker)
        return False

    def get_shares_amount(self,assetPrice):
        # works out the number of shares I want to buy/sell
            # IN: assetPrice
            # OUT: number of shares

        lg.info('Getting shares amount')

        try:
            # get the total equity available
            account = self.api.get_account()
            equity = float(account.equity)

            # calculate the number of shares
            sharesQuantity = int(gvars.maxSpentEquity / assetPrice)

            if equity - sharesQuantity*assetPrice > 0:
                lg.info('Total shares to operate with: %d' % sharesQuantity)
                return sharesQuantity
            else:
                lg.info('Cannot spend that amount, remaining equity is %.2f' % equity)
                sys.exit()

        except Exception as e:
            lg.error('Something happend at get shares amount')
            lg.error(e)
            sys.exit()

    def get_current_price(self,ticker):
        # get the current price of an ticker with a position open
            # IN: ticker
            # OUT: price ($)

        attempt = 1

        while attempt <= gvars.maxAttemptsGCP:
            try:
                position = self.api.get_position(ticker)
                currentPrice = float(position.current_price)
                lg.info('The position was checked. Current price is: %.2f' % currentPrice)
                return currentPrice
            except:
                lg.info('Position not found, cannot check price, waiting for it...')
                time.sleep(gvars.sleepTimeGCP) # wait 5 seconds and retry
                attempt += 1

        lg.error('Position not found for %s, not waiting any more' % ticker)
        return False

    def get_avg_entry_price(self,ticker):
        # get the current price of an ticker with a position open
            # IN: ticker
            # OUT: price ($)

        attempt = 1

        while attempt <= gvars.maxAttemptsGAEP:
            try:
                position = self.api.get_position(ticker)
                avgEntryPrice = float(position.avg_entry_price)
                lg.info('The position was checked. Current price is: %.2f' % avgEntryPrice)
                return avgEntryPrice
            except:
                lg.info('Position not found, cannot check price, waiting for it...')
                time.sleep(gvars.sleepTimeGAEP) # wait 5 seconds and retry
                attempt += 1

        lg.error('Position not found for %s, not waiting any more' % ticker)
        return False

    def get_general_trend(self,ticker):
        # get general trend: detect interesting trend (UP / DOWN / FALSE if not trend)
            # IN: ticker
            # OUTPUT: LONG / SHORT / NO TREND (strings)
            #If no trend defined, go back to POINT ECHO

        lg.info('\nGENERAL TREND ANALYSIS entered')

        attempt = 1

        try:
            while True:

                #period = 50 samples of 30 minutes = around 5 days (8h each) of data
                # ask for 30 min candles
                data = self.load_historical_data(ticker,interval='30m',period='5d')

                close = data.Close.values

                # calculate EMAs
                ema9 = ti.ema(close, 9)[-1]
                ema26 = ti.ema(close, 26)[-1]
                ema50 = ti.ema(close, 50)[-1]

                lg.info('%s general trend EMAs = [EMA9:%.2f,EMA26:%.2f,EMA50:%.2f]' % (ticker,ema9,ema26,ema50))

                # checking EMAs relative position
                if (ema50 < ema26) and (ema26 < ema9):
                    lg.info('Trend detected for %s: long' % ticker)
                    return 'long'
                elif (ema50 > ema26) and (ema50 > ema9):
                    lg.info('Trend detected for %s: short' % ticker)
                    return 'short'
                elif attempt <= gvars.maxAttemptsGGT:
                    lg.info('Trend not clear for %s, waiting...' % ticker)
                    attempt += 1
                    time.sleep(gvars.sleepTimeGGT * gvars.maxAttemptsGGT)
                else:
                    lg.info('Trend NOT detected and timeout reached for %s' % ticker)
                    return False

        except Exception as e:
            lg.error('Something went wrong at get general trend')
            lg.error(e)
            sys.exit()

    def get_instant_trend(self,ticker,trend):
        # get instat trend: confirm the trend detected by GT analysis
            # IN: ticker, trend (long / short)
            # OUT: True (trend confirmed) / False (not a good moment to enter)

        lg.info('\nINSTANT TREND ANALYSIS entered')

        attempt = 1

        try:
            while True:
                #period = 50 samples of 5 minutes = less than 1 day (8h) of data
                data = self.load_historical_data(ticker,interval='5m',period='1d')

                close = data.Close.values

                # calculate the EMAs
                ema9 = ti.ema(close,9)[-1]
                ema26 = ti.ema(close,26)[-1]
                ema50 = ti.ema(close,50)[-1]

                lg.info('%s instant trend EMAs = [EMA9:%.2f,EMA26:%.2f,EMA50:%.2f]' % (ticker,ema9,ema26,ema50))

                if (trend == 'long') and (ema9 > ema26) and (ema26 > ema50):
                    lg.info('Long trend confirmed for %s' % ticker)
                    return True
                elif (trend == 'short') and (ema9 < ema26) and (ema26 < ema50):
                    lg.info('Short trend confirmed for %s' % ticker)
                    return True
                elif attempt <= gvars.maxAttemptsGIT:
                    lg.info('Trend not clear for %s, waiting...' % ticker)
                    attempt += 1
                    time.sleep(gvars.sleepTimeGIT)
                else:
                    lg.info('Trend NOT detected and timeout reached for %s' % ticker)
                    return False

        except Exception as e:
            lg.error('Something went wrong at get instant trend')
            lg.error(e)
            sys.exit()

    def get_rsi(self,ticker,trend):
        # get rsi: perfom RSI analysis
            # IN: ticker, trend
            # OUT: True (confirmed) / False (not confirmed)

        lg.info('\nRSI ANALYSIS entered')

        attempt = 1

        try:
            while True:
                #period = 50 samples of 5 minutes = less than 1 day (8h) of data
                data = self.load_historical_data(ticker,interval='5m',period='1d')

                # calculate the RSI
                rsi = ti.rsi(data.Close.values, 14)[-1] # it uses 14-sample window

                lg.info('%s rsi = [%.2f]' % (ticker,rsi))

                if (trend == 'long') and (rsi > 50) and (rsi < 80):
                    lg.info('Long trend confirmed for %s' % ticker)
                    return True
                elif (trend == 'short') and (rsi < 50) and (rsi > 20):
                    lg.info('Short trend confirmed for %s' % ticker)
                    return True
                elif attempt <= gvars.maxAttemptsRSI:
                    lg.info('Trend not clear for %s, waiting...' % ticker)
                    attempt += 1
                    time.sleep(gvars.sleepTimeRSI)
                else:
                    lg.info('Trend NOT detected and timeout reached for %s' % ticker)
                    return False

        except Exception as e:
            lg.error('Something went wrong at rsi analysis')
            lg.error(e)
            sys.exit()

    def get_stochastic(self,ticker,trend):
        # get stochastic: perfom STOCHASTIC analysis
            # IN: ticker, trend
            # OUT: True (confirmed) / False (not confirmed)

        lg.info('\nSTOCHASTIC ANALYSIS entered')

        attempt = 1

        try:
            while True:
                #period = 50 samples of 5 minutes = less than 1 day (8h) of data
                data = self.load_historical_data(ticker,interval='5m',period='1d')

                # calculate the STOCHASTIC
                stoch_k, stoch_d = ti.stoch(data.High.values, data.Low.values, data.Close.values, 9, 6, 9)
                stoch_k = stoch_k[-1]
                stoch_d = stoch_d[-1]

                lg.info('%s stochastic = [K_FAST:%.2f,D_SLOW:%.2f]' % (ticker,stoch_k,stoch_d))

                if (trend == 'long') and (stoch_k > stoch_d) and (stoch_k < 80) and (stoch_d < 80):
                    lg.info('Long trend confirmed for %s' % ticker)
                    return True
                elif (trend == 'short') and (stoch_k < stoch_d) and (stoch_k > 20) and (stoch_d > 20):
                    lg.info('Short trend confirmed for %s' % ticker)
                    return True
                elif attempt <= gvars.maxAttemptsSTC:
                    lg.info('Trend not clear for %s, waiting...' % ticker)
                    attempt += 1
                    time.sleep(gvars.sleepTimeSTC)
                else:
                    lg.info('Trend NOT detected and timeout reached for %s' % ticker)
                    return False

        except Exception as e:
            lg.error('Something went wrong at stochastic analysis')
            lg.error(e)
            sys.exit()

    def check_stochastic_crossing(self,ticker,trend):
        # check whether the stochastic curves have crossed or not
        # depending on the trend
            # IN: ticker, trend
            # OUT: True if crossed / False if not crossed

        lg.info('Checking stochastic crossing...')
        #period = 50 samples of 5 minutes = less than 1 day (8h) of data
        data = self.load_historical_data(ticker,interval='5m',period='1d')

        # calculate the STOCHASTIC
        stoch_k, stoch_d = ti.stoch(data.High.values, data.Low.values, data.Close.values, 9, 6, 9)
        stoch_k = stoch_k[-1]
        stoch_d = stoch_d[-1]

        lg.info('%s stochastic = [K_FAST:%.2f,D_SLOW:%.2f]' % (ticker,stoch_k,stoch_d))

        try:
            if (trend == 'long') and (stoch_k <= stoch_d):
                lg.info('\nSTOCHASTIC CURVES CROSSED: long, k=%.2f, d=%.2f' % (stoch_k,stoch_d))
                return True
            elif (trend == 'short') and (stoch_k >= stoch_d):
                lg.info('\nSTOCHASTIC CURVES CROSSED: short, k=%.2f, d=%.2f' % (stoch_k,stoch_d))
                return True
            else:
                lg.info('Stochastic curves have not crossed')
                return False

        except Exception as e:
            lg.error('Something went wrong at check stochastic crossing')
            lg.error(e)
            return True

    def enter_position_mode(self,ticker,trend):
        # check the conditions in parallel once inside the position
        attempt = 1

        # get average entry price
        entryPrice = self.get_avg_entry_price(ticker)

        # set the take profit
        takeProfit = self.set_takeprofit(entryPrice,trend)

        # set the stop loss
        stopLoss = self.set_stoploss(entryPrice,trend)

        try:
            while True:

                self.currentPrice = self.get_current_price(ticker)

                # check if take profit met
                # LONG/UP version
                if (trend == 'long') and (self.currentPrice >= takeProfit):
                    lg.info('Take profit met at %.2f. Current price is %.2f' % (takeProfit,self.currentPrice))
                    return True

                # SHORT/DOWN version
                elif (trend == 'short') and (self.currentPrice <= takeProfit):
                    lg.info('Take profit met at %.2f. Current price is %.2f' % (takeProfit,self.currentPrice))
                    return True

                #check if stop loss is met
                # LONG/UP version
                elif (trend == 'long') and (self.currentPrice <= stopLoss):
                    lg.info('Stop loss met at %.2f. Current price is %.2f' % (stoploss,self.currentPrice))
                    return False

                # SHORT/DOWN version
                elif (trend == 'short') and (self.currentPrice <= stopLoss):
                    lg.info('Stop loss met at %.2f. Current price is %.2f' % (stoploss,self.currentPrice))
                    return False

                # check stoch crossing
                elif self.check_stochastic_crossing(ticker,trend):
                    lg.info('Stochastic curves crossed. Current price is %.2f' % self.currentPrice)
                    return True

                # we wait
                elif attempt <= gvars.maxAttemptsEPM:
                    lg.info('Waiting inside position, attempt #%d' % attempt)
                    lg.info('SL %.2f <-- %.2f --> %.2f TP' % (stopLoss,self.currentPrice,takeProfit))
                    time.sleep(gvars.sleepTimeEPM)
                    attempt += 1

                # get out, time is out
                else:
                    lg.info('Timeout reached at enter position, too late')
                    return False

        except Exception as e:
            lg.error('Something happend at enter position function')
            lg.error(e)
            return True

    def run(self,ticker):

        #POINT DELTA: LOOP until timeout reached (ex. 2h)
        while True:

            # POINT ECHO
            # ask the broker/API if we have an open position with "ticker"
            if self.check_position(self.ticker,doNotFind=True):
                lg.info('There is already an open position with that ticker! Aborting...')
                return False # aborting execution

            # POINT DELTA
            while True:

                # find general a trend
                trend = self.get_general_trend(self.ticker)
                if not trend:
                    lg.info('No general trend found for %s! Going out...' % self.ticker)
                    return False # aborting execution

                #trend='long'

                # confirm instant trend
                if not self.get_instant_trend(self.ticker,trend):
                    lg.info('The instant trend is not confirmed. Going back.')
                    continue # If failed go back to POINT DELTA

                # perfom RSI analysis
                if not self.get_rsi(self.ticker,trend):
                    lg.info('The rsi is not confirmed. Going back.')
                    continue # If failed go back to POINT DELTA

                # perfom STOCHASTIC analysis
                if not self.get_stochastic(self.ticker,trend):
                    lg.info('The stochastic is not confirmed. Going back.')
                    continue # If failed go back to POINT DELTA

                lg.info('All filtering passed, carrying on with the order!')
                break # get out of the loop

            # get current price
            currentPrice = self.load_historical_data(ticker,interval='5m',period='1d').Close.values[-1]
            self.currentPrice = round(float(currentPrice),2)

            # decide the total amount to invest
            sharesQty = self.get_shares_amount(self.currentPrice)

            lg.info('\nDESIRED ENTRY PRICE: %.2f' % self.currentPrice)
            # submit order (limit)
            success = self.submit_order(
                            'limit',
                            trend,
                            ticker,
                            sharesQty,
                            self.currentPrice
                            )

            # check position
            if not self.check_position(self.ticker):
                self.cancel_pending_order(self.ticker)
                continue # go back to POINT ECHO

            # enter position mode
            successfulOperation = self.enter_position_mode(ticker,trend)

            #GET OUT
            success = self.submit_order(
                        'market',
                        trend,
                        ticker,
                        sharesQty,
                        self.currentPrice,
                        exit = True
                        )

            while True:
                # check the position is cleared
                if not self.check_position(self.ticker,doNotFind=True):
                    break # GET OUT OF THE MAIN WHILE

                lg.info('\nWARNING! THE POSITION SHOULD BE CLOSED! Retrying...')
                time.sleep(gvars.sleepTimeCP) # wait 10 seconds

            # end of execution
            return successfulOperation
