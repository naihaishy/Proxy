# -*- coding:utf-8 -*-
# @Time : 2019/4/14 19:46
# @Author : naihai
"""IP 代理类"""
import logging
import time

import requests
from bs4 import BeautifulSoup
import schedule
from joblib import delayed, Parallel


class Link(object):
    def __init__(self, schema, host, port):
        self.port = port
        self.host = host
        self.schema = schema
        self.value = "{0}://{1}:{2}".format(schema, host, port)

    def __eq__(self, other):
        return self.port == other.port


class Proxy(object):
    def __init__(self, url, need_pagination=False):
        self.url = url
        self.links = []
        self.need_pagination = need_pagination  # 是否需要翻页
        self.page_fix = False  # 下一页链接已经得到 无需再次查找
        self.next_pages = set()  # 下一页

        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36',
        }
        self.name = "Proxy"

    def run(self, target=None):
        logging.info("Starting {0} ...".format(self.name))
        self._request()
        logging.info("Request {0} done ...".format(self.name))

        if self.need_pagination:
            logging.info("Starting {0} next pages ...".format(self.name))
            for page in self.next_pages:
                self.url = page
                self._request()
                logging.info("Request {0} page {1} done ...".format(self.name, page))

        self._validate(target)

    def schedule(self, target=None):
        """
        定时作业
        每隔1个小时重新获取最新的代理ip
        每隔10分钟重新验证ip的有效性
        :return:
        """
        schedule.every(1).hour.do(self._request)
        schedule.every(10).minutes.do(self._validate, target)
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每隔60秒检查job

    def _request(self):
        try:
            response = requests.get(url=self.url, headers=self.headers, timeout=10)
            self._parse(response)
        except requests.exceptions.RequestException as e:
            logging.warning("Request {0} failed in {1}: {2}".format(self.name, self.url, repr(e)))

    def _parse(self, response):
        """ response解析函数 需要子类重写该函数 """
        pass

    @staticmethod
    def _validate_host(proxy_name, link, target):
        try:
            proxies = {link.schema: link.host + ":" + link.port}
            response = requests.get(url=target, proxies=proxies, timeout=3)
            if response.status_code == 200:
                return link
        except Exception as e:
            logging.info(
                "Validate {0} link {1} in target {2} failed: {3}".format(proxy_name, link.value, target, repr(e)))

    def _validate(self, target=None):
        """
        验证代理主机在目标站点上的有效性
        :param target: 目标站点 为None则测试百度
        :return:
        """
        target = target if target is not None else "https://www.baidu.com/"

        delayed_list = (
            delayed(Proxy._validate_host)(self.name, link, target) for link in self.links
        )
        valid_links = Parallel(n_jobs=40, verbose=10, prefer="threads")(delayed_list)
        self.links = [link for link in valid_links if link is not None]  # 更新links


# 西刺代理
class XiciProxy(Proxy):
    def __init__(self):
        super().__init__(url="https://www.xicidaili.com/nn", need_pagination=True)
        self.name = "XiciProxy"

    def _parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        trs = soup.find_all("table", attrs={"id": "ip_list"})[0].find_all("tr")[1:]
        for tr in trs:
            tds = tr.find_all("td")
            host = tds[1].contents[0]
            port = tds[2].contents[0]
            schema = str(tds[5].contents[0]).lower()
            if schema in ["http", "https"]:
                link = Link(schema, host, port)
                self.links.append(link)

        # 第一次 获取下一页全部链接
        if self.need_pagination and not self.page_fix:
            self.page_fix = True
            for i in range(2, 10, 1):
                self.next_pages.add("https://www.xicidaili.com/nn/{0}".format(i))


# 31代理
class SanyiProxy(Proxy):
    def __init__(self):
        super().__init__(url="http://31f.cn/http-proxy/")
        self.name = "SanyiProxy"

    def _parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        trs = soup.find_all("table", attrs={"class": "table table-striped"})[0].find_all("tr")[1:]
        for tr in trs:
            tds = tr.find_all("td")
            host = tds[1].contents[0]
            port = tds[2].contents[0]
            schema = "http"
            link = Link(schema, host, port)
            self.links.append(link)


# jiangxianli代理
class JiangXianLiProxy(Proxy):
    def __init__(self):
        super().__init__(url="http://ip.jiangxianli.com/", need_pagination=True)
        self.name = "JiangXianLiProxy"

    def _parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        trs = soup.find_all("table", attrs={"class": "table"})[0].tbody.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            host = tds[1].contents[0]
            port = tds[2].contents[0]
            schema = str(tds[4].contents[0]).lower()
            if schema in ["http", "https"]:
                link = Link(schema, host, port)
                self.links.append(link)

        # 第一次 获取下一页全部链接
        if self.need_pagination and not self.page_fix:
            self.page_fix = True
            next_pages = soup.find_all("ul", attrs={"class": "pagination"})[0].find_all('a')
            for page in next_pages:
                self.next_pages.add(page.get("href"))


# 中国IP代理
class CNProxy(Proxy):
    def __init__(self):
        super().__init__(url="https://cn-proxy.com/")
        self.name = "CNProxy"

    def _parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all("table", attrs={"class": "sortable"})
        for table in tables:
            trs = table.tbody.find_all("tr")
            for tr in trs:
                tds = tr.find_all("td")
                host = tds[0].contents[0]
                port = tds[1].contents[0]
                schema = "http"
                link = Link(schema, host, port)
                self.links.append(link)


# 所有代理汇总
class AllProxy(object):
    def __init__(self):
        self.links = []
        self.proxies = []

        self.proxies.append(SanyiProxy())
        self.proxies.append(XiciProxy())
        self.proxies.append(JiangXianLiProxy())
        self.proxies.append(CNProxy())

    def run(self, target=None):
        for proxy in self.proxies:
            proxy.run(target)
            for link in proxy.links:
                if link not in self.links:
                    self.links.append(link)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line: %(lineno)d] -%(levelname)s: %(message)s')

    proxy_ = AllProxy()
    proxy_.run("https://movie.douban.com")
    with open("proxies.txt", "w") as wf:
        for link_ in proxy_.links:
            print(link_.value)
            wf.write(link_.value + "\n")
