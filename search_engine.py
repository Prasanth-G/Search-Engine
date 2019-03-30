import sys
import urllib.request  #open a port and establish a connection
import bs4  #Beautiful Soup - for parsing
import re   #Regular Expressions
import queue
from rfc3987 import parse
import requests
import json
import stemming.porter2 as stemming
import pprint

class crawler:

    just_crawl = 100
    __to_crawl = queue.LifoQueue()
    __crawled_list = []
    __crawled = {}
    __rank = {}
    keywords_database = {}
    def clear_to_crawl(self):
        self.__to_crawl = queue.LifoQueue()
    def crawled(self):
        for each in self.__crawled:
            print(each)
    def crawled_list(self):
        for each in self.__crawled_list:
            print(each)
    def rank(self):
        for each in self.__rank:
            print(each)
    def to_crawl(self):
        print(self.__to_crawl.empty)
    def __check_protocol(self,link):
        if not link[0].isalnum:
            return link
        check_protocol = re.compile(r'(?:http|ftp)s?://')
        protocol_specified = check_protocol.match(link)
        if not protocol_specified:
            link = 'http://' + link
        return link
    def __is_valid(self,url):
        expr_url = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
        if expr_url.match(url):
            return True
        return False
    def __is_blocked(self,url):
        blocked_domains = {'www.twitter.com':1,'twitter.com':1,'www.fb.com':1,'www.facebook.com':1,'facebook.com':1,'www.linkedin.com':1,'linkedin.com':1,'plus.google.com':1,'accounts.google.com':1,'hangouts.google.com':1,'www.youtube.com':1}
        p = parse(url)
        if blocked_domains.get(p['authority']):
            return True
        return False
    def __truncate_url(self,url,i):
        p = parse(url)
        path = p['path']
        if path:
            path = path[1:].split('/')
            if len(path) > i and p['authority']:
                path = path[:i-len(path)]
                url = p['authority'] + '/' + '/'.join(path)
        return url

    def __add_to_crawl(self,link,parent_link = None):
        url = self.__check_protocol(link)
        valid = self.__is_valid(url)
        blocked = self.__is_blocked(url)
        if parent_link:
            trunc_url = self.__truncate_url(url,2)
            if valid and not blocked and trunc_url not in self.__crawled:
                self.__to_crawl.put(trunc_url.lower())
                trunc_url = trunc_url.lower()
                if trunc_url not in self.__crawled[parent_link]:
                    self.__crawled[parent_link].append(trunc_url.lower())
                return True
        else:
            if valid and not blocked and url not in self.__crawled:
                self.__to_crawl.put(url.lower())
                return True
        return False
    def __add_to_keywords(self,keyword,url_index):
        keyword = keyword.lower()
        keyword = stemming.stem(keyword)
        if keyword not in self.keywords_database:
            self.keywords_database[keyword] = []
        self.keywords_database[keyword].append(url_index)
    def print(self):
        print(self.__to_crawl.empty())
    def seed_links(self,links):
        if type(links) == list:
            for each_link in links:
                self.__add_to_crawl(each_link)
        elif type(links) == str:
            self.__add_to_crawl(links)

    def start_crawling(self):
        count = 0
        while not self.__to_crawl.empty() and len(self.__crawled_list) <= self.just_crawl:
            try:
                count += 1
                print(count)
                url = self.__to_crawl.get()
                print("URL : ",url)
                if url not in self.__crawled:
                    self.__crawled[url] = []
                    url_index = len(self.__crawled_list)
                    self.__crawled_list.append(url)

                    print("attempting to open : ",url)
                    response = requests.get(url)
                    print("webpage loaded")

                    soup_object = bs4.BeautifulSoup(response.text,'html.parser')
                    #extract hyperlinks
                    a_tags = soup_object('a')
                    for tag in a_tags:
                        if tag.get('rel') != 'nofollow':
                            hyperlink = tag.get('href')
                            if hyperlink:
                                self.__add_to_crawl(hyperlink,url)

                    #extract meta data
                    p = parse(url)
                    name = p['authority']
                    if name:
                        name = re.findall('\w+\w+\w+',name)
                        if len(name) == 3:
                            server_name,domain_name,domain_extension = name
                            self.__add_to_keywords(domain_name,url_index)
                    #title
                    title_tags = soup_object('title')
                    for tag in title_tags:
                        tag = str(tag)
                        title = re.findall(r'<title>(.+)</title>',tag)
                        if title:
                            title = title[0]
                            title = re.findall('[\w+]+',title)
                            #add title to the keywords_database
                            for each_word in title:
                                self.__add_to_keywords(each_word,url_index)
            except:
                print("Error ...")
                del(self.__crawled[url])
                self.__crawled_list.pop()
                
                continue
    def store(self):
        file = open(os.path.join('data', 'keywords_database.txt'),'w')
        database_str = json.dumps(self.keywords_database)
        file.write(database_str)
        file.close()
        file = open(os.path.join('data', 'to_crawl.txt'),'w')
        #serializing queue into list
        to_crawl = []
        while not self.__to_crawl.empty():
            to_crawl.append(self.__to_crawl.get())
        to_crawl.reverse()
        to_crawl = json.dumps(to_crawl)
        file.write(to_crawl)
        file.close()
        file = open(os.path.join('data', 'crawled_list.txt'),'w')
        crawled_list = json.dumps(self.__crawled_list)
        file.write(crawled_list)
        file.close()
        file = open(os.path.join('data', 'crawled.txt'),'w')
        crawled = json.dumps(self.__crawled)
        file.write(crawled)
        file.close()

    def restore(self):
        file = open(os.path.join('data', 'keywords_database.txt'),'r')
        file_read = file.read()
        if file_read:
            self.keywords_database = json.loads(file_read)
        file.close()
        file = open(os.path.join('data', 'to_crawl.txt'),'r')
        #deserialize list to queue
        to_crawl = file.read()
        if to_crawl:
            to_crawl = json.loads(to_crawl)
            for each in to_crawl:
                self.__to_crawl.put(each)
        file.close()
        file = open(os.path.join('data', 'crawled_list.txt'),'r')
        crawled_list = file.read()
        if crawled_list:
            self.__crawled_list = json.loads(crawled_list)
        file.close()
        file = open(os.path.join('data', 'crawled.txt'),'r')
        crawled = file.read()
        if crawled:
            self.__crawled = json.loads(crawled)
        file.close()
    def calc_pagerank(self,n):
        d = 0.85
        numloops = n
        ranks = {}
        adj_list = self.__crawled
        npages = len(adj_list)
        for each in adj_list:
            ranks[each] = 1/npages
        for i in range(numloops):
            newranks = {}
            for each_ele in adj_list:
                newrank = (1 - d)/npages
                #sum rank of all inlinks
                for node in adj_list:
                    if each_ele in adj_list[node]:
                        newrank += d * (ranks[node] / len(adj_list[node]))
                newranks[each_ele] = newrank
            ranks = newranks
        self.__rank = ranks

    def query(self,search_query):
        input_str = search_query.split()
        pages_url = {}
        for each_word in input_str:
            if each_word in self.keywords_database:
                for url_index in self.keywords_database[each_word]:
                    #print(url_index)
                    url = self.__crawled_list[url_index]
                    if url not in pages_url:
                        pages_url[url] = 1
        pages_url_list = sorted(pages_url,key = pages_url.get,reverse = True)   #sort pages according to frequency of search query
        final_rank = {}
        for each_url in pages_url_list:
            if each_url in self.__rank:
                final_rank[each_url] = self.__rank[each_url]
        pprint.pprint(final_rank)
        final_list = sorted(final_rank,key = final_rank.get,reverse = True)
        return final_list
        
a = crawler()
a.restore()
a.calc_pagerank(30)

#http://computer.howstuffworks.com/internet/basics/search-engine3.htm
