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


async def fetch_profile_data():
    
   print("response")
   send_message("Algo Start")    

async def place_target_order(order_type,side,order_product,order_size,stop_order_type,stop_price):
    # Define the payload
    payload = {
        "order_type": order_type,
        "side": side,
        "product_id": int(order_product),
        "stop_order_type": stop_order_type,
        "stop_price": stop_price,
        "reduce_only": False,
        "stop_trigger_method": "mark_price",
        "size": order_size
    }
    # Fetch data from REST API
    # Fetch data from REST API
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

    # Send the POST request with the payload
    response = requests.post('https://cdn.india.deltaex.org/v2/orders', json=payload, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        print("Order placed successfully.")
        message = f"😀New Order:\n" \
          f"Order Type: {payload['order_type']}\n" \
          f"Side: {payload['side']}\n" \
          f"Product ID: {payload['product_id']}\n" \
          f"Stop Order Type: {payload['stop_order_type']}\n" \
          f"Stop Price: {payload['stop_price']}\n" \
          f"Reduce Only: {payload['reduce_only']}\n" \
          f"Stop Trigger Method: {payload['stop_trigger_method']}\n" \
          f"Size: {payload['size']}😀"
        send_message(message)
    else:
        print("Failed to place order. Status code:", response.status_code)

        
async def place_order(order_type,side,order_product_id,order_size,stop_order_type,target_value ):
    # Define the payload
    payload = {
        "order_type": order_type,
        "side": side,
        "product_id": int(order_product_id),
        "reduce_only": False,     
        "size": order_size
    }
    
    # Fetch data from REST API
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
    # Send the POST request with the payload
    response = requests.post('https://cdn.india.deltaex.org/v2/orders', json=payload, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        message = f"😀New Order:\n" \
          f"Order Type: {payload['order_type']}\n" \
          f"Side: {payload['side']}\n" \
          f"Product ID: {payload['product_id']}\n" \
          f"Reduce Only: {'Yes' if payload['reduce_only'] else 'No'}\n" \
          f"Size: {payload['size']}😀"
        send_message(message)
        await place_target_order("market_order","buy",order_product_id,1,"take_profit_order",target_value )
    else:
        send_message(response)

async def fetch_position_data():
    last_sent_time = 0  # Last time message was sent

    while True:
        # Fetch data from REST API
        payload = ''
        method = 'GET'
        endpoint = '/v2/positions/margined'
        payload_str = json.dumps(payload)
        signature, timestamp = generate_signature(method, endpoint, payload)
        timestamp = get_time_stamp() 

        headers = {
         'api-key': api_key,
         'timestamp': timestamp,
         'signature': signature,
         'User-Agent': 'rest-client',
         'Content-Type': 'application/json'
        }

        r = requests.get('https://cdn.india.deltaex.org/v2/positions/margined', headers=headers)
        position_data = r.json()  

        

        for result in position_data["result"]:
            product_id = result["product_id"]
            product_symbol = result["product_symbol"]
            realized_cashflow = result["realized_cashflow"]
            realized_funding = result["realized_funding"]
            realized_pnl = result["realized_pnl"]
            size = result["size"]
            unrealized_pnl = result["unrealized_pnl"]
            updated_at = result["updated_at"]
            user_id = result["user_id"]
            entry_price = result["entry_price"]
            mark_price = result["mark_price"]

            percentage = int(size)  
            avg_price_value = float(entry_price) - (float(entry_price) * (percentage / 100)) 
            add_price_value = float(entry_price) + (float(entry_price) * (percentage / 100)) 
            digit_count = count_digits_after_point(mark_price)
            tick_size = 1 / digit_count
            target = float(mark_price) - float(mark_price) * 2.5 / 100
            number = round((target / tick_size) * tick_size, digit_count)
            target_value = number
            decimal_number = scientific_to_decimal(number)

            message = f"Symbol: {product_symbol}\n" \
                      f"Size: {size}\n" \
                      f"Unrealized PnL    : {round((float(unrealized_pnl)), digit_count)}\n" \
                      f"Position Avg Price: {round((float(entry_price)), digit_count)}\n" \
                      f"Next_Avg_price    : {round((float(avg_price_value)), digit_count)}\n" \
                      f"Next_Add_price    : {round((float(add_price_value)), digit_count)}\n" \
                      f"Mark Price        : {round((float(mark_price)), digit_count)}\n" 
                      
        
            print(message)

           # **Check if 60 seconds have passed before sending "Algo Live"**
        current_time = time.time()
        if current_time - last_sent_time >= 60:
            send_message(message)
            last_sent_time = current_time  # Update last sent time
            
            if (float(mark_price) > avg_price_value) or (float(mark_price) < add_price_value):
                print("Ready to Sell")
                await place_order("market_order", "sell", product_id, 1, 0, target_value)

           # **Check if 60 seconds have passed before sending "Algo Live"**
        current_time = time.time()
        if current_time - last_sent_time >= 60:
            send_message(message)
            last_sent_time = current_time  # Update last sent time

        await asyncio.sleep(10)  # 10-second interval


def count_digits_after_point(number):
    # Convert the number to a string
    number_str = str(number)
    
    # Split the string at the decimal point
    parts = number_str.split('.')
    
    # Check if there is a decimal part
    if len(parts) == 2:
        # Return the length of the decimal part
        return len(parts[1])
    else:
        # Return 0 if there is no decimal part
        return 0

def scientific_to_decimal(number):
    # Convert the number to a Decimal and return as string
    decimal_number = Decimal(number)
    return str(decimal_number)

def send_message(message):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    params = {'chat_id': chat_id, 'text': message}

    response = requests.post(url, json=params)
    if response.status_code == 200:
        print('Message sent successfully!')
    else:
        print(f'Failed to send message. Error: {response.status_code} - {response.text}')

def auto_topup(message):
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'api-key': '****',
      'signature': '****',
      'timestamp': '****'
      }

    r = requests.put('https://api.delta.exchange/v2/positions/auto_topup', params={
    "product_id": 0,
    "auto_topup": "false"
    }, headers = headers)
    print(r.json())


async def main():
    while True:
        try:
            profile_task = asyncio.create_task(fetch_profile_data())
            position_task = asyncio.create_task(fetch_position_data())
            await asyncio.gather(position_task, profile_task)
        except Exception as e:
            print(f"An error occurred: {e}")
            # Optionally, you can add code here to handle the error, such as logging it
            # or sending a notification
        finally:
            # Optionally, you can add a delay here before retrying
            await asyncio.sleep(30)
    

# Run the main coroutine
asyncio.run(main())
