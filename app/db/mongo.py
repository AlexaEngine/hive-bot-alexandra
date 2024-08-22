from pymongo import MongoClient, errors
from app.config import MONGO_CLIENT, logger

# Create the MongoClient and connect to the database
try:
    client = MongoClient(MONGO_CLIENT)
    db = client.get_database('hivedb')
    hiveData = db['hive-cx-data']
except errors.ConnectionError as e:
    logger.error(f"Could not connect to MongoDB: {e}")
    raise

# Function to insert a document into a collection
def insert_document(collection_name, document):
    try:
        collection = db[collection_name]
        result = collection.insert_one(document)
        return result.inserted_id  # Return the ID of the inserted document
    except errors.PyMongoError as e:
        logger.error(f"An error occurred when inserting the document: {e}")
        raise

# Function to fetch documents from a collection based on a query
def fetch_documents(collection_name, query):
    try:
        collection = db[collection_name]
        return list(collection.find(query))  # Return the documents as a list
    except errors.PyMongoError as e:
        logger.error(f"An error occurred when fetching documents: {e}")
        return []  # Return an empty list if an error occurred
