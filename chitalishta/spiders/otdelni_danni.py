from pathlib import Path

import scrapy
import re

class OtdelniDanniSPider(scrapy.Spider):

    name = "otdelni_danni"
    start_urls = [
        "https://chitalishta.com/index.php?&act=community&do=list&special=1&&sql_which=0"
    ]
    
    def parse(self, response):
        for chitalishte in response.css("tr.odd"):
            chitalishte_detail_link = chitalishte.css('td.pad5 a[href*="do=detail"]::attr(href)').get()
            yield scrapy.Request(response.urljoin(chitalishte_detail_link), callback=self.parse_detail)
        yield from self.process_pagination(response)

    def parse_detail(self, response):
        phones = response.css("tr:nth-child(12) td[colspan='3']::text").get()
        phone_numbers = re.split(r'[,;]', phones)
        phone_numbers = filter(None, phone_numbers)
        formatted_phones = ', '.join(phone_numbers)

        faxes = response.css("tr:nth-child(13) td[colspan='3']::text").get()
        fax = faxes.split()
        formatted_faxes = ', '.join(fax)

        email = response.css("tr:nth-child(14) td[colspan='3']::text").get()
        emails = re.split(r'[\s,;]', email)
        emails = filter(lambda email: re.match(r'\S+@\S+', email), emails)
        formatted_emails = ', '.join(emails)

        yield {
            # "Линк": response.url,
            "Статус": response.css('tr:nth-child(3) td[colspan="3"]::text').get().strip(),
            "Регистрационен №": response.css("tr:nth-child(4) td[colspan='3']::text").get().strip(),
            "Име на читалище": response.css("tr:nth-child(5) td[colspan='3']::text").get().strip(),
            "Област": response.css("tr:nth-child(6) td[colspan='3']::text").get().strip(),
            "Община": response.css("tr:nth-child(7) td[colspan='3']::text").get().strip(),
            "Град/село": response.css("tr:nth-child(8) td[colspan='3']::text").get().strip(),
            "Адрес": clean_text(response.css("tr:nth-child(9) td[colspan='3']::text").get()),
            "Булстат": response.css("tr:nth-child(10) td[colspan='3']::text").get().strip(),
            "Връзка към сайт библиотеки": response.css("tr:nth-child(11) td:nth-child(2) a::attr(href)").get(),
            "Телефон": formatted_phones,
            "Факс": formatted_faxes,
            "E-mail": formatted_emails,
            "Председател": response.css("tr:nth-child(15) td[colspan='3']::text").get().strip(),
            "Секретар": response.css("tr:nth-child(16) td[colspan='3']::text").get().strip()
        }
        return
        yield from self.process_pagination(response)
    
    def process_pagination(self, response):
        pagination_links = response.css('div.pagelist a::attr(href)').getall()
        for link in pagination_links:
            if "sql_which" in link:
                yield scrapy.Request(response.urljoin(link), callback=self.parse)
def clean_text(text):
        return text.strip().replace('\n', ' ')
