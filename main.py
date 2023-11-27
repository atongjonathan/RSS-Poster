import feedparser
import os
from bs4 import BeautifulSoup
from telebot import TeleBot

TELGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = TeleBot(TELGRAM_BOT_TOKEN, parse_mode="HTML")

billboard_chat_id = -1002103516422
citizen_chat_id = -1001908193905
animecorner_chat_id = -1002056978598
billboard_url = "https://billboard.com/feed/"
citizen_url = "https://citizen.digital/feed.xml"
animecorner_url = "https://animecorner.me/feed/"
processed_urls = set()



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
    
def update_files(path,entry):
    with open(path, 'r') as file:
        processed_urls = file.readlines()   
    if entry["link"] not in processed_urls:
        print("link absent")
        with open(path, 'a') as file:
            file.write(f"\n{entry['link']}")
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
        if update_files(f"./{domain}.txt",entry):
            bot.send_message(chat_id,message, parse_mode="html")

urls = [animecorner_url,billboard_url,citizen_url]
channels = ["animecorner","billboard", "citizen"]
chat_ids = [animecorner_chat_id,billboard_chat_id,citizen_chat_id]
functions = [billboard,billboard,send_citizen_data]
items = {}
for idx,channel in enumerate(channels):
    items[channel]= {
        "feed":urls[idx],
        "chat_id":chat_ids[idx],
        "func": functions[idx]
        }

for idx,(key,value) in enumerate(items.items()):
    domain = key
    url = value["feed"]
    chat_id = value["chat_id"]
    func = value["func"]
    data = extract_data(url,domain)
    send_data(data,func,domain,chat_id)    



        


    
