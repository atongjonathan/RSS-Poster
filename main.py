import telebot
from telebot import util, types
import time
import os
from logging import getLogger, basicConfig, INFO, StreamHandler, FileHandler
from poster import RSSPoster
from db import *

basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s - line_no %(lineno)s : %(message)s ",
    handlers=[
        StreamHandler(),
        FileHandler('./logs.txt')],
    level=INFO)
logger = getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

poster = RSSPoster()
create_table()



@bot.message_handler(commands=["start"])
def hello(message):
    bot.send_message(message.chat.id, f"Hello {message.from_user.first_name}")


@bot.message_handler(commands=["logs"])
def hello(message):
    with open('logs.txt') as file:
        text = file.read()
    splitted_text = util.smart_split(text, 4096)
    for text_instance in splitted_text:
        bot.send_message(message.chat.id, text_instance)
    with open('logs.txt', 'w')as file:
        file.write("")


@bot.message_handler(commands=["update"])
def update(message=None):
    message = bot.reply_to(message, "Updating channels ⏳...")
    feeds = poster.FEEDS
    no_of_links = 0
    for feed in feeds:
        messages = poster.get_messages(feed)
        for item in messages:
            markup = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton("Read More", url=item["url"])
            markup.add(button)
            try:
                insert_json_data(item)
            except:
                continue
            bot.send_message(
            feed["chat_id"], item["text"], reply_markup=markup)
            time.sleep(60)
            no_of_links += 1
            time.sleep(2)
            break

        bot.edit_message_text(
            f"Completed ✅ total links sent {no_of_links}",
            message.chat.id,
            message.id)
        no_of_links = 0



if __name__ == "__main__":
    logger.info("Bot online")
    bot.polling()