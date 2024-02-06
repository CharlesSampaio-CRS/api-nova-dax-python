from datetime import datetime
import json
import math
from constants.constants import NOVA_DAX_HOST, NOVA_DAX_KEY, SECRET_DAX_KEY, URL_MONGO
from flask import Flask, jsonify
from pymongo import MongoClient
from novadax import RequestClient as NovaClient
from coinmarketcapapi import CoinMarketCapAPI


app = Flask(__name__)

nova_client = NovaClient(NOVA_DAX_KEY, SECRET_DAX_KEY)
cmc = CoinMarketCapAPI()
client = MongoClient(URL_MONGO)

db = client['cryptbot']
collection = db['balance']

#Get Balance Nova Dax 
@app.route(NOVA_DAX_HOST + "/webhook")
def web_hook_asset():
    data_quote = cmc.cryptocurrency_quotes_latest(symbol='ETH', convert='BRL')
    return json.dumps(str(data_quote))

#Get Balance Nova Dax 
@app.route(NOVA_DAX_HOST + "/balance")
def get_nova_dax_balance():
    try:
        response_data = nova_client.get_account_balance()['data']
        crypto_list = []
        total_amount = 0.0

        for crypto in response_data:
            balance = float(crypto['balance'])
            if balance < 1.0:
                continue
            price = get_ticker(crypto['currency'] + '_BRL')
            amount = round(balance * float(price),2)

            crypto_list.append({
                "available": float(crypto['available']),
                "balance": balance,
                "currency": crypto['currency'],
                "price": price,
                "amount": amount
            })
            total_amount += amount

            document = {
            "assets": crypto_list,
            "amount": math.ceil(total_amount * 10 ** 2) / 10 ** 2,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            collection.insert_one(document)
            document["_id"] = str(document["_id"])   
        return jsonify(document)  
    
    except Exception as e:
        return {"message": str(e)}, 500 

#Get Price SYMBOL
def get_ticker(symbol):
    return nova_client.get_ticker(symbol)['data']['lastPrice']

#Verifiry % in 10 minutos 
''' se a crypto selecionada tiver com valor 10% Up -- cria order de venda, se moeda tiver abaixo de 10% e tiver saldo maior que 25 reias. abre order de compra
-- verificar % de variacao da moeda 
-- verificar se nao tem ordem aberta 
-- verificar se tem saldo 

'''

if __name__ == '__main__':
    app.run()

