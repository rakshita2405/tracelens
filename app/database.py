
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")
database_name = os.getenv("MONGODB_DATABASE", "tracelens")

if not uri:
    raise RuntimeError("MONGODB_URI is missing from .env")

client = MongoClient(
    uri,
    serverSelectionTimeoutMS=5000,
)

database = client[database_name]


def check_database():
    client.admin.command("ping")
    return True
