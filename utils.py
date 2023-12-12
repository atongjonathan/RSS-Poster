import feedparser
from bs4 import BeautifulSoup
from logger import LOGGER
import html
import string


def get_citizen_content(content):
    soup = BeautifulSoup(content, "html.parser")
    p = soup.find_all("p")
    div = soup.find_all("div")
    img_tag = soup.find('img')
    img_src = img_tag['src'] if img_tag else None
    caption = soup.find('figcaption').text
    content_text = ""
    for paragraph in p:
        spans = paragraph.find_all("span", class_="tg-spoiler")
        if spans:
            for span in spans:
                content_text += '\n' + span.text + '\n'
        else:
            content_text += '\n' + paragraph.text.strip().replace("\n", " ") + '\n'
    if content_text == "":
        for paragraph in div:
            content_text += paragraph.text
    return content_text, img_src, caption

def format(entry):
    try:
        content = entry["content"][0]["value"]
        content_text, img_src, caption = get_citizen_content(content)
    except:
        content_text, img_src, caption = None,None,None
    tags = entry["tags"]
    author = entry["author"]
    published = entry["published"]
    updated = entry["updated"]
    summary = entry['summary']
    description = entry["description"]
    summary = description if summary == None else summary
    summary_soup = BeautifulSoup(summary, "html.parser")
    if len(summary_soup.find_all("p")) > 0:
        p_list = summary_soup.find_all("p")
    else:
        p_list = [summary_soup]
    summary = ''.join([item.text  for item in p_list if "The post" not in item.text])
    tags = '' if tags == None else tags
    tags = [f'#{tag["term"].strip(string.punctuation.replace(" ", ""))}' for tag in tags]
    tags = ", ".join(tags)
    author = "" if author is None else f"Article written by <b>{author}</b>"
    published = f'Published on {updated.split("+")[0].replace("T", " at ")}' if published is None else f'Published on {published}'
    content_text = "" if content_text is None else content_text
    caption = '' if caption is None else caption
    message = f"<a href='{entry['link']}'><b>{entry['title']}</b></a>\n\n{summary}<i>{author}</i>\n\n{published}\n\n<a href='{img_src}'>{caption}</a>"
    return message, entry['link']


def extract_data(feed_url: str):
    parser = feedparser.parse(feed_url)
    entries = parser.entries
    data = []
    attributes = ["tags", "content","author", "title", "link", "summary", "published", "updated", "description"]
    for entry in entries:
        item = {}
        for attribute in attributes:
            try:
                item[attribute] = html.unescape(getattr(entry, attribute))
            except:
                item[attribute]  = None
        data.append(item)
    return data
