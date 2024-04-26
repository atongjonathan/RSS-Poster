from telebot import util, types, TeleBot
import time
from logging import getLogger, basicConfig, INFO, StreamHandler, FileHandler
from poster import RSSPoster
from database import Database
import os
from keep_alive import keep_alive

# from db import *

basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s - line_no %(lineno)s : %(message)s ",
    handlers=[
        StreamHandler(),
        FileHandler('./logs.txt')],
    level=INFO)
logger = getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

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
def update(message):
    command = message.text
    queries = command.split(" ")[1:]
    domains = [feed["domain"] for feed in poster.FEEDS]
    if len(queries) > 0:
        for query in queries:
            if query.title() in domains:
                logger.info(f"{query} found in domains")
                for feed in poster.FEEDS:
                    if query.title() == feed["domain"]:
                        send_messages(feed, message)
            else:
                domains_txt = "\n".join(domains)
                bot.reply_to(
                    message, f"Channel {query} does not exist we have: \n{domains_txt}")
    else:
        logger.info("Updating all channels")
        message = bot.reply_to(message, "Updating all channels ⏳...")
        feeds = poster.FEEDS
        total_links = 0
        for feed in feeds:
            sent_links = send_messages(feed, message)
            total_links += sent_links
        bot.delete_message(message.chat.id, message_id=message.message_id)
        bot.send_message(
            message.chat.id, f"Updates done.✅\nLinks sent {total_links}")


def send_messages(feed: dict, message: types.Message):
    logger.info(f"Sending messages for {feed['domain']}")
    try:
        bot.edit_message_text(
        f"Updating {feed['domain']} ⏳...", message.chat.id, message.message_id)
    except Exception:
        message = bot.send_message(message.chat.id, f"Updating {feed['domain']} ⏳...")
    no_of_links = 0
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
                        paused_msg = bot.send_message(
                            message.chat.id, f"Updates paused due to too many messages for {feed['domain']} resuming in {duration}s.")
                        time.sleep(duration)
                        bot.delete_message(
                            message.chat.id, paused_msg, paused_msg.message_id)
                    except Exception as e:
                        logger.error(
                            f"'{e}'\n Sleeping for {duration} seconds")

        no_of_links += 1

    bot.edit_message_text(
        f"Completed updating {feed['domain']}✅,\nLinks sent {no_of_links}", message.chat.id, message.message_id)
    return no_of_links


if __name__ == "__main__":
    logger.info("Bot online")
    keep_alive()
    bot.polling()
