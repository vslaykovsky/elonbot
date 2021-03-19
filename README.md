# Elonbot

Trading bot that uses Elon Musk`s tweets to know when to buy cryptocurrency. 
Here is how it works:

1. Subscribing to someone's ([elonmusk](http://twitter.com/elonmusk)?) tweets 
2. Automatically detecting mentions of DOGE or other crypto in the image(or text) 
![Elon's tweet](elontweet.png)
3. Buying crypto on [Binance](http://www.ya.ru)
4. Selling it after --auto-sell-delay seconds


## Installation

git clone http://github.com/vslaykovsky/elonbot
pip install binance-python google-cloud-vision


## Running

1. Set up Twitter access keys. 
    * Go to [developer.twitter.com](https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api) to create your developer account 
    * Generate a [bearer token](https://developer.twitter.com/en/docs/authentication/oauth-2-0/bearer-tokens)
    * Set up an environment variable with the bearer token: ```export TWITTER_BEARER_TOKEN=<YOUR BEARER TOKEN>``` 
2. Set up Binance access keys.
    * Go to [Binance](https://www.binance.com/en) and create a trader account if you don't have it yet
    * Go to [API management](https://www.binance.com/en/my/settings/api-management) page and copy your API key and secret
    * Export both keys: ```export BINANCE_KEY=<your API key>; export BINANCE_SECRET=<your secret key>```
3. [Optional] Add image text recognition support with Google OCR
    * Use the [following documentation](https://cloud.google.com/vision/docs/setup) to access Google Vision API
    * Export path to your google vision configuration: ```export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/google_vision_credentials.json```
4. Run elonbot.py

```shell
python elonbot.py 
  --user=elonmusk 
  --margin-type=cross_margin 
  --crypto-rules="{\"doge\": \"DOGE\", \"btc|bitcoin\": \"BTC\"}" 
  --auto-sell-delay=600 
  --order-size=max
```
