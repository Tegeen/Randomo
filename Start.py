import sys
import time
import telepot
import logging
from telepot.loop import MessageLoop #reflect Messages
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton,InlineQueryResultArticle, InputTextMessageContent #reflect keyboard type


#connect to Telegram Bot
token = "420741794:AAEZAyVossclOyogZfHJOqwL3N-kHDv3uOE"
bot = telepot.Bot(token)

def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[   #Buttons for options available
        [InlineKeyboardButton(text='View nearby eateries', callback_data='listeateries' )],
        [InlineKeyboardButton(text='Randomize eatery!', callback_data='randomizing')],
        [InlineKeyboardButton(text='Specify preferences', callback_data='preferencequestions')],
        [InlineKeyboardButton(text='Give feedback', callback_data='preferencequestions')]
    ])

    bot.sendMessage(chat_id, 'Please select an option', reply_markup=keyboard)

def location(bot, update):
    user = update.message.from_user
    user_location = update.message.location
    logger.info("Location of %s: %f / %f"% (user.first_name, user_location.latitude, user_location.longitude))
    
def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('Callback Query:', query_id, from_id, query_data)

    bot.answerCallbackQuery(query_id, text='Received')

MessageLoop(bot, {'chat': on_chat_message, 'callback_query': on_callback_query}).run_as_thread()
print ('Listening...')

#Keep program running
while 1:
    time.sleep(10)

#bot.sendMessage(272300259, 'Hey!')


