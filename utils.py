import feedparser
from bs4 import BeautifulSoup
from logger import LOGGER
processed_urls = set()


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
                content_text += '\nStart-span\n' + span.text + '\nEnd-start\n'
        else:
            content_text += '\n' + paragraph.text.strip().replace("\n", " ") + '\n'
    if content_text == "":
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
        LOGGER.error(f"No link found for for {title}")
    except BaseException:
        pass
    finally:
        processed_urls.add(link)
    return message


def billboard(entry):
    link = entry["link"]
    title = entry["title"]
    date = entry["date"]
    summary = entry["summary"]
    author = entry["author"]
    try:
        tags = ', '.join(entry["tags"])
    except KeyError:
        tags = ""

    summary = summary.replace("<p>", "").replace("</p>", "")
    message = f"<a href='{link}'><b>{title}</b></a>\n\n{summary}\n\n{tags}\n\n<i>Article written by <b>{author}</b>\nPublished on {date}</i>"
    return message


def extract_data(feed_url: str, domain):
    feed = feedparser.parse(feed_url)
    entries = feed.entries
    data = []
    for entry in entries:

        item = {
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary
        }
        if domain == "billboard" or domain == "soompi" or domain == "animecorner":
            try:
                item["tags"] = [
                    f'#{tag["term"].replace(" ","")}' for tag in entry.tags]
            except KeyError:
                pass
        item["date"] = entry.published if domain != "tmz" else entry["updated"]
        item["author"] = entry if "citizen" in domain else entry.author
        item["html_content"] = entry.content[0].value if "citizen" in domain else None
        data.append(item)
    sorted_data = sorted(data, key=lambda entry: entry["date"])

    return sorted_data
