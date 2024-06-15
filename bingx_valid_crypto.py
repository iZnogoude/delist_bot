import os
import requests

def get_usdt_perpetual_symbols():
    url = 'https://open-api.bingx.com/openApi/swap/v2/quote/contracts'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        symbols = data['result']
        usdt_perpetual_symbols = [symbol for symbol in symbols if symbol['quote_currency'] == 'USDT' and symbol['status'] == 'Trading']
        # print(f"USDT Perpetual Symbols: {usdt_perpetual_symbols}")  # Commented out diagnostic print
        return usdt_perpetual_symbols
    else:
        print(f"Erreur {response.status_code}: Impossible de récupérer les symboles.")
        return []

def get_turnover_24h(symbol):
    url = f'https://open-api.bingx.com/openApi/swap/v2/quote/ticker?symbol={symbol}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['retCode'] == 0 and 'list' in data['result'] and len(data['result']['list']) > 0:
            turnover24h = data['result']['list'][0]['turnover24h']
            print(f"Turnover 24h for {symbol}: {turnover24h}")  # Diagnostic print for turnover 24h
            return turnover24h
        else:
            print(f"Erreur dans la réponse de l'API pour le symbole {symbol}: {data['retMsg']}")
            return None
    else:
        print(f"Erreur {response.status_code}: Impossible de récupérer le turnover pour le symbole {symbol}.")
        return None

def save_symbols_to_file(symbols, filename):
    try:
        # Créer le dossier s'il n'existe pas
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as file:
            for symbol in symbols:
                max_leverage = get_max_leverage(symbol)
                turnover24h = get_turnover_24h(symbol['name'])
                if turnover24h:
                    file.write(f"{symbol['name']} - Levier Max: {max_leverage} - Turnover 24h: {turnover24h}\n")
                else:
                    file.write(f"{symbol['name']} - Levier Max: {max_leverage} - Turnover 24h: Non disponible\n")
        print(f"Liste des cryptos enregistrée dans {filename}")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement dans le fichier: {e}")

def get_max_leverage(symbol):
    return symbol['leverage_filter']['max_leverage']

if __name__ == "__main__":
    usdt_perpetual_symbols = get_usdt_perpetual_symbols()
    if usdt_perpetual_symbols:
        save_symbols_to_file(usdt_perpetual_symbols, 'dossier_txt/bingx_valid_crypto.txt')
    else:
        print("Aucune crypto valide en USDT perpétuel trouvée.")
