# encoding: utf-8

# import needed libraries
from traderlib import *
from logger import *
import sys

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST

import gvars

# check our trading account
def check_account_ok(api):
    try:
        account = api.get_account()
        if account.status != 'ACTIVE':
            lg.info('The account is not ACTIVE, aborting')
            sys.exit()
    except Exception as e:
        lg.error('Could not get account info, aborting')
        lg.info(str(e))
        sys.exit()

# close current orders
def clean_open_orders(api):

    lg.info('Cancelling all orders...')

    try:
        api.cancel_all_orders()
        lg.info('All orders cancelled')
    except Exception as e:
        lg.error('Could not cancel all orders')
        lg.error(e)
        sys.exit()

def check_asset_ok(api,ticker):
    # check whether the asset is OK for trading
        # IN: ticker
        # OUT: True if it exists and is tradable / False otherwise
    try:
        asset = api.get_asset(ticker)
        if asset.tradable:
            lg.info('Asset exists and tradable')
            return True
        else:
            lg.info('Asset exists but not tradable, exiting')
            sys.exit()
    except Exception as e:
        lg.error('Asset does not exist or something happens!')
        lg.error(e)
        sys.exit()

# execute trading bot
def main():

    api = tradeapi.REST(gvars.API_KEY, gvars.API_SECRET_KEY, gvars.API_URL, api_version='v2')

    # OUT: boolean tradingSuccess (True = success / False = failure)

    # initialize the logger (imported from logger)
    initialize_logger()

    # check our trading account
    check_account_ok(api)

    # close current orders
    clean_open_orders(api)

    # get ticker
    #ticker = input('Write the ticker you want to operate with: ')
    ticker = 'TSLA'

    check_asset_ok(api,ticker)

    trader = Trader(ticker,api) # initialize trading bot

    while True:
        tradingSuccess = trader.run(ticker) # run trading bot library

        if not tradingSuccess:
            lg.info('Trading was not successful, locking asset')
            time.sleep(gvars.sleepTimeME)
        else:
            lg.info('Trading was successful!')
            time.sleep(gvars.sleepTimeME)

if __name__ == '__main__':
    main()
