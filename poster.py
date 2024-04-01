import feedparser
from bs4 import BeautifulSoup
import html
import string
from logging import getLogger
import json
from telegraph import Telegraph
from mongodb import Database


class RSSPoster():
    def __init__(self):
        self.FEEDS = self.get_feeds()
        self.logger = getLogger(__name__)
        self.database = Database()

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
            url = url.replace("www.", "")
            domain = url.split("//")[1].split("/")[0]
            if ".com" in url:
                return domain.replace(".com", "").split(".")[0]
            return domain.replace(".co", "").split(".")[0]
        except Exception as e:
            self.logger.error(f"Error {e} extracting from {url}:")
            return None

    def extract_data(self, feed_url: str):
        """Extracts data from rss url"""
        parser = feedparser.parse(feed_url)
        domain = self.get_domain_from_url(feed_url)
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
                item["domain"] = domain
            data.append(item)
        return data

    def format(self, entry: dict) -> dict:
        """Compiles all entry data into a message text"""
        try:
            entry = self.get_citizen_content(entry)
        except BaseException:
            pass
        if entry.get("domain") == "anitrendz":
            self.get_telegraph_link(entry)
        tags = entry["tags"]
        img_src = entry.get("img_src")
        caption = entry.get("caption")
        telegraph_url = entry.get("telegraph_url")
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
        link = entry["link"] if telegraph_url is None else telegraph_url
        published = f'Published on {updated.split("+")[0].replace("T", " at ")}' if published is None else f'Published on {published}'
        caption = '' if caption is None else caption
        text = f"<a href='{link}'><b>{entry['title']}</b></a>\n\n{summary}<i>{author}</i>\n\n{published}\n\n<a href='{img_src}'>{caption}</a>"
        message = {"text": text, "url": entry['link']}
        return message

    def get_telegraph_link(self, entry, soup=None):
        if soup is None:
            content = entry["content"][0]["value"].replace(
                "&lt;!doctype html>", "")
            soup = BeautifulSoup(content, "html.parser")
        existing = self.database.json_data.find_one({"url": entry["link"]})
        if existing == None:
            telegraph_url = self.to_telegraph(title=entry["title"], soup=soup)
            entry["telegraph_url"] = telegraph_url

    def get_citizen_content(self, entry):
        content = entry["content"][0]["value"].replace(
            "&lt;!doctype html>", "")
        soup = BeautifulSoup(content, "html.parser")
        """For links from citizen and formats its data uniquely"""
        img_tag = soup.find('img')
        img_src = img_tag['src'] if img_tag else None
        caption = soup.find('figcaption').text
        self.get_telegraph_link(entry, soup)
        entry["img_src"] = img_src
        entry["caption"] = caption
        return entry

    def get_messages(self, url: dict) -> list:
        """Gets all the messages to be sent from a feed"""
        entries = self.extract_data(url)
        messages = [self.format(entry) for entry in entries]
        return messages

    def filter_tags(self, soup: BeautifulSoup):
        allowed_tags = ['a', 'blockquote', 'br', 'em',
                        'figure', 'h3', 'h4', 'img', 'p', 'strong']

        for tag in soup.find_all(True):
            if tag.name not in allowed_tags:
                tag.name = 'p'  # Change disallowed tags to 'p' tag


# Parse HTML

    def to_telegraph(self, soup: BeautifulSoup, title):

        # Filter tags
        self.filter_tags(soup)

        # Get the filtered HTML string
        filtered_html_string = str(soup)

        telegraph = Telegraph()
        telegraph.create_account(short_name="citizen")
        response = telegraph.create_page(
            title, html_content=filtered_html_string)
        return response["url"]
