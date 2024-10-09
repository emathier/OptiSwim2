# Login
from time import sleep
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import websocket
import websockets
import ssl
import json
import mysql.connector
from mysql.connector import Error
import pytz
import datetime

# Use a service account.
cred = credentials.Certificate('/home/ubuntu/optiSwim/creds.json')
# cred = credentials.Certificate('z:/projects/optiSwim/firebase/creds.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

# connect to my sql
# Define the database connection parameters
config = {
    "host": "localhost",
    "user": "serviceaccount",
    "password": "sn8bsmDvtiHu8BBxNuni",
    "database": "optiSwim"
}

# Establish a connection to the MySQL server
try:
    conn = mysql.connector.connect(**config)
    if conn.is_connected():
        print("Connected to MySQL server")
    cursor = conn.cursor()
except mysql.connector.Error as err:
    print(f"Error: {err}")

# Ignore SSL certificate verification errors
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Add data
def saveToDb(data):
    # Firebase
    tmp = {"timestamp": firestore.SERVER_TIMESTAMP, "location"  : data }
    db.collection("timestamps").add(tmp)

    # MySQL
    oerlikon = data['Oerlikon']
    city = data['City']
    time = datetime.datetime.now().astimezone(pytz.timezone("Europe/Berlin")).strftime('%Y-%m-%d %H:%M:%S')
    insert_query = f"INSERT INTO currentfill (time, oerlikon, city) VALUES ('{time}',{oerlikon}, {city})"
    print(insert_query)
    try:
       cursor.execute(insert_query)
       conn.commit()
    except Error as e:
        print(f"Error: {e}")
        conn.rollback()

def getData():
    websocket_url = 'wss://badi-public.crowdmonitor.ch:9591/api'
    ws = websocket.create_connection(websocket_url, sslopt={"cert_reqs": ssl.CERT_NONE, "ssl_context": ssl_context})
    ws.send("")
    jsonResponse = json.loads(ws.recv())

    data = {}
    for i in range(32):
        data[jsonResponse[i]['name']] = int(jsonResponse[i]['currentfill'])

    ans = {}
    ans['Oerlikon'] = data['Hallenbad Oerlikon']
    ans['City'] = data['Hallenbad City']

    ws.close()

    return ans


while(True):
    saveToDb(getData())
    sleep(30)