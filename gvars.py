# encoding: utf-8

# REST API
API_KEY = "PK3T8KO3Z8ZL87PQY6SJ"
API_SECRET_KEY = "6DYWTL5MiNR3kkdOUd8KiU5S85Opq43Kd6DChzQ3"
API_URL = "https://paper-api.alpaca.markets"

stopLossMargin = 0.01 # percentage margin for the stop loss
# example: 10 - (10*0.05) = 9.5 means that my stoploss is at 9.5$

takeProfitMargin = 0.01 # percentage margin for the take profit
# example: 10 + (10*0.1) = 11 means that my take profit is at 11$

maxSpentEquity = 5000 # total equity to spend in a single operation

# LIMIT PRICES
maxVar = 0.02 # max variation percentage when buying/selling

# MAX ATTEMPTS SECTION
maxAttemptsCP = 10 # CHECK POSTION
maxAttemptsGCP = 5 # GET CURRENT PRICE
maxAttemptsGGT = 10 # GET GENERAL TREND
maxAttemptsGIT = 20 # GET INSTANT TREND
maxAttemptsRSI = 20 # GET RSI TREND
maxAttemptsSTC = 20 # GET STOCHASTIC
maxAttemptsCPO = 5 # CHECK PENDING POSITION
maxAttemptsEPM = 360 # ENTER POSITION MODE
maxAttemptsGAEP = 5 # GET AVERAGE ENTRY PRICE

# SLEEP TIMES SECTION (seconds)
sleepTimeCP = 5 # CHECK POSITION
sleepTimeGCP = 5 # GET CURRENT PRICE
sleepTimeGGT = 60 # GET GENERAL TREND
sleepTimeGIT = 30 # GET INSTANT TREND
sleepTimeRSI = 30 # GET RSI TREND
sleepTimeSTC = 20 # GET STOCHASTIC
sleepTimeCPO = 5 # CHECK PENDING POSITION
sleepTimeEPM = 10 # ENTER POSITION MODE
sleepTimeGAEP = 5 # GET AVERAGE ENTRY PRICE
sleepTimeME = 60*60 # MAIN EXECUTION AFTER FAILING
