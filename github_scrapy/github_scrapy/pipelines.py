# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface


import string
from collections import Counter

import nltk
import psycopg2
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from psycopg2 import extras
from scrapy.exceptions import DropItem

nltk.download('punkt')
nltk.download('stopwords')


class GithubScrapyPipeline:
    def __init__(self, db_settings):
        self.db_settings = db_settings
        self.connection = None
        self.cursor = None

        self.all_words = Counter()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        db_settings = {
            'host': settings.get('DB_HOST', 'localhost'),
            'database': settings.get('DB_DATABASE', 'your_database_name'),
            'user': settings.get('DB_USER', 'your_database_user'),
            'password': settings.get('DB_PASSWORD', 'your_database_password'),
            'port': settings.get('DB_PORT', '5432'),
        }
        return cls(db_settings)

    def open_spider(self, spider):
        self.connection = psycopg2.connect(**self.db_settings)
        self.cursor = self.connection.cursor()
        self.create_table()

    def close_spider(self, spider):
        self.connection.close()

        self.save_word_frequency_to_file('word_frequency.txt')

    def create_table(self):
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS github_profiles (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE,
            full_name VARCHAR(255),
            bio TEXT,
            email VARCHAR(255),
            location VARCHAR(255),
            website VARCHAR(255),
            photo_url VARCHAR(255),
            languages JSONB,
            social_links JSONB
        );
        '''
        self.cursor.execute(create_table_query)
        self.connection.commit()

    '''
        Example
        {'bio': 'Back-End Eng / \r\nAlgo-Quant Trade Dev /\r\nCrawler Expert ',

        'email': 'info.enescan@gmail.com',

        'full_name': 'Enes Can Işık',

        'languages': {'C++', 'Python', 'C#'},

        'location': 'Turkey',

        'photo_url': 'https://avatars.githubusercontent.com/u/53035239?s=64&v=4',

        'social_links': {'linkedin': 'https://www.linkedin.com/in/enes-can-i/',
                          'twitter': 'https://twitter.com/CryptoTylerMoon'},

        'username': 'themiralay',

        'website': 'bulldicator.com'}

        '''

    def process_item(self, item, spider):
        all_text = ' '.join([
            item.get('bio', ''),
            item.get('email', ''),
            item.get('full_name', ''),
            item.get('location', ''),
            str(list(item.get('languages', ''))),
        ])

        self.update_word_count(all_text)

        try:
            insert_query = '''
            INSERT INTO github_profiles (
                username, full_name, bio, email, location,
                website, photo_url, languages, social_links
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (username) DO NOTHING;
            '''
            self.cursor.execute(insert_query, (
                item['username'],
                item['full_name'],
                item['bio'],
                item['email'],
                item['location'],
                item['website'],
                item['photo_url'],
                extras.Json(list(item['languages'])),  # Convert set to list and use Json adapter
                extras.Json(item['social_links'])  # Use Json adapter for the dictionary
            ))
            self.connection.commit()

        except Exception as e:
            self.connection.rollback()

            raise DropItem(f"Failed to save item to PostgreSQL: {str(e)}")

        return item

    def update_word_count(self, text):
        tokens = word_tokenize(text.lower())

        stop_words = set(stopwords.words('english'))
        stemmer = PorterStemmer()
        filtered_tokens = [
            stemmer.stem(word) for word in tokens
            if word not in stop_words and word not in string.punctuation
        ]

        self.all_words.update(filtered_tokens)

    def save_word_frequency_to_file(self, file_path):
        with open(file_path, 'w') as file:
            for word, count in self.all_words.items():
                file.write(f'{word}: {count}\n')
