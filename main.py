import telebot
from telebot import util,types
import time
from utils import extract_data, format
import os
from logger import LOGGER

def get_domain_from_url(url):
    try:
        # Split the URL by "//" and take the second part
        url = url.replace("www","")
        domain = url.split("//")[1].split("/")[0]
        return domain.replace(".com", "").split(".")[0]
    except Exception as e:
        LOGGER.error(f"Error {e} extracting from {url}:")
        return None

def send_data(entries, domain, chat_id, no_of_links):
    for entry in entries:
        message,content = format(entry)        
        not_sent = update_files(path=f"./db/{domain}.txt", link=entry["link"])
        if not_sent:
            try:
                markup = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton("Read More", url=content)
                markup.add(button)                
                sent_message = bot.send_message(1095126805, message,reply_markup=markup, parse_mode="html")
                message_data = {"id":sent_message.id, "content":content}
                messages_content.append(message_data)
                time.sleep(2)
                no_of_links += 1
            except Exception as e:
                LOGGER.error(f"Error '{e}' occured when sending {domain} data")
    LOGGER.info(f"{domain.title()} updated successfully")
    return no_of_links


def to_update(items,message,no_of_links = 0):    
    for (key, value) in items.items():
        domain = key
        url = value["feed"]
        chat_id = value["chat_id"]
        try:
            data = extract_data(url)
        except Exception as e:
            LOGGER.error(f"Error {e} when extracting data from {domain}")
        bot.edit_message_text(f"Updating {domain.title()}", message.chat.id, message.id)
        try:
            links = send_data(data, domain, chat_id, no_of_links)
            no_of_links += links
            bot.edit_message_text(f"Updated {domain.title()} Successfully!. Links sent {no_of_links}", message.chat.id, message.id)
        except Exception as e:
            LOGGER.error(f"Error '{e}' occurred when sending {domain} data")
            bot.edit_message_text(f"Updated {domain} failed!. Error: {e}", message.chat.id, message.id)        
    return no_of_links





def update_files(path, link):
    processed_urls = ""
    if os.path.exists(path):
        with open(path, 'r') as file:
            processed_urls = file.read()
    else:
        with open(path, 'w') as file:
            processed_urls = file.write("\n")
    if link not in processed_urls:
        with open(path, 'a') as file:
            file.write(f"\n{link}")
        return True
    return False


TELGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELGRAM_BOT_TOKEN = "6726476385:AAFCpAcbxZ-RLuUYIWhaW75TD22Tpl5teRo"



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
    },
    {
        "chat_id": 1095126805, "url": "https://animesenpai.net/feed/"
    }
]
urls = [feed["url"] for feed in FEEDS]
chat_ids = [feed["chat_id"] for feed in FEEDS]
domains = [get_domain_from_url(url) for url in urls]
items = {}
for idx, channel in enumerate(domains):
    items[channel] = {
        "feed": urls[idx],
        "chat_id": chat_ids[idx],
    }

messages_content = []
bot = telebot.TeleBot(TELGRAM_BOT_TOKEN, parse_mode="HTML")
@bot.message_handler(commands=["start"])
def hello(message):
    bot.send_message(message.chat.id, f"Hello {message.from_user.first_name}")


@bot.message_handler(commands=["logs"])
def hello(message):
    with open('logs.txt')as file:
        text = file.read()
    splitted_text = util.smart_split(text, 4096)
    for text_instance in splitted_text:
        bot.send_message(message.chat.id, text_instance)
    with open('logs.txt', 'w')as file:
        file.write("")


@bot.message_handler(commands=["stop"])
def stop(message=None):
    global infinity
    infinity = False
    bot.send_message(message.chat.id, "Infinity stoped")


@bot.message_handler(commands=["update"])
def update(message):
    message = bot.send_message(message.chat.id, "Updating channels ⏳...")
    no_of_links = to_update(items,message)
    bot.edit_message_text(
        f"Completed ✅ total links sent {no_of_links}",
        message.chat.id,
        message.id)
    no_of_links = 0


if __name__ == "__main__":
    LOGGER.info("Bot online")
    bot.polling(non_stop=True)
    # data = format(extract_data("https://billboard.com/feed/"))
    # print(data)
    # bot.send_message(, data)
