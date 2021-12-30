#!/usr/bin/python3
import configparser
import requests
import logging
import os
import sys
import json
from datetime import datetime, timedelta

__author__ = 'jared seaton'

# Get script path
pathname = os.path.dirname(sys.argv[0])
script_path = os.path.abspath(pathname)

# config file named finnhub.cfg, with a "Settings"
# section for finnhub api authentication token.
# This should contain the vars: token
finnhubCfg = configparser.RawConfigParser()
finnhubCfg.read(script_path + "/finnhub.cfg")
token = finnhubCfg.get("Settings", "token")

# define the logging
logging.basicConfig(filename=script_path + '/ratings.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# set variables
today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)
endpoint = 'upgrade-downgrade'
updown_url = 'https://finnhub.io/api/v1/stock/upgrade-downgrade?' + '&token=' + token
targets_url = 'https://finnhub.io/api/v1/stock/price-target?' + '&token=' + token + '&symbol='
powerbi_url = 'https://api.powerbi.com/beta/b67d722d-aa8a-4777-a169-ebeb7a6a3b67/datasets/' \
              '520ae51f-637f-4efd-96be-dad192e05be4/rows?key=xOihNIQCsJUKPN0QCs93Ni3JCw0UL' \
              'xfuul7LXbsyqDrprXUnu6NFehkGrhbxvnfxt9SZs3lQDqLdQjBstxp13g%3D%3D'


def submit_metrics():
    ratingdict = {
        "Buy": "1",
        "Strong Buy": "1",
        "Market Perform": "2",
        "Sector Perform": "2",
        "Outperform": "2",
        "Overweight": "2",
        "Market Outperform": "2",
        "Speculative Buy": "2",
        "Moderate Buy": "2",
        "Accumulate": "2",
        "Add": "2",
        "Neutral": "3",
        "Equal-Weight": "3",
        "In-Line": "3",
        "Hold": "3",
        "Sector Weight": "3",
        "Equalweight": "3",
        "Market Weight": "3",
        "Underperform": "4",
        "Underweight": "4",
        "Moderate Sell": "4",
        "Weak Hold": "4",
        "Reduce": "4",
        "Sell": "5",
        "Strong Sell": "5"
    }

    # make the GET request for upgrades/downgrades
    rating_change = requests.get(updown_url, verify=True)

    # iterate through the data
    for rating in rating_change.json():
        # setting some variables for easier access
        toGrade = int(ratingdict.get(rating["toGrade"]))
        if ratingdict.get(rating["fromGrade"]) is None:
            fromGrade = 0
        else:
            fromGrade = int(ratingdict.get(rating["fromGrade"]))
        symbol = rating["symbol"]
        company1 = rating["company"].replace(',', '')
        action = rating["action"]
        date = datetime.fromtimestamp(rating["gradeTime"]).date()

        logging.debug("finnhub rating return code:" + str(rating_change.status_code))

        # we only want the latest data, so check gradeTime vs "yesterday"
        if datetime.fromtimestamp(rating["gradeTime"]).date() > yesterday:

            # pull target price data for each symbol
            targets_url = 'https://finnhub.io/api/v1/stock/price-target?' + '&token=' + token + '&symbol=' + symbol
            stock_targets_get = requests.get(targets_url, verify=True)
            logging.debug("finnhub target return code:" + str(stock_targets_get.status_code))

            # pull current price data for each symbol
            price_url = 'https://finnhub.io/api/v1/quote?symbol=' + symbol + '&token=' + token
            stock_price_get = requests.get(price_url, verify=True)
            logging.debug("finnhub price return code:" + str(stock_price_get.status_code))

            stock_targets = stock_targets_get.json()
            stock_price = stock_price_get.json()

            stock_data_string = [{"toGrade": toGrade, "gradeTime": str(date), "symbol": symbol, "company": company1,
                                  "fromGrade": fromGrade, "action": action, "targetHigh": stock_targets["targetHigh"],
                                  "targetLow": stock_targets["targetLow"], "targetMean": stock_targets["targetMean"],
                                  "targetMedian": stock_targets["targetMedian"], "currentPrice": stock_price["c"]}]

            # convert to json
            stock_data_json = json.dumps(stock_data_string)
            logging.debug("stock data:" + stock_data_string)

            # send metrics to powerbi
            powerbi_push = requests.post(powerbi_url, json=stock_data_string)
            logging.debug("powerbi return code:" + str(powerbi_push.status_code))
            logging.debug("powerbi response:" + powerbi_push.content)


# Verify connection is working properly
verify_url = requests.get(updown_url, verify=True)

# check whether api verify was successful, then execute, or error if it failed
if verify_url.status_code != 200:
    logging.critical("Unable to connect to isilon host: " + verify_url)
if verify_url.status_code == 200:
    submit_metrics()
