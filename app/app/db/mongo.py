from pymongo import MongoClient
from app.config import MONGO_CLIENT

client = MongoClient(MONGO_CLIENT)
db = client['hivedb']
hiveData = db['hive-cx-data']

def insert_document(collection_name, document):
    collection = db[collection_name]
    collection.insert_one(document)
