import feedparser
import os
from bs4 import BeautifulSoup
from telebot import TeleBot
import time
import threading
import signal

TELGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = TeleBot(TELGRAM_BOT_TOKEN, parse_mode="HTML")
links = 0
billboard_chat_id = -1002103516422
citizen_chat_id = -1001908193905
animecorner_chat_id = -1002056978598
soompi_chat_id = -1002042618375
billboard_url = "https://billboard.com/feed/"
citizen_url = "https://citizen.digital/feed.xml"
animecorner_url = "https://animecorner.me/feed/"
soompi_url = "https://www.soompi.com/feed"
processed_urls = set()
infinity = True



def get_domain_from_url(url):
    try:
        # Split the URL by "//" and take the second part
        domain = url.split("//")[1].split("/")[0]
        return domain.replace(".com", "")

    except Exception as e:
        print(f"Error extracting domain from {url}: {e}")
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
        print(f"No link found for for {title}")
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
    
def update_files(path,link):
    with open(path, 'r') as file:
        processed_urls = file.read()   
    if link not in processed_urls:
        global links
        links +=1
        with open(path, 'a') as file:
            file.write(f"\n{link}")
        return True
    else:
        return False

def extract_data(feed_url:str,domain):
    feed = feedparser.parse(feed_url)
    entries = feed.entries
    entries = sorted(entries,key=lambda entry:entry.published)
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

def send_data(entries,func,domain,chat_id):
    for entry in entries:
        message = func(entry)
        if update_files(f"./{domain}.txt",entry["link"]):
            try:
                bot.send_message(chat_id,message, parse_mode="html")
                time.sleep(5)
            except Exception as e:
                print(e)


urls = [animecorner_url,billboard_url,citizen_url,soompi_url]
channels = ["animecorner","billboard", "citizen","soompi"]
chat_ids = [animecorner_chat_id,billboard_chat_id,citizen_chat_id,soompi_chat_id]
functions = [billboard,billboard,send_citizen_data,billboard]
items = {}
for idx,channel in enumerate(channels):
    items[channel]= {
        "feed":urls[idx],
        "chat_id":chat_ids[idx],
        "func": functions[idx]
        }

def to_update():
    for (key,value) in items.items():
        domain = key
        url = value["feed"]
        chat_id = value["chat_id"]
        func = value["func"]
        try:
            data = extract_data(url,domain)
        except Exception as e:
            print(e)
        send_data(data,func,domain,chat_id)  
    
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
        update = bot.send_message(1095126805,f"Completed, Links sent: {links} ")
        time.sleep(30)
        bot.delete_message(update.chat.id,update.id)

    links = 0 

stop_polling_event = threading.Event()
def polling_thread():
    while not stop_polling_event.is_set():
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error in polling thread: {e}")
            time.sleep(5)
if __name__ == "__main__":
    print("Bot online")
    polling_thread_instance = threading.Thread(target=polling_thread)
    polling_thread_instance.start()
    while infinity:
        update()
        time.sleep(60*5)
    stop_polling_event.set()
    polling_thread_instance.join()


        


    
