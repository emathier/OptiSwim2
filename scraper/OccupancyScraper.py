# Goal of this script is to fetch occupancy data and store in a mysql db. Important here is that needs to inform us if it fails the collect data.
import websocket
import datetime
import json
import mysql.connector
from mysql.connector import Error
import pytz
import sentry_sdk
from sentry_sdk import capture_message
from sentry_sdk import capture_exception
import time
import os
from dotenv import load_dotenv

load_dotenv()



sentry_sdk.init(
    dsn=os.getenv("SENTRY_KEY"),
    traces_sample_rate=1.0,

    # To set a uniform sample rate
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production,
    profiles_sample_rate=1.0,
)


with sentry_sdk.start_transaction(op="task", name="Start up"):
    # connect to mysql db
    config = {
        "host": "localhost",
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PWD"),
        "database": "optiSwim"
    }  


    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            print("Connected to MySQL server")
        cursor = conn.cursor()
    except Exception as e:
        capture_exception(e)
        exit()


# ChatGPT inspired
global global_msg
global_msg = None
def getData():
    try: 
        url = 'wss://badi-public.crowdmonitor.ch:9591/api'
        def on_message(ws, message):
            global global_msg
            global_msg = message
            ws.close()

        def on_error(ws, error):
            print(f"Error: {error}")
            ws.close()

        def on_close(ws, close_status_code, close_reason):
            print(f"WebSocket closed. Code: {close_status_code} Reason: {close_reason}")

        def on_open(ws):
            print("WebSocket opened")
            # You can send a message when the connection opens
            ws.send("")

        # Create a WebSocket object and specify event handlers
        ws = websocket.WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        # Start the connection (blocking call)
        ws.run_forever()
    except Exception as e:
        capture_exception(e)
        exit()

    return global_msg

def parseData(data):
    try:
        jsonData = json.loads(data)
        out = {}
        for pool in jsonData:
            if pool['name'] in ['Hallenbad City' , 'Hallenbad Oerlikon']:
                out[pool['name']] = int(pool['currentfill'])
        
        return out
    except Exception as e:
        capture_exception(e)
        exit()



def write_to_db(data):
    # MySQL
    try: 
        oerlikon = data['Hallenbad Oerlikon']
        city = data['Hallenbad City']
        time = datetime.datetime.now().astimezone(pytz.timezone("Europe/Berlin")).strftime('%Y-%m-%d %H:%M:%S')
        insert_query = f"INSERT INTO currentfill (time, oerlikon, city) VALUES ('{time}',{oerlikon}, {city})"
        print(insert_query)
    except Exception as e:
        capture_exception(e)
        exit()

    try:
       #cursor.execute(insert_query)
       #conn.commit()
       print("",end="")
    except Error as e:
        capture_exception(e)
        print(f"Error: {e}")
        conn.rollback()
        exit()

def collectData():
    with sentry_sdk.start_transaction(op="task", name="Fetch and save data"):
        with sentry_sdk.start_span(name="Get Data from api"):
            fetchedData = getData()
        with sentry_sdk.start_span(name="Parse Data"):
            parsedData = parseData(fetchedData)
        with sentry_sdk.start_span(name="Write to DB"):
            write_to_db(parsedData)


while(True):
    collectData()
    time.sleep(30)