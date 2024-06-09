import requests
import json

# Fonction pour récupérer les symboles et les volumes en USDT depuis l'API Bitget
def get_symbols_and_volumes(api_url):
    print("Récupération des symboles et des volumes depuis l'API...")
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Échec de la récupération des données depuis {api_url}")
    
    data = response.json()
    symbols_and_volumes = {item['symbol']: item['usdtVolume'] for item in data['data']}
    print(f"A récupéré {len(symbols_and_volumes)} symboles et volumes.")
    return symbols_and_volumes

# Fonction pour récupérer le levier maximum depuis l'API Bitget
def get_max_leverage(api_url, symbols):
    print("Récupération du levier maximum pour chaque symbole...")
    max_leverage = {}
    for symbol in symbols:
        print(f"Récupération des données pour le symbole : {symbol}")
        response = requests.get(f"{api_url}&symbol={symbol}")
        if response.status_code != 200:
            print(f"Échec de la récupération des données pour {symbol} depuis {api_url}")
            continue
        
        data = response.json()
        if 'data' in data and isinstance(data['data'], list):
            for item in data['data']:
                if item['symbol'] == symbol:
                    max_leverage[symbol] = item['maxLever']
                    print(f"Le levier maximum pour {symbol} est de {item['maxLever']}")
                    break
        elif 'data' in data and isinstance(data['data'], dict):
            max_leverage[symbol] = data['data'].get('maxLever', 'N/A')
            print(f"Le levier maximum pour {symbol} est de {max_leverage[symbol]}")
    return max_leverage

# Fonction principale pour orchestrer les appels d'API et générer le fichier de sortie
def main():
    output_file = 'dossier_txt/bitget_valid_crypto.txt'
    
    api_url_volumes = "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
    api_url_leverage = "https://api.bitget.com/api/v2/mix/market/contracts?productType=usdt-futures"

    symbols_and_volumes = get_symbols_and_volumes(api_url_volumes)
    symbols = list(symbols_and_volumes.keys())
    max_leverage = get_max_leverage(api_url_leverage, symbols)

    print(f"Écriture de la sortie dans {output_file}...")
    with open(output_file, 'w') as file:
        for symbol, volume in symbols_and_volumes.items():
            leverage = max_leverage.get(symbol, 'N/A')
            line = f"{symbol} - Levier Max: {leverage} - Turnover 24h: {volume}\n"
            file.write(line)
            print(f"A écrit {symbol}: Volume={volume}, Levier Max={leverage}")

    print(f"Sortie écrite dans {output_file}")

if __name__ == "__main__":
    main()
