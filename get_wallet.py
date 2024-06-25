import requests
import hmac
import hashlib
import base64

# URL des infos de comptes chez bitget /api/v2/mix/account/account
# URL du serveur time https://api.bitget.com/api/v2/public/time

# Remplacez par vos informations d'authentification Bitget
bitget_api_key = 'bg_d63c6918af84afd109fd595167220c49'
bitget_api_secret = '222cff1b2712ffcc7e0bb61f40140a43baaf41533431431cecc77ad2a81154cf'
bitget_passphrase = '6ZWjA6XYwmBGcDnvr5ZvAzzCGQf9pZ3T'

# Spécifiez le symbole ici, par exemple 'BTCUSDT'
symbol = 'BTCUSDT'
# Spécifiez le type de produit, par exemple 'umcbl'
# umcbl USDT perpetual contract
# dmcbl Universal margin perpetual contract
# cmcbl USDC perpetual contract
# sumcbl USDT simulation perpetual contract
# sdmcbl Universal margin simulation perpetual contract
# scmcbl USDC simulation perpetual contract

product_type = 'umcbl'
# Spécifiez le margin coin, par exemple 'USDT'
margin_coin = 'USDT'

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
        return

    local_timestamp = str(server_timestamp)
    method = 'GET'
    request_path = f'/api/v2/mix/account/account?symbol={symbol}&productType={product_type}&marginCoin={margin_coin}'  # Chemin de l'API pour les comptes

    # Crée la signature pour l'authentification
    prehash_string = local_timestamp + method + request_path
 #   print("Prehash String:", prehash_string)  # Debugging line
    signature = hmac.new(bitget_api_secret.encode('utf-8'), prehash_string.encode('utf-8'), hashlib.sha256).digest()
    signature_base64 = base64.b64encode(signature).decode()
 #   print("Signature:", signature_base64)  # Debugging line

    headers = {
        'ACCESS-KEY': bitget_api_key,
        'ACCESS-SIGN': signature_base64,
        'ACCESS-TIMESTAMP': local_timestamp,
        'ACCESS-PASSPHRASE': bitget_passphrase,
        'Content-Type': 'application/json'
    }

#    print("Headers:", headers)  # Debugging line

    # Faire la requête GET pour obtenir le solde du portefeuille
    response = requests.get('https://api.bitget.com' + request_path, headers=headers)

    if response.status_code == 200:
        data = response.json()
#        print("Réponse JSON brute:", data)  # Debugging line
        if 'data' in data and isinstance(data['data'], dict):
            max_available = data['data'].get('maxTransferOut', 'N/A')    #Variable maxTransferOut ou crossedMaxAvailable
            print(f"Le montant 'maxTransferOut' du portefeuille est : {max_available} USDT")
        else:
            print("Format de réponse inattendu ou données manquantes.")
    else:
        print("Erreur lors de la récupération du solde du portefeuille.")
        print("Code de réponse:", response.status_code)
        print("Message:", response.text)

# Appeler la fonction pour tester
get_bitget_wallet_balance()
