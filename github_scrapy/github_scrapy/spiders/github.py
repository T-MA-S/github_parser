import json
import random

import scrapy
from scrapy import Request

from github_scrapy.items import GithubScrapyItem
from github_scrapy.settings import PROXY_LIST, GITHUB_TOKENS


class GithubSpider(scrapy.Spider):
    name = "github"
    allowed_domains = ["github.com"]
    start_urls = ["https://github.com"]

    def start_requests(self):
        countries = ['Russia', 'Turkey', 'UAE', 'Armenia', 'Belarus',
                     'Uzbekistan', 'Kazakhstan', 'Kyrgyzstan', 'Moldova']
        languages = ['JavaScript', 'HTML', 'Python', 'Java', 'C++', 'PHP', 'C#', 'CSS', 'C', 'Jupyter+Notebook']
        sort_by = ['followers', 'joined', 'repositories']
        orders = ['desc', 'asc']

        for country in countries:
            for language in languages:
                for p in range(1, 101):
                    for sort in sort_by:
                        for order in orders:
                            request = Request(f'https://github.com/search?q=language%3A{language}+'
                                            f'location%3A{country}&type=users&p={p}&s{sort}=&o={order}')

                            if PROXY_LIST:
                                request.meta['proxy'] = random.choice(PROXY_LIST)
                            yield request

    def parse(self, response, item=None):
        try:
            if 'item' in response.meta:
                item = response.meta['item']

                try:
                    result = json.loads(response.text)

                    email = result[0]['commit']['author']['email']
                except:
                    email = ''

                item['email'] = email
                yield item
            else:
                result = json.loads(response.text)['payload']['results']
                for person in result:
                    request = Request(f"https://github.com/{person['display_login']}", callback=self.parse)
                    if PROXY_LIST:
                        request.meta['proxy'] = random.choice(PROXY_LIST)
                    yield request

        except Exception:
            photo_url = response.css('img.avatar-user::attr(src)').get()
            photo_url = photo_url.split('?')[0] if photo_url else None

            full_name = response.css('span.p-name::text').get()
            full_name = full_name.strip() if full_name else None

            username = response.css('span.p-nickname::text').get()
            username = username.strip() if username else None

            bio = response.css('div.p-note::attr(data-bio-text)').get()

            location = response.css('span.p-label::text').get()
            location = location.strip() if location else None

            website = response.css('li[itemprop="url"] a.Link--primary::text').get()

            languages = set(response.css('span[itemprop="programmingLanguage"]::text').getall())

            social_links = {}
            for i, social_block in enumerate(response.css('li[itemprop="social"]')):
                platform = social_block.css('svg.octicon title::text').get()
                platform = platform.lower() if platform else f'url{i}'
                link = social_block.css('a.Link--primary::attr(href)').get()
                if platform and link:
                    social_links[platform] = link

            repository_href = response.css('a.Link.mr-1.text-bold.wb-break-word::attr(href)').get()
            repository_href = repository_href if repository_href else None

            if not repository_href:
                repository_href = response.css('a.Link.text-bold.flex-auto::attr(href)').get()
                repository_href = repository_href if repository_href else None

            new_item = GithubScrapyItem()
            new_item['photo_url'] = photo_url
            new_item['full_name'] = full_name
            new_item['username'] = username
            new_item['bio'] = bio
            new_item['location'] = location
            new_item['website'] = website
            new_item['languages'] = languages
            new_item['social_links'] = social_links
            new_item['email'] = ''

            if not repository_href:
                yield new_item

            request = Request(f'https://api.github.com/repos{repository_href}/commits',
                              callback=self.parse,
                              headers={'Authorization': f'token {random.choice(GITHUB_TOKENS)}'},
                              meta={'item': new_item})

            if PROXY_LIST:
                request.meta['proxy'] = random.choice(PROXY_LIST)

            yield request
