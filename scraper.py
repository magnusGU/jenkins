"""The scraper scrapes the input-rss feeds, takes all new articles,
 and parses the full-length articles from the original website
 """
import datetime
import re
import requests

import feedparser


def get_feeds(urls, updated):
    """Returns rss feeds as a list, if the feeds have been updated"""
    feeds = []
    for url, time in zip(urls, updated):
        feeds.append(feedparser.parse(url, modified=time))
    return feeds


def get_articles(feed, updated):
    """Returns all new articles as a list containing tuples of
    (title, link, summary, datetime object, HTML article-content)
    """
    articles = []
    for post in feed:
        time = _time_comparison(post.updated, updated)
        if time:
            print(post['title'])
            articles.append({
                "headline": post['title'],
                "link": post['link'],
                "summary": post['summary'],
                "date": time,
                "content": format_content(get_content(post['link']).text)
            })
        else:
            # As far as have been observed all posts appear in order sorted on
            # time, so break as soon as first repeat appears
            break
    return articles


def _time_comparison(date1, date2):
    """Returns datetime object if first timestamp/parameter is most up-to-date."""

    def _tryallformats(date):
        try:
            return datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %Z')
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            raise ValueError("Time format not supported yet")

    if date2 == 0:
        timestamp1 = _tryallformats(date1).replace(tzinfo=None)
        return timestamp1

    timestamp1 = _tryallformats(date1).replace(tzinfo=None)
    timestamp2 = _tryallformats(date2).replace(tzinfo=None)

    if timestamp1 == max(timestamp1, timestamp2):
        return timestamp1

    return False


def get_content(url):
    """Returns HTML content from parameter url"""
    hdr = {'User-Agent': 'Mozilla/5.0'}
    content = requests.get(url, headers=hdr)

    return content


def format_content(unformat):
    """Returns cleaned text, with most HTML stuff removed"""
    try:
        if '<p class="story-body__introduction">' in unformat:
            sindex = unformat.find('<p class="story-body__introduction">')
            eindex = unformat.find('<div id="share-tools">')
            cut = unformat[sindex:eindex]
        elif '<div class="content__article-body' in unformat:
            sindex = unformat.find('<div class="content__article-body')
            eindex = unformat.find('<div class="after-article')
            cut = unformat[sindex:eindex]
        elif '<div class="StandardArticleBody_body">' in unformat:
            sindex = unformat.find('<div class="StandardArticleBody_body">')
            eindex = unformat.find('</p><div class="Attribution_container">')
            cut = unformat[sindex:eindex]

        cut = re.sub(r'\<[^>]*\>', ' ', cut)
        text = re.sub(r'\/\*\*\/[^>]*\/\*\*\/', ' ', cut)  # /**/
        return text
    except NameError:
        # The post was probably a video-news or something unique
        print("Empty")
        return ""

# Lists of equal length, one for urls to scrape, and one of times the urls
# were last scraped. If no such time exist, send [.., 0,..]


def scrape(urls=['http://feeds.bbci.co.uk/news/rss.xml',], updated=[0,]):
    """Returns list of articles found in feeds from url parameter
    and the date those feeds were last updated
    """
    # https://www.techradar.com/rss
    def _tryattr(source, attr):
        try:
            value = getattr(source, attr)
            return value
        except AttributeError:
            return False

    feeds = get_feeds(urls, updated)

    articles = []
    last_modified = []
    for news, time in zip(feeds, updated):
        if(any('title' for x in news) and
           any('status' for x in news) and
           any('updated' for x in news)):
            title = _tryattr(news, 'title')
            if not title:
                title = _tryattr(news.feed, 'title')
            status = _tryattr(news, 'status')
            if not status:
                status = _tryattr(news.feed, 'status')
            modified = _tryattr(news, 'modified')
            if not modified:
                modified = _tryattr(news.feed, 'modified')
        else:
            print("Missing title, status or updated fields")
            continue

        print(f'{title}, Status of news feed: {status}, Last updated: {modified}')
        if modified:
            last_modified.append(modified)
        else:
            last_modified.append(time)

        # Not all feeds support the modified tag, so double check last updated
        if modified == time or status == '304':
            continue

        articles.append(get_articles(news['entries'], time))

    return articles, last_modified
