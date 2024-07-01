# Binance future delisting bot 

[![Python version](https://img.shields.io/pypi/pyversions/binance-futures-connector)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This is a future trading bot that detects when Binance announces that a cryptocurrency is going to be removed from its list.
### How it works:
The bot lists all the crypto-currencies of your broker in a file.
A routine detects delisting announcements from a Binance telegram channel and as soon as the announcement is published, the bot shorts this cryptocurrency with maximum leverage. If several cryptonies are delisted, it chooses the one with the highest volume and the highest leverage available.
A variable allows you to allocate a percentage of your portfolio to this trad. If you want other leverage effects, you will need to modify the code.
For your information, Binance is the world's biggest broker in terms of trading volume. As soon as it announces that it is going to delist a cryptocurrency, its price drops instantly. This is due to all the other delisting bot  ^_^

It is working with whook from germangar https://github.com/germangar/whook

### Installation
#### Telegram API
First of all you need to create an API application on telegram. Go to this page and gollow the instructions https://core.telegram.org/api/obtaining_api_id
It's quite simple but you could struggle a little bit with telegram application creation (it's a little bit buggy) ^_^

You will get an api_id and a api_hash. That's the only things important for the delist_bot usage.

#### Requirements
The bot is coded in Python, make sure phyton 3 is installed on your server.
For the whook you need already ccxt and flask python modules
