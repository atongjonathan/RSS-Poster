import feedparser
from bs4 import BeautifulSoup
import html
import string
from logging import getLogger
import json
from telegraph import Telegraph


class RSSPoster():
    def __init__(self):
        self.FEEDS = self.get_feeds()
        self.logger = getLogger(__name__)

    def get_feeds(self) -> list:
        """Gets feeds from config.json and adding domain key with value to it"""
        with open("config.json") as file:
            FEEDS = json.load(fp=file)
        for feed in FEEDS:
            feed["domain"] = self.get_domain_from_url(feed["url"]).title()
        return FEEDS

    def get_domain_from_url(self, url: str) -> str:
        """Gets the domain given a url"""
        try:
            # Split the URL by "//" and take the second part
            url = url.replace("www", "")
            domain = url.split("//")[1].split("/")[0]
            return domain.replace(".com", "").split(".")[0]
        except Exception as e:
            self.logger.error(f"Error {e} extracting from {url}:")
            return None

    def extract_data(self, feed_url: str):
        """Extracts data from rss url"""
        parser = feedparser.parse(feed_url)
        entries = parser.entries
        data = []
        attributes = [
            "tags",
            "content",
            "author",
            "title",
            "link",
            "summary",
            "published",
            "updated",
            "description"]
        for entry in entries:
            item = {}
            for attribute in attributes:
                try:
                    item[attribute] = html.unescape(getattr(entry, attribute))
                except BaseException:
                    item[attribute] = None
            data.append(item)
        return data

    def format(self, entry) -> dict:
        """Compiles all entry data into a message text"""
        try:
            content = entry["content"][0]["value"].replace("!doctype html>", "")
            content_text, img_src, caption = self.get_citizen_content(content)
        except BaseException:
            content_text, img_src, caption = None, None, None
        tags = entry["tags"]
        author = entry["author"]
        published = entry["published"]
        updated = entry["updated"]
        summary = entry['summary']
        description = entry["description"]
        summary = description if summary is None else summary
        summary_soup = BeautifulSoup(summary, "html.parser")
        if len(summary_soup.find_all("p")) > 0:
            p_list = summary_soup.find_all("p")
        else:
            p_list = [summary_soup]
        summary = ''.join(
            [item.text for item in p_list if "The post" not in item.text])
        tags = '' if tags is None else tags
        tags = [
            f'#{tag["term"].strip(string.punctuation.replace(" ", ""))}' for tag in tags]
        tags = ", ".join(tags)
        author = "" if author is None else f"\n\nArticle written by <b>{author}</b>"
        published = f'Published on {updated.split("+")[0].replace("T", " at ")}' if published is None else f'Published on {published}'
        content_text = "" if content_text is None else content_text
        caption = '' if caption is None else caption
        text = f"<a href='{entry['link']}'><b>{entry['title']}</b></a>\n\n{summary}<i>{author}</i>\n\n{published}\n\n<a href='{img_src}'>{caption}</a>"
        message = {"text": text, "url": entry['link']}
        return message

    def get_citizen_content(self, content):
        """For links from citizen and formats its data uniquely"""
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

    def get_messages(self, url: dict) -> list:
        """Gets all the messages to be sent from a feed"""
        entries = self.extract_data(url)
        messages = [self.format(entry) for entry in entries]
        return messages

    def filter_tags(self, soup):
        allowed_tags = ['a', 'blockquote', 'br', 'em',
                        'figure', 'h3', 'h4', 'img', 'p', 'strong']

        for tag in soup.find_all(True):
            if tag.name not in allowed_tags:
                tag.name = 'p'  # Change disallowed tags to 'p' tag

        # Allow embedded youtube and vimeo iframe tags
        for iframe in soup.find_all('iframe'):
            if 'youtube.com' in iframe.get('src') or 'vimeo.com' in iframe.get('src'):
                iframe.unwrap()
            else:
                iframe.decompose()


# Parse HTML

    def to_telegraph(self, html_string, title):
        soup = BeautifulSoup(html_string, 'html.parser')

        # Filter tags
        self.filter_tags(soup)

        # Get the filtered HTML string
        filtered_html_string = str(soup)

        telegraph = Telegraph()
        telegraph.create_account(short_name="citizen")
        response = telegraph.create_page(
            title, html_content=filtered_html_string)
        return response["url"]
