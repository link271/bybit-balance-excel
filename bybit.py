import requests
import time
import hashlib
import hmac
import uuid
import json
import pandas as pd
import datetime


API_KEY = 'YOUR_API_KEY'
SECRET_KEY ='YOUR_SECRET_KEY'
httpClient = requests.session()
recv_window = str(5000)
url ='https://api.bybit.com'


def HTTP_Request(endpoint,method,payload,Info):
    global time_stamp
    time_stamp = str(int(time.time() * 10 **3))
    signature = gen_signature(payload)
    headers = {
        'X-BAPI-API-KEY': API_KEY,
        'X-BAPI-SIGN': signature,
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    if(method=='POST'):
        response = httpClient.request(method,url+endpoint,headers=headers,data=payload)
    else:
        response = httpClient.request(method,url+endpoint+"?"+payload,headers=headers)
    return response

def gen_signature(payload):
    param_str = str(time_stamp) + API_KEY+recv_window+payload
    bybit_hash = hmac.new(bytes(SECRET_KEY,"utf-8"),param_str.encode('utf-8'),hashlib.sha256)
    signature = bybit_hash.hexdigest()
    return signature

def get_total_balances_funding_wallet():
    endpoint_funds = "/asset/v3/private/transfer/account-coins/balance/query"
    method = "GET"
    payload_funds = 'accountType=FUND'
    fund_wallet_balances=HTTP_Request(endpoint_funds,method,payload_funds,"Get Wallet Balance").text
    balance_json = json.loads(fund_wallet_balances)
    total_balances =0
    for item in balance_json['result']['balance']:
        if(item['walletBalance'] and float(item['walletBalance'])>0):
            if(item['coin']=='USDT'):
                total_balances+=float(item['walletBalance'])
            else:
                total_balances+= get_token_price(item['coin'])* float(item['walletBalance'])
    return total_balances

def get_total_balances_unified_wallet():
    endpoint = "/v5/account/wallet-balance"
    method = "GET"
    payload = 'accountType=UNIFIED'
    unified_wallet_balances = HTTP_Request(endpoint,method,payload,"Get Wallet Balance").text
    balance_json = json.loads(unified_wallet_balances)

    total_balances = float(balance_json['result']['list'][0]['totalEquity'])
    return total_balances

def get_token_price(token):
    endpoint = "/v5/market/tickers"
    method = "GET"
    payload = f'category=spot&symbol={token}USDT'
    res = HTTP_Request(endpoint,method,payload,"Get Price")
    if(res.status_code==200):
        return float(res.json()['result']['list'][0]['lastPrice'])


def calc_total_bal():
    #Your INIT balance
    INIT_USDT = 999999
    v3_balances = get_total_balances_funding_wallet()
    v5_balances = get_total_balances_unified_wallet()
    total_balances = v3_balances + v5_balances
    # print(total_balances)
    df = pd.read_excel('bybit_updated.xlsx','Sheet2')
    usdt_balances = total_balances + df['Current Stake USDT'][0]
    profit = usdt_balances- INIT_USDT
    new_df = pd.DataFrame(index=(df.index.max()+1,),columns=df.columns,data =[[usdt_balances, datetime.datetime.now(),profit, df['Current Stake USDT'][0]]])
    df = pd.concat([df, new_df], axis=0)
    print(df)
    df.to_excel('bybit_updated.xlsx','Sheet2',index=False)


calc_total_bal()
