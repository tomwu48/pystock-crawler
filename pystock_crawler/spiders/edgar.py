import os

from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule

from pystock_crawler import utils
from pystock_crawler.loaders import ReportItemLoader


class URLGenerator(object):

    def __init__(self, symbols, start_date='', end_date='', start=0, count=None):
        end = start + count if count is not None else None
        self.symbols = symbols[start:end]
        self.start_date = start_date
        self.end_date = end_date

    def __iter__(self):
        url = 'http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=%s&type=10-&dateb=%s&datea=%s&owner=exclude&count=300'
        for symbol in self.symbols:
            yield (url % (symbol, self.end_date, self.start_date))


class EdgarSpider(CrawlSpider):

    name = 'edgar'
    allowed_domains = ['sec.gov']

    rules = (
        Rule(SgmlLinkExtractor(allow=('/Archives/edgar/data/[^\"]+\-index\.htm',))),
        Rule(SgmlLinkExtractor(allow=('/Archives/edgar/data/[^\"]+/[A-Za-z]+\-\d{8}\.xml','/Archives/edgar/data/[^\"]+/[A-Za-z0-9\-]+_htm\.xml',)), callback='parse_10qk'),
    )

    def __init__(self, **kwargs):
        super(EdgarSpider, self).__init__(**kwargs)

        symbols_arg = kwargs.get('symbols')
        start_date = kwargs.get('startdate', '')
        end_date = kwargs.get('enddate', '')
        limit_arg = kwargs.get('limit', '')

        utils.check_date_arg(start_date, 'startdate')
        utils.check_date_arg(end_date, 'enddate')
        start, count = utils.parse_limit_arg(limit_arg)

        if symbols_arg:
            if os.path.exists(symbols_arg):
                # get symbols from a text file
                symbols = utils.load_symbols(symbols_arg)
            else:
                # inline symbols in command
                symbols = symbols_arg.split(',')
            self.start_urls = URLGenerator(symbols, start_date, end_date, start, count)
            for one_url in self.start_urls:
                print(one_url)
        else:
            self.start_urls = []

    def parse_10qk(self, response):
        '''Parse 10-Q or 10-K XML report.'''
        loader = ReportItemLoader(response=response)
        item = loader.load_item()

        if 'doc_type' in item:
            doc_type = item['doc_type']
            if doc_type in ('10-Q', '10-K'):
                return item

        return None
