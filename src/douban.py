import random
import re
import time
from urllib.parse import unquote, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from lxml import etree


DOUBAN_BASE = "https://book.douban.com/"
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3573.0 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': DOUBAN_BASE
}


class DoubanBookSearcher:
    

    DOUBAN_SEARCH_URL = "https://www.douban.com/search"
    DOUBAN_BOOK_CAT = "1001"
    DOUBAN_CONCURRENCY_SIZE = 3  # 查询条目数
    DOUBAN_BOOK_URL_PATTERN = re.compile(".*/subject/(\\d+)/?")

    def __init__(self):
        self.book_loader = DoubanBookLoader()
        # self.thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix='douban_async')

    def calc_url(self, href):
        query = urlparse(href).query
        params = {item.split('=')[0]: item.split('=')[1] for item in query.split('&')}
        url = unquote(params['url'])
        if self.DOUBAN_BOOK_URL_PATTERN.match(url):
            return url

    def load_book_urls_new(self, query):
        """根据关键字获取相关电子书的url

        Args:
            query (string):关键字_

        Returns:
            array: 返回相关电子书的url的数组
        """
        url = self.DOUBAN_SEARCH_URL
        params = {"cat": self.DOUBAN_BOOK_CAT, "q": query}
        res = requests.get(url, params, headers=DEFAULT_HEADERS)
        book_urls = []
        if res.status_code in [200, 201]:
            html = etree.HTML(res.content)
            alist = html.xpath('//a[@class="nbg"]')
            for link in alist:
                href = link.attrib['href']
                parsed = self.calc_url(href)
                if parsed and len(book_urls) < self.DOUBAN_CONCURRENCY_SIZE:
                    book_urls.append(parsed)
        return book_urls

    def search_books(self, query):
        """通过关键字搜索电子书信息

        Args:
            query (string): 关键字

        Returns:
            array: _description_
        """
        book_urls = self.load_book_urls_new(query)
        books = []
        
        for book_url in book_urls:
            book = self.book_loader.load_book(book_url)
            if(book is not None):
                books.append(book)
        # 转化成audiobookshelf对象
        matches = {"matches":books}
        return matches
    
    


class DoubanBookHtmlParser:
    DOUBAN_BOOK_URL_PATTERN = re.compile(".*/subject/(\\d+)/?")

    def __init__(self):
        self.id_pattern = self.DOUBAN_BOOK_URL_PATTERN
        self.date_pattern = re.compile("(\\d{4})-(\\d+)")
        self.tag_pattern = re.compile("criteria = '(.+)'")

    def parse_book(self, url, book_content):
        book =BookMetadata()
        html = etree.HTML(book_content)
        title_element = html.xpath("//span[@property='v:itemreviewed']")
        book.title = self.get_text(title_element)
        share_element = html.xpath("//a[@data-url]")
        if len(share_element):
            url = share_element[0].attrib['data-url']
        # book.url = url
        id_match = self.id_pattern.match(url)
        if id_match:
            book.id = id_match.group(1)
        img_element = html.xpath("//a[@class='nbg']")
        if len(img_element):
            cover = img_element[0].attrib['href']
            if not cover or cover.endswith('update_image'):
                book.cover = ''
            else:
                book.cover = cover
        # rating_element = html.xpath("//strong[@property='v:average']")
        # book.rating = self.get_rating(rating_element)
        
        elements = html.xpath("//span[@class='pl']")
        for element in elements:
            text = self.get_text(element)
            if text.startswith("作者") :
                authors = []
                authors.extend([self.get_text(author_element) for author_element in
                                     filter(self.author_filter, element.findall("..//a"))])
                book.author = ' '.join(authors)
            elif text.startswith("出版社"):
                book.publisher = self.get_tail(element)
            elif text.startswith("副标题"):
                 book.subtitle = self.get_tail(element)
            elif text.startswith("出版年"):
                book.publishedYear = self.get_publish_date(self.get_tail(element))
            elif text.startswith("ISBN"):
                book.isbn= self.get_tail(element)
            
        summary_element = html.xpath("//div[@id='link-report']//div[@class='intro']")
        if len(summary_element):
            book.description = etree.tostring(summary_element[-1], encoding="utf8").decode("utf8").strip()
            book.description = self.remove_html_tags(book.description)
        tag_elements = html.xpath("//a[contains(@class, 'tag')]")
        if len(tag_elements):
            book.tags = [self.get_text(tag_element) for tag_element in tag_elements]
        else:
            book.tags = self.get_tags(book_content)
        return book

    def get_tags(self, book_content):
        tag_match = self.tag_pattern.findall(book_content)
        if len(tag_match):
            return [tag.replace('7:', '') for tag in
                    filter(lambda tag: tag and tag.startswith('7:'), tag_match[0].split('|'))]
        return []

    def get_publish_date(self, date_str):
        if date_str:
            date_match = self.date_pattern.fullmatch(date_str)
            if date_match:
                date_str = "{}-{}-1".format(date_match.group(1), date_match.group(2))
        return date_str

    def get_rating(self, rating_element):
        return float(self.get_text(rating_element, '0')) / 2

    def author_filter(self, a_element):
        a_href = a_element.attrib['href']
        return '/author' in a_href or '/search' in a_href

    def get_text(self, element, default_str=''):
        text = default_str
        if len(element) and element[0].text:
            text = element[0].text.strip()
        elif isinstance(element, etree._Element) and element.text:
            text = element.text.strip()
        return text if text else default_str

    def get_tail(self, element, default_str=''):
        text = default_str
        if isinstance(element, etree._Element) and element.tail:
            text = element.tail.strip()
            if not text:
                text = self.get_text(element.getnext(), default_str)
        return text if text else default_str
    
    def remove_html_tags(self,text):
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    

class DoubanBookLoader:

    def __init__(self):
        self.book_parser = DoubanBookHtmlParser()
        
    def load_book(self, url):
        """_summary_

        Args:
            url (String): 豆瓣图书的url

        Returns:
            BookMetadata: 图书元数据
        """
        book = None
        self.random_sleep()
        start_time = time.time()
        res = requests.get(url, headers=DEFAULT_HEADERS)
        if res.status_code in [200, 201]:
            print("下载书籍:{}成功,耗时{:.0f}ms".format(url, (time.time() - start_time) * 1000))
            book_detail_content = res.content
            book = self.book_parser.parse_book(url, book_detail_content.decode("utf8"))
        return book

    def random_sleep(self):
        random_sec = random.random() / 10
        print("Random sleep time {}s".format(random_sec))
        time.sleep(random_sec)


class BookMetadata:
    """元数据
    """
    id = ""
    title = "" # 标题
    subtitle = "" # 副标题
    author = ""
    narrator = ""
    publisher = ""
    publishedYear = ""
    description = ""
    cover = "" # 封面
    isbn = ""
    asin = ""
    genres = ""
    tags = []
    series = ""
    language = ""
    duration = 0

    def __init__(self):
        pass







