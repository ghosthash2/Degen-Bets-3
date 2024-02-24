
# %%
from telegram import ForceReply
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from eth_account.messages import encode_defunct
from eth_account import Account
import telebot
from pymongo.server_api import ServerApi
from pymongo import MongoClient
import requests
import json
url = "http://localhost:3000/sports"
response = requests.get(url)
print(json.dumps(response.json(), indent=4))

games = json.dumps(response.json(), indent=4)

# %%


def get_all_sports():
    url = "http://localhost:3000/sports"
    response = requests.get(url)

    games = response.json()
    return games


def get_all_sport_keys():
    sports = get_all_sports()
    keys = []
    for sport in sports:
        print(sport["key"])
        keys.append(sport["key"])
    return keys


print(get_all_sport_keys())


# %% idkl
# Connect to MongoDB hand qVbt3zOxjRip4Aw5
uri = "mongodb+srv://hand:qVbt3zOxjRip4Aw5@bet.q2qgo6q.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi("1"))

# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["telegram_bot"]
users = db["users"]

users.update_one({"user_id": 794349480}, {"$set": {"user_step": "0", "user_step_sport_id": "0",
                                                   "user_step_match_id": "0", "user_step_wager": "0", "user_step_betsOnHome": "0", }})


# %%

def sign_message_with_encrypted_credentials(encrypted_account_json: str, message: str) -> str:
    encrypted_account = json.loads(encrypted_account_json)
    account_key = Account.decrypt(encrypted_account, password="password")
    account = Account.from_key(account_key)
    msg_hash = encode_defunct(text=message)
    signed_message = account.sign_message(msg_hash)
    return signed_message.signature.hex()
