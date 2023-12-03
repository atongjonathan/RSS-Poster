import telebot
import time
from utils import send_citizen_data, billboard, extract_data
import os
from logger import LOGGER

infinity = True

TELGRAM_BOT_TOKEN = os.environ.get('TELGRAM_BOT_TOKEN')


FEEDS = [
    {
        "chat_id": -1002103516422, "url": "https://billboard.com/feed/"
    },
    {
        "chat_id": -1001908193905, "url": "https://citizen.digital/feed.xml"
    },
    {
        "chat_id": -1002056978598, "url": "https://animecorner.me/feed/"
    },
    {
        "chat_id": -1002042618375, "url": "https://soompi.com/feed"
    },
    {
        "chat_id": -1002139940705, "url": "https://tmz.com/rss.xml"
    }
]


bot = telebot.TeleBot(TELGRAM_BOT_TOKEN, parse_mode="HTML")


def get_domain_from_url(url):
    try:
        # Split the URL by "//" and take the second part
        domain = url.split("//")[1].split("/")[0]
        return domain.replace(".com", "").split(".")[0]

    except Exception as e:
        LOGGER.error(f"Error {e} extracting from {url}:")
        return None


urls = [feed["url"] for feed in FEEDS]
chat_ids = [feed["chat_id"] for feed in FEEDS]
domains = [get_domain_from_url(url) for url in urls]
items = {}
for idx, channel in enumerate(domains):
    items[channel] = {
        "feed": urls[idx],
        "chat_id": chat_ids[idx],
        "func": send_citizen_data if "citizen" in urls[idx] else billboard
    }


@bot.message_handler(commands=["start"])
def hello(message):
    bot.send_message(message.chat.id, f"Hello {message.from_user.first_name}")


@bot.message_handler(commands=["logs"])
def hello(message):
    with open('logs.txt')as file:
        text = file.read()
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["stop"])
def stop(message=None):
    global infinity
    infinity = False
    bot.send_message(message.chat.id, "Infinity stoped")


@bot.message_handler(commands=["update"])
def update(message=None):
    chat_id = 1095126805 if message is None else message.chat.id
    message = bot.send_message(chat_id, "Updating channels ⏳...")
    no_of_links = to_update(items)
    bot.edit_message_text(
        f"Completed ✅ links sent {no_of_links}",
        message.chat.id,
        message.id)
    no_of_links = 0


def send_data(entries, func, domain, chat_id):
    for entry in entries:
        message = func(entry)
        if (update_files(path=f"./db/{domain}.txt", link=entry["link"])):
            try:
                bot.send_message(chat_id, message, parse_mode="html")
                time.sleep(2)
            except Exception as e:
                LOGGER.error(e, "When in send data in", domain)
    LOGGER.info(f"{domain.title()} updated successfully")


def to_update(items, no_of_links=0):
    for (key, value) in items.items():
        domain = key
        url = value["feed"]
        chat_id = value["chat_id"]
        func = value["func"]
        try:
            data = extract_data(url, domain)
            no_of_links += 1
        except Exception as e:
            LOGGER.error(f"Error {e} in to_update")
        try:
            send_data(data, func, domain, chat_id)
        except Exception as e:
            LOGGER.error(f"Error {e} when sending {domain}")
        time.sleep(3)
    return no_of_links


def update_files(path, link):
    with open(path, 'r') as file:
        processed_urls = file.read()
    if link not in processed_urls:
        with open(path, 'a') as file:
            file.write(f"\n{link}")
        return True
    else:
        return False


if __name__ == "__main__":
    LOGGER.info("Bot online")
    bot.polling(non_stop=True)
