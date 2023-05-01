import asyncio
import argparse
import itertools
import sys
import logging
from datetime import datetime, timedelta

import aiohttp

# Block with parsing arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "period",
    help="Shows the exchange rates for the number of specified days.",
    type=int,
    choices=range(1, 11),
    metavar='PERIOD'
)
parser.add_argument('--select_currency', '-s', help='Enter currency abbreviation to get its exchange rate')
args = vars(parser.parse_args())
amount_of_days = args["period"]
custom_value = args['select_currency']


def set_dates_from_amount_of_days(amount: int):
    current_day = datetime.today().date()
    dates_from_days = [(current_day - timedelta(days=i)).strftime("%d.%m.%Y") for i in range(amount)]
    return dates_from_days


def convert_to_dict_view(responses_list: tuple):
    responses_list = list(itertools.chain.from_iterable(responses_list))    # Merge two lists into one
    exchange_rates_list = []
    for response_dict, date in responses_list:
        day_exchange_rates = {date: {
            'currency': response_dict['currency'],
            'purchase': response_dict['purchaseRateNB'],
            'sale': response_dict['saleRateNB']
        }}
        exchange_rates_list.append(day_exchange_rates)
    return exchange_rates_list


async def get_exchange_rates(session, date):
    try:
        async with session.get(
                f"https://api.privatbank.ua/p24api/exchange_rates?date={date}"
        ) as response:
            if response.status == 200:
                exchange_rates = await response.json()
                results = []
                if not custom_value:
                    for dict_rate in exchange_rates['exchangeRate']:
                        if "USD" in dict_rate["currency"] or "EUR" in dict_rate["currency"]:
                            results.append((dict_rate, date))
                else:
                    for dict_rate in exchange_rates['exchangeRate']:
                        if custom_value in dict_rate["currency"]:
                            results.append((dict_rate, date))
                    if not results:
                        logging.info('Your currency does not exist!')
                        sys.exit(1)
                return results
            else:
                logging.info(f"Error {response.status}")
    except aiohttp.ClientConnectionError as e:
        logging.error(f'Connection error: {e}')


async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [get_exchange_rates(session, date) for date in dates]
        results = await asyncio.gather(*tasks)
        days = convert_to_dict_view(results)
        return days


if __name__ == "__main__":
    dates = set_dates_from_amount_of_days(amount_of_days)
    rate_days = asyncio.run(main())
    for rate_day in rate_days:
        print(rate_day)
