import sys
import os
import json
import time
from pymongo import MongoClient

db_name = "291db"

def insert_data(file: str, tweets):
    """
    insert data in small batches
    """
    batch = 1000
    with open(file, 'r', encoding='utf-8') as file:
        json_data = file.read()
    buffer = []
    for line in json_data.splitlines():
        try:
            # analyze each tweet
            tweet = json.loads(line.strip())
            buffer.append(tweet)

            # insert data when the buffer length is long enough
            if len(buffer) >= batch:
                tweets.insert_many(buffer)
                buffer = []

        except json.JSONDecodeError as e:
            print(f"jump JSON line: {line.strip()} ({e})")

    # insert left data
    if buffer:
        tweets.insert_many(buffer)

    print("Finished Insertion.")
    

def load_json(file: str, port: str):
    """
    
    """
    # judge if file exists
    if not os.path.exists(file):
        print(f"ERROR: file {file} does not exist.")
        sys.exit(1)

    # judge if the file ends with .json
    if not file.endswith(".json"):
        print(f"ERROR: file {file} is not a .json file.")
        sys.exit(1)

    try:
        # connect to mongodb server
        client = MongoClient(f"mongodb://localhost:{port}/")
        print("Successfully connected to mongodb server. Port:", port)
        db = client[db_name] # create or get the database 291db

        # delete tweet collection if it exists
        if 'tweets' in db.list_collection_names():
            db.tweets.drop()
            
        # create new tweets collection
        tweets = db['tweets']
        print("Successfully create a new collection named 'tweets'.")

        insert_data(file, tweets)
        time.sleep(2)
        client.close()
        print("Client closed.")

    except Exception as e:
        print("ERROR:", e)


if __name__ == '__main__':
    # check the correct input
    if len(sys.argv) != 3:
        print("usage: python3 load-json.py <json_file> <port>")
        sys.exit(1)
    
    file = sys.argv[1] # json file name
    port = sys.argv[2] # port
    load_json(file, port)