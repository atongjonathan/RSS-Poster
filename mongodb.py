from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv
import os

load_dotenv("config.env")
class Database():
    def __init__(self):
        client = MongoClient(os.environ.get("DATABASE_URL"))
        self.db = client.get_database("RSS")
        self.json_data = self.db.get_collection("json_data")
    
    def insert_json_data(self, message):
        existing_message = self.json_data.find_one(message)
        if existing_message:
            raise DuplicateKeyError("Message Already Exists")
        else:
            self.json_data.insert_one(message)

    
