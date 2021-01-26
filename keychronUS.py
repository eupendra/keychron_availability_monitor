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
        }
    }
    name='keychron'
    start_urls = [
        'https://www.keychron.com/products/keychron-k4-wireless-mechanical-keyboard-version-2']

    def parse(self, response):

        data = json.loads(response.xpath(
            '//script[@type="application/ld+json"]/text()')[0].get())
        for var in data['offers']:
            yield {
                'name': var['name'],
                'availability': var['availability'].strip('http://schema.org/'),
                'price': var['price']
            }


def send_mail():
    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASS = os.environ.get('EMAIL_PWD')
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER
    msg["Subject"] = "Keychron Availability Status"
    # Message body
    import pandas as pd         
    df = pd.read_csv(CSV_FILE) 
    msg.set_content(df.to_html(), subtype='html')
    
    with smtplib.SMTP("smtp.gmail.com",587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)



def cleanup():
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    
cleanup()
process = CrawlerProcess()
process.crawl(KeychronSpider)
process.start()
send_mail()
