import feedparser
import os
from bs4 import BeautifulSoup
from telebot import TeleBot
import time
import threading
import signal
import logging

# Constants
BILLBOARD_URL = "https://billboard.com/feed/"
CITIZEN_URL = "https://citizen.digital/feed.xml"
ANIMECORNER_URL = "https://animecorner.me/feed/"
SOOMPI_URL = "https://www.soompi.com/feed"
UPDATE_INTERVAL_SECONDS = 60  # 5 minutes

BILLBOARD_FILE_PATH = "./billboard.txt"
CITIZEN_FILE_PATH = "./citizen.txt"
ANIMECORNER_FILE_PATH = "./animecorner.txt"
SOOMPI_FILE_PATH = "./soompi.txt"

billboard_chat_id = -1002103516422
citizen_chat_id = -1001908193905
animecorner_chat_id = -1002056978598
soompi_chat_id = -1002042618375

processed_urls = set()
infinity = True

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_TOKEN = "5954527089:AAHQJGcyGaI_MfT6DsoEgmKicfjBujizCbA"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class TelegramBot:
    def __init__(self, token):
        self.bot = TeleBot(token, parse_mode="HTML")

    def send_message(self, chat_id, message):
        try:
            self.bot.send_message(chat_id, message)
            time.sleep(5)
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    def edit_message_text(self, chat_id, message_id, text):
        try:
            self.bot.edit_message_text(text, chat_id, message_id)
        except Exception as e:
            logging.error(f"Error editing message: {e}")

def get_domain_from_url(url):
    try:
        domain = url.split("//")[1].split("/")[0].replace(".com", "")
        return domain
    except Exception as e:
        logging.error(f"Error extracting domain from {url}: {e}")
        return None

def send_citizen_data(entry):
    html_content = entry["html_content"]
    link = entry["link"]
    title = entry["title"]
    date = entry["date"]
    author = entry["author"]
    try:
        author_detail = author["author_detail"]
        author = author_detail["name"]
        email = author_detail["email"]
    except KeyError:
        author = "None"
    author_text = ""
    if author != "None":
        author_text = f"<i>Article written by <a href='mailto:{email}'>{author}</a></i>" 
    soup = BeautifulSoup(html_content, "html.parser")
    p = soup.find_all("p")
    div = soup.find_all("div")

    content_text = ""

    for paragraph in p:
        spans = paragraph.find_all("span", class_="tg-spoiler")
        img_tag = soup.find('img')
        img_src = img_tag['src'] if img_tag else None
        caption = soup.find('figcaption').text

        if spans:
            for span in spans:
                content_text += '\nStart-span\n'+ span.text + '\nEnd-start\n'
        else:            
            content_text += '\n' +paragraph.text.strip().replace("\n", " ") +'\n'
    if content_text=="":
        for paragraph in div:            
            img_tag = soup.find('img')
            img_src = img_tag['src'] if img_tag else None
            caption = soup.find('figcaption').text
            date = soup.find("pubDate")
            author = soup.find("author")        
            content_text += paragraph.text

    try:
        message = f"<a href='{link}'><b>{title}</b></a>\n<code>{content_text}</code>\n\n<i>Published on {date}</i>\n\n<b>{author_text}</b>\n\n<a href='{img_src}'>{caption}</a>"
    except UnboundLocalError:
        message = f"<a href='{link}'><b>{title}</b></a>\n{content_text}"
        print(f"No link found for {title}")
    except:
        pass
    finally:
        processed_urls.add(link)
    return message

def billboard(entry):
    link = entry["link"]
    title = entry["title"]
    date = entry["date"]
    date = entry["date"]
    summary = entry["summary"]
    author = entry["author"]
    tags = ', '.join(entry["tags"])
    summary = summary.replace("<p>","").replace("</p>","")
    message = f"<a href='{link}'><b>{title}</b></a>\n\n{summary}\n{tags}\n\n<i>Article written by <b>{author}</b>\nPublished on {date}</i>"
    return message

def update_files(path, link):
    try:
        with open(path, 'r') as file:
            processed_urls = file.read()
        if link not in processed_urls:
            global links
            links += 1
            with open(path, 'a') as file:
                file.write(f"\n{link}")
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error updating files: {e}")
        return False

def extract_data(feed_url, domain):
    try:
        feed = feedparser.parse(feed_url)
        entries = sorted(feed.entries, key=lambda entry: entry.published)
        if domain == "citizen":
            data = [
                {
                    "html_content": entry.content[0].value,
                    "title": entry.title,
                    "link": entry.link,
                    "date": entry.published,
                    "author": entry
                }            
                for entry in entries
            ]
            return data
        else:
            data = [
                {
                    "title": entry.title,
                    "link": entry.link,
                    "date": entry.published,
                    "summary": entry.summary,
                    "author": entry.author,
                    "tags": [f'#{tag["term"].replace(" ","")}' for tag in entry.tags]
                }
                for entry in entries
            ]          
            return data
    except Exception as e:
        logging.error(f"Error extracting data from {feed_url}: {e}")
        return []

def send_data(entries, func, domain, chat_id, bot_instance):
    for entry in entries:
        message = func(entry)
        if update_files(f"./{domain}.txt", entry["link"]):
            bot_instance.send_message(chat_id, message)

def to_update(bot_instance):
    for (key, value) in items.items():
        domain = key
        url = value["feed"]
        chat_id = value["chat_id"]
        func = value["func"]
        try:
            data = extract_data(url, domain)
        except Exception as e:
            logging.error(f"Error getting data for {domain}: {e}")
        send_data(data, func, domain, chat_id, bot_instance)

def polling_thread(bot_instance):
    while not stop_polling_event.is_set():
        try:
            bot_instance.bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Error in polling thread: {e}")
            time.sleep(5)


if __name__ == "__main__":
    bot = TeleBot(TELEGRAM_BOT_TOKEN)
    @bot.message_handler(commands=["infinity"])
    def update(message=None):
        global infinity
        infinity = True
        bot.send_message(message.chat.id, "Infinity started")
    @bot.message_handler(commands=["stop"])
    def update(message=None):
        global infinity
        infinity = False
        bot.send_message(message.chat.id, "Infinity stoped")       
    @bot.message_handler(commands=["update"])
    def update(message=None):
        if message is not None:
            message = bot.reply_to(message, "Updating ...")
            print("Command")
            to_update()
            global links
            bot.edit_message_text(f"Completed, Links sent: {links} ",message.chat.id,message.id)
        else:
            print("Auto")
            bot.send_message(1095126805,f"Completed, Links sent: {links} ")
    try:
        bot_instance = TelegramBot(TELEGRAM_BOT_TOKEN)
        items = {
            "billboard": {"feed": BILLBOARD_URL, "chat_id": billboard_chat_id, "func": billboard},
            "citizen": {"feed": CITIZEN_URL, "chat_id": citizen_chat_id, "func": send_citizen_data},
            "animecorner": {"feed": ANIMECORNER_URL, "chat_id": animecorner_chat_id, "func": billboard},
            "soompi": {"feed": SOOMPI_URL, "chat_id": soompi_chat_id, "func": billboard},
        }

        links = 0

        stop_polling_event = threading.Event()


        logging.info("Bot is online")
        polling_thread_instance = threading.Thread(target=polling_thread, args=(bot_instance,))
        polling_thread_instance.start()

        while infinity:
            to_update(bot_instance)
            time.sleep(UPDATE_INTERVAL_SECONDS)

        stop_polling_event.set()
        polling_thread_instance.join()

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

