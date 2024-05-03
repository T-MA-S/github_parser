# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GithubScrapyItem(scrapy.Item):
    photo_url = scrapy.Field()
    full_name = scrapy.Field()
    username = scrapy.Field()
    bio = scrapy.Field()
    location = scrapy.Field()
    website = scrapy.Field()
    social_links = scrapy.Field()
    email = scrapy.Field()
    languages = scrapy.Field()

