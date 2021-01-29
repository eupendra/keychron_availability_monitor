import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess
import pandas as pd

CSV_FILE = 'k4India.csv'
# Set Debug to True to get mails even if No stock
DEBUG = False


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
        'https://keychron.in/product/keychron-k1-wireless-mechanical-keyboard-version-3',
        'https://keychron.in/product/keychron-k2-wireless-mechanical-keyboard',
        'https://keychron.in/product/keychron-k4-wireless-mechanical-keyboard',
        'https://keychron.in/product/keychron-k6-wireless-mechanical-keyboard'
    ]

    def parse(self, response):
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
            yield {
                'name': version + switch_option + keys,
                'available': available,
                'display_regular_price': item['display_regular_price'],
                'url': response.url
            }


def get_body_subject():
    df = pd.read_csv(CSV_FILE)
    if df["available"].any():
        subject = "✔ Keychron(IN) - Available"
        body = df[df["available"]].to_html()
    else:
        subject = "❌ Keychron(IN) - Out of Stock" if DEBUG else None
        body = df.to_html() if DEBUG else None
    return body, subject


def send_mail():
    import smtplib
    from email.message import EmailMessage
    try:
        msg = EmailMessage()
        MAIL_USER = os.environ.get('ZMAIL_FROM_USER')
        MAIL_PASS = os.environ.get('ZMAIL_PWD')
        MAIL_TO = os.environ.get('ZMAIL_TO_USER')
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
