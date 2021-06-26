import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess
import pandas as pd
import smtplib
from email.message import EmailMessage
from urllib.parse import urlparse

CSV_FILE = 'keychronIndia.csv'
# Set Debug to True to get mails even if No stock
DEBUG = False

PRODUCTS_TO_MONITOR = ['k2', 'k1', 'k4']  # partial url match


class KeychronIndiaSpider(scrapy.Spider):
    custom_settings = {
        'FEEDS': {
            CSV_FILE: {
                'format': 'csv',
                'encoding': 'utf-8',
                'overwrite': True
            },
        },
        'LOG_LEVEL': 'DEBUG' if DEBUG else 'WARN'
    }
    name = 'keychron_india'
    start_urls = [
        'https://keychron.in/',
    ]

    def parse(self, response):
        links = response.xpath('//li[contains(@class,"menu-item")]//a[contains(@href,"product")]/@href').getall()
        for link in links:
            if any(p.lower() in link.lower() for p in PRODUCTS_TO_MONITOR):
                yield scrapy.Request(link, callback=self.parse_keyboard)

    def parse_keyboard(self, response):
        # inspect_response(response, self)
        raw_data = response.xpath(
            '//form[@class="variations_form cart"]/@data-product_variations'
        ).get()
        data = json.loads(raw_data)
        for item in data:
            version = item["attributes"].get("attribute_pa_version", "")
            switch_option = item["attributes"].get("attribute_pa_switch-option", "")
            keys = item["attributes"].get("attribute_pa_key", "")
            available = item['is_in_stock']
            if 'rgb' in version:
                version = 'RGB'
            elif 'white' in version:
                version = 'White'

            if 'blue' in switch_option:
                switch_option = '<span style="color:blue">BLUE</span>'
            elif 'red' in switch_option:
                switch_option = '<span style="color:red">RED</span>'
            elif 'brown' in switch_option:
                switch_option = '<span style="color:brown">BROWN</span>'

            yield {
                'Model': urlparse(response.url).path.strip('/').strip('/').split('/')[-1],
                'Version': version,
                'Switch': switch_option,
                'Keys': keys,
                'available': available,
                'display_regular_price': item['display_regular_price'],
                'url': response.url,

            }


def get_body_subject():
    df = pd.read_csv(CSV_FILE)

    if DEBUG:
        subject = "Keychron(IN) - Status" if DEBUG else None
        body = df.to_html(escape=False) if DEBUG else None
    elif df["available"].any():
        subject = "✔ Keychron(IN) - Available"
        body = df[df["available"]].to_html(escape=False)
    return body, subject


def send_mail():
    try:
        body, subject = get_body_subject()
        if not (body and subject) and not DEBUG:
            print("Nothing in stock, exiting...")
            return
        msg = EmailMessage()
        MAIL_USER = 'asdsfsdfs'
        MAIL_PASS = 'asdsfsdfs'
        MAIL_TO = 'asdsfsdfs@gmail.com'

        msg["Subject"] = subject
        msg['From'] = MAIL_USER
        msg['To'] = MAIL_TO
        msg['Cc'] = MAIL_USER

        msg.set_content(body, subtype='html')

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(MAIL_USER, MAIL_PASS)
            smtp.send_message(msg)

    except Exception as e:
        print("Error in Sending Mail\n", str(e))
    else:
        print("Mail Sent!")


def main():
    try:
        process = CrawlerProcess()
        process.crawl(KeychronIndiaSpider)
        process.start()
    except Exception as e:
        print('Unexpected error\n' + str(e))
    else:
        send_mail()


if __name__ == '__main__':
    main()
