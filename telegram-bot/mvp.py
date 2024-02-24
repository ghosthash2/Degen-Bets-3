import telebot
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from eth_account import Account
import json
from eth_account.messages import encode_defunct
import requests
from functools import lru_cache, wraps
from datetime import datetime, timedelta
import os

# testing

BACKEND_PORT = os.environ.get("BACKEND_PORT")
BACKEND_HOSTNAME = os.environ.get("BACKEND_HOSTNAME")
BACKEND_URL = f"{BACKEND_HOSTNAME}:{BACKEND_PORT}"


def print_and_send_to_slack(message):
    print(message)
    # slack
    # url =
    # requests.post(url, json={"text": message})


def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.utcnow() >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.utcnow() + func.lifetime

            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache


# Connect to MongoDB hand qVbt3zOxjRip4Aw5
uri = os.environ.get("MONGODB_URI")
client = MongoClient(uri, server_api=ServerApi("1"))

# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    exit()

db = client[os.environ.get("MONGODB_DB")]
users = db[os.environ.get("MONGODB_COLLECTION")]

# BOT_TOKEN = os.environ.get("BOT_TOKEN")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)


def create_ethereum_wallet():
    new_account = Account.create("afdouhblsi bet 12983GIZUOGZUIO 420lol")
    encrypted_account = json.dumps(
        Account.encrypt(new_account.key, password="password"))
    return encrypted_account, new_account.address


def sign_message_with_encrypted_credentials(encrypted_account_json, message):
    encrypted_account = json.loads(encrypted_account_json)
    account_key = Account.decrypt(encrypted_account, password="password")
    account = Account.from_key(account_key)
    msg_hash = encode_defunct(text=message)
    signed_message = account.sign_message(msg_hash)
    return signed_message.signature.hex()


@timed_lru_cache(60000, None)
def get_all_matches(sport_key):
    url = f"http://{BACKEND_URL}/sports/{sport_key}"
    response = requests.get(url)

    matches = response.json()
    return matches


@timed_lru_cache(60000, None)
def get_all_sports():
    url = f"http://{BACKEND_URL}/sports"
    response = requests.get(url)

    games = response.json()
    return games


def shortString(string):
    # Split the string into words
    words = string.split("_")
    # Create an empty list to store the last letter of each word
    letters = []
    # Iterate over each word in the list
    for word in words:
        # Append the last letter of the word to the list
        letters.append(word[-1])
    # Join the letters together and convert to uppercase
    short = "".join(letters).upper()
    # Return the short string
    return short


def get_all_sport_keys():
    sports = get_all_sports()
    keys = []
    for sport in sports:
        keys.append(f"bet{sport['keyTG']}")
    return keys


def get_all_sport_match_keys():
    sports = get_all_sports()
    keys = []
    for sport in sports[:10]:
        matches = get_all_matches(sport_key=sport["key"])
        for match in matches:
            keys.append(f"bet{sport['keyTG']}{match['idTG']}")
    return keys


def sport_key_to_game(game_to_find):
    requested_game = None
    games = get_all_sports()

    for game in games:
        if game["keyTG"] == game_to_find:
            requested_game = game

    return requested_game


def sport_string_to_game(game_to_find):
    requested_game = None
    games = get_all_sports()

    for game in games:
        if game["key"] == game_to_find:
            requested_game = game

    return requested_game


def find_match_by_string(game, match_to_find):
    game = sport_string_to_game(game)

    requested_match = None
    matches = get_all_matches(game["key"])

    for match in matches:
        if match["id"] == match_to_find:
            requested_match = match

    return game, requested_match


def find_match_by_key(game, match_to_find):
    game = sport_key_to_game(game)

    requested_match = None
    matches = get_all_matches(game["key"])

    for match in matches:
        if match["idTG"] == match_to_find:
            requested_match = match

    return game, requested_match


def get_all_bets():
    url = f"http://{BACKEND_URL}/bets"
    response = requests.get(url)

    bets = response.json()
    return bets


global keys
KEYS = []


def refetch_all_bet_keys():
    global KEYS
    KEYS = get_all_bets_keys()


def get_all_bets_keys():
    global KEYS
    bets = get_all_bets()
    # instead of hard reload just append bet into it.
    for bet in bets:
        if bet['completed']:
            continue
        if bet['groupId']:
            KEYS.append(
                f"accept{bet['id'].replace('-','')}@{bot.get_me().username}")

        KEYS.append(f"accept{bet['id'].replace('-','')}")

    return KEYS


@bot.message_handler(commands=get_all_bets_keys())
def accept_bet(message):
    print(
        f"User interacted with, 'accept_bet'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")

    bets = get_all_bets()

    find = ""
    bet_to_find = message.text.replace("/accept", "")

    if message.chat.type == "group":
        bet_to_find = bet_to_find.replace(
            f"@{bot.get_me().username}", "")

    for bet in bets:
        if bet["id"].replace("-", "") == bet_to_find:
            find = bet
            break

    print("found the match", find)

    url = f"http://{BACKEND_URL}/bets/accept"

    user = users.find_one({"user_id": message.from_user.id})
    sig = sign_message_with_encrypted_credentials(
        encrypted_account_json=user["wallet_json"], message="I WANT TO PLACE THIS BET")

    request_body = {
        "id": bet_to_find[:8] + '-' + bet_to_find[8:12] + '-' + bet_to_find[12:16] + '-' + bet_to_find[16:20] + '-' + bet_to_find[20:],
        "signature": sig
    }

    response = requests.post(url, json=request_body)

    if response.status_code == 200:
        print('Request successful')
    else:
        print('Request failed with status code:', response.status_code)

    bot.reply_to(message, "successfull bet.")


@bot.message_handler(commands=["reset"])
def reset_bet(message):
    users.update_one({"user_id": message.from_user.id}, {"$set": {"user_step": "0", "user_step_sport_id": "0",
                                                                  "user_step_match_id": "0", "user_step_wager": "0", "user_step_betsOnHome": "0", }})
    bot.reply_to(message, "Reset successfull!")


@bot.message_handler(commands=["balance"])
def send_balance(message):
    print(
        f"User interacted with, 'send_balance'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")
    response = ""
    user = users.find_one({"user_id": message.from_user.id})
    if user is None:
        response = "You have not been registert, type /start."
    else:
        response = f"Your current balance is: {user['balance']}"

    bot.reply_to(
        message, response)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    print(
        f"User interacted with, 'send_welcome'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")
    user = users.find_one({"user_id": message.from_user.id})
    if user is None:
        encrypted_wallet, address = create_ethereum_wallet()
        user = {
            "user_id": message.from_user.id,
            "balance": 100,
            "wallet_json": encrypted_wallet,
            "username": message.from_user.full_name,
            "wallet_address": address,
            # 0 =  nothing, 1 = asked for wager, 2 = asked for team, 3 ask to confirm, 4 bet created.
            "user_step": "0",
            "user_step_wager": "0",
            "user_step_betsOnHome": "0",
            "user_step_sport_id": "0",
            "user_step_match_id": "0",
        }
        users.insert_one(user)
        user = users.find_one({"user_id": message.from_user.id})

    # Send welcome message
    commands = [
        "/start - Show this message",
        "/balance - Check your balance",
        "/games - List all available games",
        "/bets - List all available bets"
    ]

    infos = [
        f"Balance: {user['balance']}",
        f"WalletAddress: {user['wallet_address']}",
    ]

    bot.reply_to(
        message, f"Welcome to the bot! Here are the available commands:\n\n{chr(10).join(commands)}\n\nInfos:\n\n{chr(10).join(infos)}")


@bot.message_handler(commands=["games"])
#  use this to create for each game the betst new list should return "/{key}, title, desciptipon "
def send_available_bets(message):
    print(
        f"User interacted with, 'send_available_bets'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")
    games = get_all_sports()
    response = "Here are the available bets:\n\n"

    for game in games[:10]:
        entry = f"- {game['title']}, {game['description']}, /bet{game['keyTG']}\n"
        response += entry

    bot.reply_to(
        message, f"{response}")


@bot.message_handler(commands=["settle"])
#  use this to create for each game the betst new list should return "/{key}, title, desciptipon "
def settle_bets(message):
    print(
        f"User interacted with, 'settle_bets'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")

    active_bets = get_all_bets()

    for active_bet in active_bets:
        if active_bet["competitorId"] == None:
            continue

        payload = {
            "sport": active_bet["sport"],
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"http://{BACKEND_URL}/bets/settle", json=payload, headers=headers)

        # Check response status code
        if response.status_code == 204:
            print("Bet settled")
        else:
            print("Failed to create bet. Status code:", response.status_code)


@bot.message_handler(commands=["bets"])
#  use this to create for each game the betst new list should return "/{key}, title, desciptipon "
def send_open_bets(message):
    print(
        f"User interacted with, 'send_open_bets'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")
    bets = get_all_bets()
    response = "Here are the available games:\n\n"

    if bets == []:
        response += "No bets found."
        bot.reply_to(
            message, f"{response}")
        return

    for bet in bets:
        if bet["completed"] == "true":
            continue
        if bet["competitorId"] != None:
            continue
        if message.chat.type == "group" and str(message.chat.id) != bet["groupId"]:
            continue
        if message.chat.type != "group" and bet["groupId"] != None:
            continue

        opponent = users.find_one({"wallet_address": bet["creatorId"]})
        # game, match = find_match_by_key(bet["sport"], bet["matchId"])

        winner = team_bool_to_string(bet['homeToWin'])
        home_text = f"Bet: For {winner} to win."

        sport, match = find_match_by_string(bet["sport"], bet["matchId"])

        entry = f"- {sport['description']}, {match['home_team']} x {match['away_team']},{home_text}, {opponent['username']}, /accept{bet['id'].replace('-','')}\n"
        response += entry

    bot.reply_to(
        message, f"{response}")


@bot.message_handler(commands=get_all_sport_keys())
def send_available_bet_matches(message):
    print(
        f"User interacted with, 'send_available_bet_matches'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")
    # resolve here the short to the right key by fethcing all games and matching the keyTG and then making a request getting all the machtes with the key.
    game_to_find = message.text[4:]
    if message.chat.type == "group":
        game_to_find = message.text.replace(
            f"@{bot.get_me().username}", "")[4:]

    requested_game = sport_key_to_game(game_to_find)

    if requested_game == None:
        bot.reply_to(
            message, "Game not found, this should not happen. But this edgecase is not not possible.  greetings from the MVP development ^.^")
        return

    matches = get_all_matches(requested_game["key"])
    response = f"Here are the available matches to bet against in the {requested_game['description']}:\n\n"

    completed_matches = list(filter(lambda m: m["completed"] == True, matches))

    if len(completed_matches):
        for game in completed_matches[:10]:
            entry = f"-{game['home_team']} x {game['away_team']}, /bet{game_to_find}{game['idTG']}\n"
            response += entry
    else:
        response += "Ups, there are no completed matches to choose from for the MVP demo!"

    bot.reply_to(message, response)


def timestamp_converter(date_string):
    date_object = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    formatted_date = date_object.strftime("%d. %b. %Y")
    return formatted_date


def timestamp_to_string(timestamp: str) -> str:
    now = datetime.utcnow()
    timestamp_datetime = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
    time_diff = now - timestamp_datetime
    if time_diff.days > 365:
        return f'The timestamp is from {time_diff.days//365} years ago.'
    elif time_diff.days > 30:
        return f'The timestamp is from {time_diff.days//30} months ago.'
    elif time_diff.days > 7:
        return f'The timestamp is from {time_diff.days//7} weeks ago.'
    elif time_diff.days > 0:
        return f'The timestamp is from {time_diff.days} days ago.'
    elif time_diff.seconds >= 3600:
        return f'The timestamp is from {time_diff.seconds//3600} hours ago.'
    elif time_diff.seconds >= 60:
        return f'The timestamp is from {time_diff.seconds//60} minutes ago.'
    else:
        return 'The timestamp is from just now.'


@bot.message_handler(commands=get_all_sport_match_keys())
def send_create_bet_interaction(message):
    print(
        f"User interacted with, 'send_create_bet_interaction'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")

    user = users.find_one({"user_id": message.from_user.id})
    if user == None:
        bot.reply_to(message, "new user run /start in dm's")
        return

    if user["user_step"] != "0":
        bot.reply_to(
            message, "complete the last bet in order to create the new bet. If you want to reset and cancel, type /reset")
        return

    # resolve here the short to the right key by fethcing all games and matching the keyTG and then making a request getting all the machtes with the key.
    selected_sport_tgkey = message.text.replace("/bet", "")[:-10]
    selected_match_tgid = message.text[-10:]

    if message.chat.type == "group":
        selected_sport_tgkey = message.text.replace("/bet", "").replace(
            f"@{bot.get_me().username}", "")[:-10]
        selected_match_tgid = message.text.replace("/bet", "").replace(
            f"@{bot.get_me().username}", "")[-10:]

    print(selected_sport_tgkey, selected_match_tgid)

    requested_sport, requested_match = find_match_by_key(
        selected_sport_tgkey, selected_match_tgid)

    print(requested_sport, "Requested Sport",
          requested_match, "Requested Match")

    commence_time = timestamp_converter(requested_match["commence_time"])

    user = users.find_one({"user_id": message.from_user.id})
    response = f"{requested_sport['description']}\n\nMatch: {requested_match['sport_title']} - {commence_time}\n{requested_match['home_team']} vs {requested_match['away_team']}\n\nHow much do you want to wager? (Balance: {user['balance']})"

    users.update_one({"user_id": message.from_user.id},
                     {"$set": {"user_step": "1", "user_step_sport_id": requested_sport["key"], "user_step_match_id": requested_match["id"]}})

    bot.reply_to(message, response)
    # bot.reply_to(message, response)


def get_user_step(user_id):
    user = users.find_one({"user_id": user_id})
    result = ""

    try:
        result = user["user_step"]
    except KeyError as ke:
        # manage migration to new model
        print("Migrating to new shema")
        users.update_one({"user_id": user_id}, {"$set": {"user_step": "0", "user_step_sport_id": "0",
                         "user_step_match_id": "0", "user_step_wager": "0", "user_step_betsOnHome": "0", }})
        return get_user_step(user_id)

    return result


# handling of the bet ammount
@bot.message_handler(func=lambda message: get_user_step(message.from_user.id) == "1")
def bet_ammount_setting(message):
    print(
        f"User interacted with, 'bet_ammount_setting'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")

    wager_amount = 0

    try:
        wager_amount = int(message.text)

        user = users.find_one({"user_id": message.from_user.id})

        if user == None:
            bot.reply_to(message, "new user run /start in dm's")
            return

        if int(user["balance"]) < wager_amount:
            bot.reply_to(
                message, "You dont have enought funds, try with a lower amount, check your balance with /balance.")
            return

        users.update_one({"user_id": message.from_user.id}, {"$set": {"user_step": "2",
                                                                      "user_step_wager": wager_amount}})
    except ValueError:
        bot.reply_to(message, "Please try again with a number.")
        return

    bot.reply_to(
        message, "Successfull, now send 0 if you bet on the home team, or 1 if you bet on the away team.")


# team, or 'away' on the away team.")

def team_bool_to_string(team_bool: bool):
    if team_bool:
        return "home"
    else:
        return "away"


def team_string_to_bool(team_string: str):
    if team_string == "home":
        return True
    else:
        return False

# handling of the bet ammount


@bot.message_handler(func=lambda message: get_user_step(message.from_user.id) == "2")
def bet_team_setting(message):
    print(
        f"User interacted with, 'bet_team_setting'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")

    bet_team = message.text.lower()

    response = "Bet created."

    if bet_team == "0" or bet_team == "1":

        selected_team_bool = True
        if bet_team == "1":
            selected_team_bool = False

        users.update_one({"user_id": message.from_user.id}, {
                         "$set": {"user_step": "3", "user_step_betsOnHome": selected_team_bool}})

        response = "Confirm with yes, or type /reset"
    else:
        response = "Please try again with either '0' or '1'."

    bot.reply_to(
        message, response)


# handling of the bet ammount
@bot.message_handler(func=lambda message: get_user_step(message.from_user.id) == "3")
def bet_confirmation(message):
    print(
        f"User interacted with, 'bet_confirmation'\nWith id: {message.from_user.id}\nfirstname: {message.from_user.first_name}\nfullname: {message.from_user.full_name}\ntext: {message.text}")

    confirm_response = message.text.lower()
    chat_response = ""

    if confirm_response != "yes":
        chat_response = "Reset with /reset."

    try:
        user = users.find_one({"user_id": message.from_user.id})
        if user == None:
            bot.reply_to(message, "new user run /start in dm's")
            return
        sig = sign_message_with_encrypted_credentials(
            encrypted_account_json=user["wallet_json"], message="I WANT TO PLACE THIS BET")
        print(sig)

        groupId = None
        if message.chat.type == "group":
            groupId = str(message.chat.id)

        payload = {
            "matchId": user["user_step_match_id"],
            "sport": user["user_step_sport_id"],
            "value": user["user_step_wager"],
            "signature": sig,
            "validTill": 1733617982000,
            "homeToWin": user["user_step_betsOnHome"],
            "groupId": groupId
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"http://{BACKEND_URL}/bets", json=payload, headers=headers)

            # Check response status code
            if response.status_code == 201:
                print("Bet created successfully.")
                new_balance = int(user["balance"]) - \
                    int(user["user_step_wager"])
                users.update_one({"user_id": message.from_user.id}, {
                    "$set": {"balance": new_balance, "user_step": "0", "user_step_betsOnHome": "0", "user_step_match_id": "0", "user_step_sport_id": "0", "user_step_wager": "0"}})

                chat_response += "Bet created."
                refetch_all_bet_keys()
            else:
                chat_response += "Bet failed."
                print("Failed to create bet. Status code:", response.status_code)
        except Exception as e:
            print(e)

        # send the bet to the backend
        # clean up and set it back. and update balance

    except Exception as e:
        print(e)

    bot.reply_to(
        message, chat_response)


bot.infinity_polling()
