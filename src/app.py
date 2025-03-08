import requests
import asyncio
import json
import time
import datetime
import hashlib
import hmac
import base64
import os
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch values from .env
api_key = os.getenv('DELTA_API_KEY')
api_secret = os.getenv('DELTA_API_SECRET')
bot_token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')

def generate_signature(method, endpoint, payload):
    timestamp = str(int(time.time()))
    signature_data = method + timestamp + endpoint + payload
    message = bytes(signature_data, 'utf-8')
    secret = bytes(api_secret, 'utf-8')
    hash = hmac.new(secret, message, hashlib.sha256)
    return hash.hexdigest(), timestamp

def get_time_stamp():
    d = datetime.datetime.utcnow()
    epoch = datetime.datetime(1970,1,1)
    return str(int((d - epoch).total_seconds()))

def send_message(message):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    params = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, json=params)
    if response.status_code == 200:
        print('Message sent successfully!')
    else:
        print(f'Failed to send message. Error: {response.status_code} - {response.text}')

async def fetch_profile_data():
    print("Fetching profile data...")
    send_message("Algo Start")

async def place_order(order_type, side, order_product_id, order_size, stop_order_type, target_value):
    payload = {
        "order_type": order_type,
        "side": side,
        "product_id": int(order_product_id),
        "reduce_only": False,
        "size": order_size
    }
    
    method = 'POST'
    endpoint = '/v2/orders'
    payload_str = json.dumps(payload)
    signature, timestamp = generate_signature(method, endpoint, payload_str)
    timestamp = get_time_stamp()
    
    headers = {
        'api-key': api_key,
        'timestamp': timestamp,
        'signature': signature,
        'User-Agent': 'rest-client',
        'Content-Type': 'application/json'
    }
    
    response = requests.post('https://cdn.india.deltaex.org/v2/orders', json=payload, headers=headers)
    
    if response.status_code == 200:
        message = f"New Order:\nOrder Type: {payload['order_type']}\nSide: {payload['side']}\nProduct ID: {payload['product_id']}\nReduce Only: {'Yes' if payload['reduce_only'] else 'No'}\nSize: {payload['size']}"
        send_message(message)
    else:
        send_message(f"Failed to place order: {response.text}")

async def fetch_position_data():
    while True:
        payload = ''
        method = 'GET'
        endpoint = '/v2/positions/margined'
        signature, timestamp = generate_signature(method, endpoint, payload)
        timestamp = get_time_stamp()
        
        headers = {
            'api-key': api_key,
            'timestamp': timestamp,
            'signature': signature,
            'User-Agent': 'rest-client',
            'Content-Type': 'application/json'
        }
        
        response = requests.get('https://cdn.india.deltaex.org/v2/positions/margined', headers=headers)
        position_data = response.json()
        
        for result in position_data.get("result", []):
            product_symbol = result["product_symbol"]
            size = result["size"]
            mark_price = float(result["mark_price"])
            entry_price = float(result["entry_price"])
            avg_price_value = entry_price * 0.98
            
            message = f"Symbol: {product_symbol}\nSize: {size}\nMark Price: {mark_price}\nNext Avg Price: {avg_price_value}"
            print(message)
            send_message(message)
            
        await asyncio.sleep(10)

async def main():
    while True:
        try:
            profile_task = asyncio.create_task(fetch_profile_data())
            position_task = asyncio.create_task(fetch_position_data())
            await asyncio.gather(position_task, profile_task)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await asyncio.sleep(30)

asyncio.run(main())
