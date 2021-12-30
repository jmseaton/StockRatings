from time import sleep

import finnhub


# Setup client
finnhub_client = finnhub.Client(api_key="sandbox_c71nnkaad3ieuiu4d00g")

updown = finnhub_client.upgrade_downgrade()
symbols = [i["symbol"] for i in updown]
print(finnhub_client.covid19())
#for symbol in symbols:
#    print(finnhub_client.price_target(symbol).get('targetLow'))
#    sleep(10)
