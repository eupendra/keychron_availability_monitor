import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess
CSV_FILE = 'k4.csv'


class KeychronSpider(scrapy.Spider):
    custom_settings = {
        'FEEDS': {
            CSV_FILE: {
                'format': 'csv',
                'encoding': 'utf-8'
            },
        },
        'LOG_LEVEL' : 'WARNING'
    }
    name = 'keychron'
    start_urls = [
        'https://keychron.in/product/keychron-k1-wireless-mechanical-keyboard-version-3',
        'https://keychron.in/product/keychron-k2-wireless-mechanical-keyboard',
        'https://keychron.in/product/keychron-k4-wireless-mechanical-keyboard',
        'https://keychron.in/product/keychron-k6-wireless-mechanical-keyboard',
    ]

    def parse(self, response):
        raw_data = response.xpath(
            '//form[@class="variations_form cart"]/@data-product_variations').get()
        data = json.loads(raw_data)
        for item in data:
            version = item["attributes"].get("attribute_pa_version","")
            switch_option = item["attributes"].get("attribute_pa_switch-option","") 
            if not version and not switch_option:
                version = item["attributes"].get("attribute_pa_key")
                
            yield {
                'name': version + switch_option,
                'type': response.url.split('/')[-1],
                'stock': item["is_in_stock"],
                'display_regular_price': item['display_regular_price'],
                'url': response.url
            }


def send_mail():
    import smtplib
    from email.message import EmailMessage
    try:
        msg = EmailMessage()
        EMAIL_USER = os.environ.get('EMAIL_USER')
        EMAIL_PASS = os.environ.get('EMAIL_PWD')
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER
        
        import pandas as pd

        df = pd.read_csv(CSV_FILE)
        msg.set_content(df.to_html(), subtype='html')
        if df["stock"].any():
            msg["Subject"] = "✔ Keychron IN - In STOCK"
            msg.set_content(df[df["stock"]].to_html(), subtype='html')
            with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                smtp.starttls()
                smtp.login(EMAIL_USER, EMAIL_PASS)
                smtp.send_message(msg)

    except:
        print("Error in Sending Mail")

    print("Mail Sent!")


def cleanup():
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)


cleanup()
process = CrawlerProcess()
process.crawl(KeychronSpider)
process.start()
send_mail()
