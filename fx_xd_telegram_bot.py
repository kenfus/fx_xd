from telegram.ext import Updater
from telegram.ext import CommandHandler
import telegram

telegram_token = '979162059:AAGaEqWhC8E0S_o3rsYYZEVYHZpN0n5YcnA'

updater = Updater(token=telegram_token, use_context=True)
dispatcher = updater.dispatcher

bot = telegram.Bot(token = telegram_token)

bot.send_message(chat_id=536080467, text="I'm sorry Dave I'm afraid I " + str(4) + "can't do that.")