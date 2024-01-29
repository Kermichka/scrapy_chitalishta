from pathlib import Path

import scrapy
import re
import csv
    
class InformacionniKartiSpider(scrapy.Spider):

    name = "informacionni_karti"
    start_urls = [
        "https://chitalishta.com/index.php?&act=community&do=list&special=1&&sql_which=0"
    ]
    # If you'd like not all the information for faster debugging

    # MAX_PAGES = 2
    # current_page = 1

    def save_to_csv(self, data):
        csv_file = 'examples/informacionni_karti_quoted.csv'
        with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            if csvfile.tell() == 0:
                header = list(data.keys())
                csv_writer.writerow(header)
            csv_writer.writerow(data.values())


    def parse(self, response):
        for chitalishte in response.css("tr.odd"):
            chitalishte_detail_link = chitalishte.css('td.pad5 a[href*="do=detail"]::attr(href)').get()
            yield scrapy.Request(response.urljoin(chitalishte_detail_link), callback=self.parse_detail)
        yield from self.process_pagination(response)

    def parse_detail(self, response):
            information_card_links = response.css('td.bold[colspan="4"] a[href*="do=detail"]::attr(href)').getall()
            for link in information_card_links:
                yield scrapy.Request(response.urljoin(link), callback=self.parse_information_cards)
            yield from self.process_pagination(response)
    

    def parse_information_cards(self, response):
        def format_broi(broi):
            broi = broi.lower()
            if not broi.isnumeric() or broi == "0":
                return ""
            return float(broi)
        
        def format_texts(text):
            if text is None:
                return ""
            text = text.strip()
            text_lower = text.lower()

            # due to special cases "нама"
            if re.search(r'н.ма', text_lower) or "не" in text_lower or text == "-" or text == "0" or text == "o":
                return ""
            text = re.sub(r'[\r\n;\t]', '|', text)


            if text.startswith('-'):
                text = text[1:].lstrip()
            
            # remove - after pipes with and without space
            text = re.sub(r'\|\s*-', '|', text)

            # remove additional pipes with and without space between them

            text = re.sub(r'\|\s*\|', '|', text)
            text = re.sub(r'\|+', '|', text)
            
            return text
       
        h2_text = response.css('table h2::text').get()
        h2_text_numbers = re.findall(r'\d+', h2_text)
        info_karta_za = ''.join(h2_text_numbers)

        phones = format_texts(response.css('input[name="form[phone]"]::attr(value)').get()).replace(',','|')
        formatted_phones = str(re.sub(r'[^0-9/,\|]', '', phones)).replace(',', '|')
        
        email = response.css('input[name="form[email]"]::attr(value)').get()
        emails = re.split(r'\s|[,;]', email)
        emails = filter(lambda email: re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email), emails)
        formatted_emails = '|'.join(emails)

        bulstat = response.css('input[name="form[bulstat]"]::attr(value)').get()
        bulstats = re.split(r'(?<![\/,])\D+', bulstat)
        bulstats = filter(None, bulstats)
        formatted_bulstats = '|'.join(bulstats)

        naimenovanie = response.css('input[name="form[name]"]::attr(value)').get().strip()
        formatted_naimenovanie = naimenovanie.replace('"','')
        
        data = {
            "ИНФОРМАЦИОННА КАРТА ЗА": info_karta_za,
            "Рег. номер": response.css('input[name="form[regid]"]::attr(value)').get().strip(),
            "Наименование": formatted_naimenovanie,
            "Област": response.xpath('//label[contains(text(), "Област")]/following-sibling::input[@type="hidden"]/following-sibling::text()').get().strip(),
            "Община": response.xpath('//label[contains(text(), "Община")]/following-sibling::input[@type="hidden"]/following-sibling::text()').get().strip(),
            "Град/село": response.xpath('//label[contains(text(), "Град/село")]/following-sibling::input[@type="hidden"]/following-sibling::text()').get().strip(),
            "Адрес": format_texts(response.css('input[name="form[address][main]"]::attr(value)').get().strip()),
            "Булстат": formatted_bulstats,
            "Телефон": formatted_phones,
            "Email": formatted_emails,
            "Web страница": response.css('input[name="form[webpage]"]::attr(value)').get(),
            "Председател": response.css('input[name="form[director]"]::attr(value)').get(),
            "Секретар": response.css('input[name="form[secretary]"]::attr(value)').get(),
            "Жители": format_broi(response.css('input[name="form[teritory][person]"]::attr(value)').get()),
            "Посетители": format_broi(response.css('input[name="form[teritory][users]"]::attr(value)').get()),
            "Клон 1": format_texts(response.css('input[name="form[filial][1]"]::attr(value)').get()),
            "Клон 2": format_texts(response.css('input[name="form[filial][2]"]::attr(value)').get()),
            "Брой членове": format_broi(response.css('input[name="form[regusers]"]::attr(value)').get()),
            "Молби за членство": format_broi(response.css('input[name="form[regmolba]"]::attr(value)').get()),
            "Нови членове": format_broi(response.css('input[name="form[regnew]"]::attr(value)').get()),
            "Отказани молби": format_broi(response.css('input[name="form[regrej]"]::attr(value)').get()),
            "Библиотечни дейности": format_texts(response.css('input[name="form[main][biblioid]"]::attr(value)').get()),
            "Участие 'Живи човешки съкровища'": format_texts(response.css('textarea[name="form[main][treasures]"]::text').get()),
            "Регионални листа": format_broi(response.css('input[name="form[main][treasure][regnum]"]::attr(value)').get()),
            "Национални листа": format_broi(response.css('input[name="form[main][treasure][nacnum]"]::attr(value)').get()),
            "Кръжоци, клубове": format_texts(response.css('textarea[name="form[main][activities][clubs]"]::text').get()),
            "Kръжоци, клубове бр.": format_broi(response.css('input[name="form[main][activities][clubsnum]"]::attr(value)').get()),
            "Езикови школи, кръжоци": format_texts(response.css('textarea[name="form[main][activities][lang]"]::text').get()),
            "Езикови, кръжоци бр.": format_broi(response.css('input[name="form[main][activities][langnum]"]::attr(value)').get()),
            "Краезнание": format_texts(response.css('textarea[name="form[main][activities][kraj]"]::text').get()),
            "Краезнание бр.": format_broi(response.css('input[name="form[main][activities][krajnum]"]::attr(value)').get()),
            "Музейни колекции": format_texts(response.css('textarea[name="form[main][activities][museum]"]::text').get()),
            "Музейни колекции бр.": format_broi(response.css('input[name="form[main][activities][museumnum]"]::attr(value)').get()),
            "Фолклорни състави и формации": format_texts(response.css('textarea[name="form[main][ltvorch][folk]"]::text').get()),
            "Фолклорни състави и формации бр.": format_broi(response.css('input[name="form[main][ltvorch][folknum]"]::attr(value)').get().strip()),
            "Театрални състави": format_texts(response.css('textarea[name="form[main][ltvorch][theatre]"]::text').get()),
            "Театрални състави бр.": format_broi(response.css('input[name="form[main][ltvorch][theatrenum]"]::attr(value)').get().strip()),
            "Танцови състави и групи": format_texts(response.css('textarea[name="form[main][ltvorch][dance]"]::text').get()),
            "Танцови състави и групи бр.": format_broi(response.css('input[name="form[main][ltvorch][dancenum]"]::attr(value)').get().strip()),
            "Групи за класически и/или модерен балет": format_texts(response.css('textarea[name="form[main][ltvorch][balley]"]::text').get()),
            "Групи за класически и/или модерен балет бр.": format_broi(response.css('input[name="form[main][ltvorch][balleynum]"]::attr(value)').get().strip()),
            "Вокални групи, хорове и индивидуални изпълнители": format_texts(response.css('textarea[name="form[main][ltvorch][vocal]"]::text').get()),
            "Вокални групи, хорове и индивидуални изпълнители бр.": format_broi(response.css('input[name="form[main][ltvorch][vocalnum]"]::attr(value)').get().strip()),
            "Други": format_texts(response.css('textarea[name="form[main][ltvorch][other]"]::text').get()),
            "Други бр.": format_broi(response.css('input[name="form[main][ltvorch][othernum]"]::attr(value)').get().strip()),
            "Участия празници, фестивали т.н.": format_texts(response.css('textarea[name="form[main][events]"]::text').get()),
            "Участия празници, фестивали т.н. бр.": format_broi(response.css('input[name="form[main][eventsnum]"]::attr(value)').get().strip()),
            "Нови дейности": format_texts(response.css('textarea[name="form[main][newactivities][txt]"]::text').get()),
            "Нови дейности самостоятелно бр.": format_broi(response.css('input[name="form[main][newactivities][mainsum]"]::attr(value)').get().strip()),
            "Нови дейности несамостоятелно бр.": format_broi(response.css('input[name="form[main][newactivities][partnersum]"]::attr(value)').get().strip()),
            "Работа с хора с увреждания, етнически различия и др.": format_texts(response.css('textarea[name="form[main][injury]"]::text').get()),
            "Работа с хора с увреждания, етнически различия и др.  бр.": format_broi(response.css('input[name="form[main][othersum]"]::attr(value)').get().strip()),
            "Други дейности": format_texts(response.css('textarea[name="form[main][other]"]::text').get()),
            "Други дейности бр.": format_broi(response.css('input[name="form[main][ltvorch][vocalnum]"]::attr(value)').get().strip()),
            "Проведени събрания": format_texts(response.css('textarea[name="form[org][meetings]"]::text').get()),
            "Последна регистрация": format_texts(response.css('input[name="form[org][prereg]"]::attr(value)').get()),
            "Материална база": format_texts(response.css('textarea[name="form[org][matbase]"]::text').get()),
            "Субсидирана численост": format_broi(response.css('input[name="form[org][subspeople]"]::attr(value)').get()),
            "Персонал": format_broi(response.css('input[name="form[org][personal][all]"]::attr(value)').get()),
            "Персонал висше": format_broi(response.css('input[name="form[org][personal][hi]"]::attr(value)').get()),
            "Специализирани длъжности": format_broi(response.css('input[name="form[org][personal][spec]"]::attr(value)').get()),
            "Административни длъжности": format_broi(response.css('input[name="form[org][personal][adm]"]::attr(value)').get()),
            "Помощен персонал": format_broi(response.css('input[name="form[org][personal][other]"]::attr(value)').get()),
            "Участие в обучения": format_texts(response.css('textarea[name="form[org][obuchenie]"]::text').get()),
            "Санкции": format_texts(response.css('textarea[name="form[org][sanctions]"]::text').get()),
            "Допълнително": format_texts(response.css('textarea[name="form[remark]"]::text').get())
        }
        self.save_to_csv(data)
        yield from self.process_pagination(response)


    def process_pagination(self, response):
        pagination_links = response.css('div.pagelist a::attr(href)').getall()
        for link in pagination_links:
            if "sql_which" in link:
                yield scrapy.Request(response.urljoin(link), callback=self.parse)

        # If you'd like not all the information for faster debugging
        # if self.current_page < self.MAX_PAGES:
        #     pagination_links = response.css('div.pagelist a::attr(href)').getall()
        #     for link in pagination_links:
        #         if "sql_which" in link:
        #             self.current_page += 1
        #             yield scrapy.Request(response.urljoin(link), callback=self.parse)
        #             break
