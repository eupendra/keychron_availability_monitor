import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess
import pandas as pd
import scraper_helper as sh

CSV_FILE = 'k4US.csv'
# Set Debug to True to get mails even if No stock
DEBUG = False
FULL_SIZE_ONLY = True


class KeychronSpider(scrapy.Spider):
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
    name = 'keychron'
    start_urls = [
        # 'https://www.keychron.com/products/keychron-k4-wireless-mechanical-keyboard-version-2',
        # 'https://www.keychron.com/products/keychron-k2-hot-swappable-wireless-mechanical-keyboard',
        # 'https://www.keychron.com/products/keychron-k2-wireless-mechanical-keyboard',
        # 'https://www.keychron.com/products/keychron-k8-tenkeyless-wireless-mechanical-keyboard',
        'https://www.keychron.com/collections/keyboard/products/keychron-k1-wireless-mechanical-keyboard'

    ]

    def parse(self, response):

        data = json.loads(response.xpath(
            '//script[@type="application/ld+json"]/text()').get()
        )

        for var in data['offers']:
            if FULL_SIZE_ONLY:
                if not '104-key' in var['name']:
                    continue
            available = True if 'InStock' in var['availability'] else False
            if not available:
                continue
            item = {
                'name': var['name'],
                'available': available,
                'price': var['price'],
                'url': response.url
            }
            yield item


def get_body_subject():
    try:
        df = pd.read_csv(CSV_FILE)
        if df["available"].any():
            subject = "✔ Keychron(US) - Available"
            body = df[df["available"]].to_html()
        else:
            subject = "❌ Keychron(US) - Out of Stock" if DEBUG else None
            body = df.to_html() if DEBUG else None
    except:
        return None, None

    return body, subject


def send_mail():
    import smtplib
    from email.message import EmailMessage
    try:
        msg = EmailMessage()
        MAIL_USER = 'asdsfsdfs@gmail.com'
        MAIL_PASS = 'asdsfsdfs'
        MAIL_TO = 'asdsfsdfs@gmail.com'
        body, subject = get_body_subject()
        if not (body and subject) and not DEBUG:
            print("Nothing in stock, exiting...")
            return
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
    sh.run_spider(KeychronSpider)
    send_mail()


if __name__ == '__main__':
    main()
