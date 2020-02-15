def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')

def enter_long(update, context, currency_pair, price):
    update.messege.reply_text('Currency pair: ', currency_pair, ':\nEntering long at ', price)

def enter_short(update, context, currency_pair, price):
    update.messege.reply_text('Currency pair: ', currency_pair, ':\nEntering short at ', price)

def exit_long(update, context, currency_pair, price):
    update.messege.reply_text('Currency pair: ', currency_pair, ':\nExiting long at ', price)

def exit_short(update, context, currency_pair, price):
    update.messege.reply_text('Currency pair: ', currency_pair, ':\nExiting long at ', price)

def stop_loss_long(update, context, currency_pair, price):
    update.messege.reply_text('Currency pair: ', currency_pair, ':\nLong stop loss hit at ', price)

def stop_loss_short(update, context, currency_pair, price):
    update.messege.reply_text('Currency pair: ', currency_pair, ':\nShort stop at ', price)

bot.send_message(chat_id=536080467, text='Currency pair: ' + currency_pair + ':\nShort stop at ' + str(price))