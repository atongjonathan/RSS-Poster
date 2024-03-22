import telebot
from telebot import util, types
import time
from logging import getLogger, basicConfig, INFO, StreamHandler, FileHandler
from poster import RSSPoster
from mongodb import Database
import os

# from db import *

basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s - line_no %(lineno)s : %(message)s ",
    handlers=[
        StreamHandler(),
        FileHandler('./logs.txt')],
    level=INFO)
logger = getLogger(__name__)

TELEGRAM_BOT_TOKEN = "5954527089:AAHQJGcyGaI_MfT6DsoEgmKicfjBujizCbA"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

poster = RSSPoster()
db = Database()


@bot.message_handler(commands=["start"])
def hello(message):
    bot.send_message(message.chat.id, f"Hello {message.from_user.first_name}")


@bot.message_handler(commands=["logs"])
def hello(message):
    with open('logs.txt') as file:
        text = file.read()
    splitted_text = util.smart_split(text, 4096)
    for text_instance in splitted_text:
        try:
            bot.send_message(message.chat.id, text_instance)
        except Exception as e:
            logger.error(e)
            return
    with open('logs.txt', 'w')as file:
        file.write("")


@bot.message_handler(commands=["update"])
def update(message=None):
    message = bot.reply_to(message, "Updating channels ⏳...")
    feeds = poster.FEEDS
    no_of_links = 0
    for feed in feeds:
        bot.edit_message_text(
            f"Updating {feed['domain']}... ",
            message.chat.id,
            message.id)
        messages = poster.get_messages(feed.get("url"))
        for item in messages:
            markup = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton("Read More", url=item["url"])
            markup.add(button)
            try:
                db.insert_json_data(item)
            except:
                continue
            try:
                bot.send_message(
                    feed["chat_id"], item["text"], reply_markup=markup)
            except Exception as e:
                messages = util.smart_split(item['text'])
                for split_message in messages:
                    try:
                        bot.send_message(
                            feed["chat_id"], text=split_message, reply_markup=markup)
                    except Exception as e:
                        if "429" in str(e):
                            duration = int(e.__str__()[-2:])
                        try:
                            bot.edit_message_text(
                                f"Update paused for {duration}s due to too many messages, for {feed['domain']} will resume shortly...",
                                message.chat.id,
                                message.id)
                        except Exception as e:
                            pass
                        logger.error(
                            f"An error occured when sending smart split :'{e}'\n Sleep in {duration}")
                        time.sleep(duration)
            no_of_links += 1

        bot.edit_message_text(
            f"Completed updating {feed['domain']}",
            message.chat.id,
            message.id)

    bot.edit_message_text(
        f"Finished update. Links sent: {no_of_links} ✅",
        message.chat.id,
        message.id)
    no_of_links = 0


if __name__ == "__main__":
    logger.info("Bot online")
    bot.polling()
