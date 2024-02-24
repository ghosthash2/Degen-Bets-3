import os
import telebot
import requests

# BOT_TOKEN = os.environ.get("BOT_TOKEN")
BOT_TOKEN = "6755596896:AAHJp4xf7g6Gs3Y0Ef3-cLzKA8CTyl1GukE"

bot = telebot.TeleBot(BOT_TOKEN)

# def get_daily_horoscope(sign: str, day: str) -> dict:
#     """Get daily horoscope for a zodiac sign.
#     Keyword arguments:
#     sign:str - Zodiac sign
#     day:str - Date in format (YYYY-MM-DD) OR TODAY OR TOMORROW OR YESTERDAY
#     Return:dict - JSON data
#     """
#     url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
#     params = {"sign": sign, "day": day}
#     response = requests.get(url, params)
#     return response.json()


def get_all_sports():
    url = "http://localhost:3000/sports/soccer_epl"
    response = requests.get(url)
    return response.json()


@bot.message_handler(commands=["start", "hello"])
def send_welcome(message):
    bot.reply_to(
        message, "Howdy, to get started enter /sports, to get started!")


@bot.message_handler(commands=["settlebets"])
def settle_bets(message):
    url = "http://localhost:3000/bets/settle"

    payload = {
        "sport": "soccer_epl"
    }

    response = requests.post(url, json=payload)
    tele_response = ""
    if response.status_code == 204:
        tele_response = "Bets settled successfully!"
        print("Bets settled successfully!")
    else:
        tele_response = "ERROR"
        print("Failed to settle bets.")

    bot.reply_to(
        message, tele_response)


@bot.message_handler(commands=["betcreate"])
def create_bet(message):
    url = "http://localhost:3000/bets"

    payload = {
        "matchId": "e30fdf73c9ed3bb469aaf7d5fc6b9585",
        "sport": "soccer_epl",
        "value": 123,
        "signature": "0x7a5299603f296636d5bd406c2f69bc7c988a37564360f20132d3ba8afbe942bf60042418450642f294d7fc25e05542f2a1217ffeb39c42552d5ea7441d4ed1c01b",
        "validTill": 1733617982000,
        "homeToWin": True
    }

    response = requests.post(url, json=payload)
    tele_response = ""
    if response.status_code == 201:
        tele_response = "Bet created successfully!"
        print("Bet created successfully!")
    else:
        tele_response = "ERROR"
        print("Failed to create bet.")

    bot.reply_to(
        message, tele_response)


@bot.message_handler(commands=["betjoin"])
def accept_bet(message):
    url = "http://localhost:3000/bets/accept"

    payload = {
        "id": "86623556-9040-42f5-a81d-cee78015c7b4",
        "signature": "0x17a81cd0f8e6edc5ee7b77df33a5543c38452c9708775bcd1d3b23efd8dc81ab69e686f0f79dc2d8c8989054946f18d4302530ba604e39bfa942a612eeecbcc81b"
    }

    response = requests.post(url, json=payload)
    tele_response = ""
    if response.status_code == 200:
        tele_response = "Bet accepted successfully!"
        print("Bet accepted successfully!")
    else:
        tele_response = "ERROR"
        print("Failed to accept bet.")

    bot.reply_to(
        message, tele_response)


bot.infinity_polling()
