import os
import re
import requests
import schedule
import time
from datetime import datetime
from telethon import TelegramClient, events
import subprocess
import asyncio

# Remplacez par vos informations
api_id = '21792675'
api_hash = '7962c5e570690dc344d6d47dda7a99f0'
phone_number = '+33777040699'
channel_username = 'coin_listing'   #Canal telegram à écouter:coin_listing  #Canal telegram pour test:AnonymousChatGroupTiga
output_file = 'dossier_txt/binance_delisting.txt'
valid_crypto_file = 'dossier_txt/bybit_valid_crypto.txt'
webhook_url = 'http://localhost/whook'
username = 'jfmayol'
percentage = 90

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
def run_bybit_valid_crypto():
    process = subprocess.Popen(["python", "bybit_valid_crypto.py"])
    process.wait()  # Attendre que le processus enfant se termine
    print("Le bot est en marche et récupère les messages...")  # Ajout de cet instruction
    # Une fois le processus terminé, reconnectez-vous à l'écoute des événements Telegram
    client.loop.create_task(main())


# Planification de l'exécution du script every 24 hours à minuit
schedule.every().day.at("00:00").do(run_bybit_valid_crypto)

# Créer une nouvelle instance du client
client = TelegramClient('session_name', api_id, api_hash)

async def main():
    print("Le bot est en marche et récupère les messages...")
    await client.start(phone=phone_number)
    channel = await client.get_entity(channel_username)

    async def process_message(message_content):
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
                message = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {username} {highest_turnover_crypto} sell {percentage}% x{max_leverage}'
                print(f"Envoi du message : {message}")
                response = requests.post(webhook_url, data=message)
                if response.status_code == 200:
                    print("Webhook envoyé avec succès.")
                else:
                    print("Échec de l'envoi du webhook.")

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
    
    while True:
        schedule.run_pending()
        time.sleep(1)

with client:
    # Exécuter les tâches planifiées dans un thread séparé
    from threading import Thread
    thread = Thread(target=run_scheduled_tasks)
    thread.start()
    
    client.loop.run_until_complete(main())