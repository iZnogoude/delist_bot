import os
import re
import requests
import schedule
import time
from datetime import datetime
from telethon import TelegramClient, events
import subprocess
import asyncio
import hmac
import hashlib
import base64
import json
import sys
import ccxt

# Charger les paramètres depuis le fichier config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Extraire les paramètres
api_id = config['api_id']
api_hash = config['api_hash']
phone_number = config['phone_number']
channel_username = config['channel_username']
webhook_url = config['webhook_url']
username = config['username']
percentage = config['percentage']
exchange_choice = config['exchange_choice']

bitget_api_key = config['bitget_api_key']
bitget_api_secret = config['bitget_api_secret']
bitget_passphrase = config['bitget_passphrase']
symbol = 'BTCUSDT'
product_type = 'umcbl'
margin_coin = 'USDT'
wallet_balance_file = 'bitget_wallet_balance.txt'

# Créer une instance de l'exchange Bitget via CCXT
exchange = ccxt.bitget({
    'apiKey': bitget_api_key,
    'secret': bitget_api_secret,
    'password': bitget_passphrase,
    'options': {
        'defaultType': 'swap',
    }
})

if exchange_choice == 'bybit':
    valid_crypto_file = 'dossier_txt/bybit_valid_crypto.txt'
    script_file = 'bybit_valid_crypto.py'
    output_file = 'dossier_txt/binance_delisting.txt'
elif exchange_choice == 'bitget':
    valid_crypto_file = 'dossier_txt/bitget_valid_crypto.txt'
    script_file = 'bitget_valid_crypto.py'
    output_file = 'dossier_txt/binance_delisting.txt'

# Créer le répertoire s'il n'existe pas
os.makedirs('dossier_txt', exist_ok=True)

# Lire les cryptos valides et leurs informations supplémentaires à partir du fichier
valid_cryptos = {}
with open(valid_crypto_file, 'r', encoding='utf-8') as f:
    for line in f:
        parts = line.split(' - ')
        crypto_name = parts[0]
        additional_info = ' - '.join(parts[1:])
        turnover_str = re.search(r'Turnover 24h: ([\d.]+)', parts[-1])
        max_leverage_str = re.search(r'Levier Max: (\d+)', additional_info)
        if turnover_str and max_leverage_str:
            turnover = float(turnover_str.group(1))
            max_leverage = int(max_leverage_str.group(1))
            valid_cryptos[crypto_name] = {'info': additional_info, 'turnover': turnover, 'max_leverage': max_leverage}

# Fonction pour exécuter le script bybit_valid_crypto.py
def run_exchange_valid_crypto():
    process = subprocess.Popen([sys.executable, script_file])
    process.wait()  # Attendre que le processus enfant se termine
    print(f"--------------------------------------\n  Le bot de délisting est en marche.\n{percentage}% des fonds sont alloués sur {exchange_choice}.\n--------------------------------------")
    # Une fois le processus terminé, reconnectez-vous à l'écoute des événements Telegram
    client.loop.create_task(main())

# Planification de l'exécution du script every 24 hours
schedule.every().day.at("12:00").do(run_exchange_valid_crypto)

# Créer une nouvelle instance du client
client = TelegramClient('session_name', api_id, api_hash)

def get_server_time():
    response = requests.get('https://api.bitget.com/api/v2/public/time')
    if response.status_code == 200:
        data = response.json()
        server_time = data['data']['serverTime']
        return int(server_time)
    else:
        print("Erreur lors de la récupération de l'horodatage du serveur.")
        print("Code de réponse:", response.status_code)
        print("Message:", response.text)
        return None

def get_bitget_wallet_balance():
    server_timestamp = get_server_time()
    if not server_timestamp:
        return None

    local_timestamp = str(server_timestamp)
    method = 'GET'
    request_path = f'/api/v2/mix/account/account?symbol={symbol}&productType={product_type}&marginCoin={margin_coin}'  # Chemin de l'API pour les comptes

    # Crée la signature pour l'authentification
    prehash_string = local_timestamp + method + request_path
    signature = hmac.new(bitget_api_secret.encode('utf-8'), prehash_string.encode('utf-8'), hashlib.sha256).digest()
    signature_base64 = base64.b64encode(signature).decode()

    headers = {
        'ACCESS-KEY': bitget_api_key,
        'ACCESS-SIGN': signature_base64,
        'ACCESS-TIMESTAMP': local_timestamp,
        'ACCESS-PASSPHRASE': bitget_passphrase,
        'Content-Type': 'application/json'
    }

    # Faire la requête GET pour obtenir le solde du portefeuille
    response = requests.get('https://api.bitget.com' + request_path, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and isinstance(data['data'], dict):
            max_available = data['data'].get('maxTransferOut', 'N/A')
            with open(wallet_balance_file, 'w', encoding='utf-8') as f:
                f.write(str(max_available))
            print(f"Le montant 'maxTransferOut' du portefeuille est : {max_available} USDT")
            return max_available
        else:
            print("Format de réponse inattendu ou données manquantes.")
    else:
        print("Erreur lors de la récupération du solde du portefeuille.")
        print("Code de réponse:", response.status_code)
        print("Message:", response.text)
    return None

def scheduled_wallet_balance_check():
    schedule.every().hour.do(get_bitget_wallet_balance)
    while True:
        schedule.run_pending()
        time.sleep(1)

async def main():
    print(f"--------------------------------------\n  Le bot de délisting est en marche.\n{percentage}% des fonds sont alloués sur {exchange_choice}.\n--------------------------------------")
    await client.start(phone=phone_number)
    channel = await client.get_entity(channel_username)

    async def process_message(message_content):
        print(f"Message reçu : {message_content}")
        extracted_info = re.search(r'Binance Will Delist (.*?) on', message_content)
        if extracted_info:
            crypto_list = extracted_info.group(1).strip().split(', ')
            highest_turnover_crypto = None
            highest_turnover = -1
            for crypto in crypto_list:
                crypto_with_usdt = f"{crypto}USDT"
                if crypto_with_usdt in valid_cryptos:
                    turnover = valid_cryptos[crypto_with_usdt]['turnover']
                    if turnover > highest_turnover:
                        highest_turnover = turnover
                        highest_turnover_crypto = crypto_with_usdt

            if highest_turnover_crypto:
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(f"{highest_turnover_crypto} - {valid_cryptos[highest_turnover_crypto]['info']}\n")
                print(f"Nouvelle crypto trouvée : {highest_turnover_crypto}")
                max_leverage = valid_cryptos[highest_turnover_crypto]['max_leverage']
                max_transfer_out = get_bitget_wallet_balance()
                if max_transfer_out is not None:
                    short_amount = round((float(max_transfer_out) * percentage) / 100)
                    message = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {username} {highest_turnover_crypto} sell {short_amount} x{max_leverage} force_usdt'
                    print(f"Envoi du message : {message}")
                    try:
                        response = requests.post(webhook_url, data=message)
                        print(f"Webhook response: {response.status_code}, {response.text}")
                        if response.status_code == 200:
                            print("Webhook envoyé avec succès.")
                        else:
                            print("Échec de l'envoi du webhook.")
                    except requests.exceptions.RequestException as e:
                        print(f"Erreur lors de l'envoi du webhook : {e}")

    async for message in client.iter_messages(channel, limit=1):
        if message.message:
            await process_message(message.message)

    @client.on(events.NewMessage(chats=channel))
    async def new_message_listener(event):
        if event.message.message:
            await process_message(event.message.message)

    await client.run_until_disconnected()

# Fonction pour exécuter les tâches planifiées
def run_scheduled_tasks():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Exécuter la vérification du solde du portefeuille dans un thread séparé
    from threading import Thread
    thread = Thread(target=scheduled_wallet_balance_check)
    thread.start()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

# Lancer immédiatement la récupération du solde du portefeuille
print("Lancement initial de la récupération du solde du portefeuille...")
initial_balance = get_bitget_wallet_balance()
if initial_balance is None:
    print("Échec de la récupération du solde initial. Vérifiez votre connexion et vos informations d'authentification.")

with client:
    # Exécuter les tâches planifiées dans un thread séparé
    from threading import Thread
    thread = Thread(target=run_scheduled_tasks)
    thread.start()
    
    client.loop.run_until_complete(main())
