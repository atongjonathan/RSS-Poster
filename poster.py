import feedparser
from bs4 import BeautifulSoup
import html
import string
from logging import getLogger
import json
from telegraph import Telegraph
import html


class RSSPoster():
    def __init__(self):
        self.FEEDS = self.get_feeds()
        self.logger = getLogger(__name__)
        self.telegraph = Telegraph()
        self.telegraph.create_account("Citizen")

    def get_feeds(self) -> list:
        """Gets feeds from config.json and adding domain key with value to it

            Returns:
                FEEDS (list) a list of dictionaries including:
                    - 'chat_id (int)'
                    - 'url' (str) 
                    - ''domain' (str)
        """
        with open("config.json") as file:
            FEEDS = json.load(fp=file)
        for feed in FEEDS:
            feed["domain"] = self.get_domain_from_url(feed["url"]).title()
        return FEEDS

    def get_domain_from_url(self, url: str) -> str:
        """Gets the domain given a url

            Args:
                - 'url' (str) - feed url
            
            Returns:
                - 'domain (str)'
        
        """
        try:
            # Split the URL by "//" and take the second part
            url = url.replace("www", "")
            domain = url.split("//")[1].split("/")[0]
            return domain.replace(".com", "").split(".")[0]
        except Exception as e:
            self.logger.error(f"Error {e} extracting from {url}:")
            return None

    def extract_data(self, feed_url: str)-> list:
        """Extracts data from rss url
        
        Args:
            - 'feed_url' (str): RSS feed url

        Returns a list of dict containing:
            - 'tags' (list): of dicts including:
                - 'term': The tag string
                - 'scheme': None
                - 'label': None
            - 'content': HTML string of content data
            - 'author' (str):
            - 'title' (str):
            - 'link' (str):
            - 'summary' (str): HTML string of summary 
            - 'published' (str):
            - 'updated' (str):
            - 'description' (str):      
             
        """
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
        """Compiles all entry data into a message text
        
        Args:
            - entry (dict): Instance of a single from an extracted data

        Returns:
            - message (dict): including:
                - text (str): HTML formatted text
                - url (str): Instant view url 
        """
        content = html.unescape(entry["content"][0]["value"].strip())
        print(content)
        response = self.telegraph.create_page(title=entry['title'], content=content)
        print(response)
        try:
            content = entry["content"][0]["value"]
            
            
            entry["link"] = response["url"]
            content_text, img_src, caption = self.get_citizen_content(content)
        except Exception as e:
            print(e)
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

    def get_messages(self, url: str) -> list:
        """Gets all the formatted messages to be sent from a feed"""
        entries = self.extract_data(url)
        messages = [self.format(entry) for entry in entries]
        return messages
