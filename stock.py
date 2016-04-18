# encoding: utf-8
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import csv, re
import telepot
from telepot.delegate import per_chat_id, create_open
import config

def souping(url, decode='utf-8'):
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) ' \
                 'Gecko/20071127 Firefox/2.0.0.11'
    req = Request(url, headers={'User-Agent': user_agent})
    resp = urlopen(req)
    html = resp.read()
    soup = BeautifulSoup(html.decode(decode, 'ignore'), 'html.parser')
    return soup

# 종목코드로 현재 주가 조회하기
def get_price(corp_code):
    try:
        url = "http://m.finance.daum.net/m/item/main.daum?code="+corp_code
        soup = souping(url)
        info = soup.find('div', {'class': 'item_idx_info'})
        
        name = info.h2.a.string
        price = info.find('span', {'class': 'price'}).string
        price_fluc = info.find('span', {'class': 'price_fluc'}).get_text()
        rate_fluc = info.find('span', {'class': 'rate_fluc'}).get_text()
        return (name + " (" + corp_code + ")\n" + price + " " + price_fluc + " " + rate_fluc)

    except Exception as e:
        return ("검색결과가 없습니다. 종목코드를 확인하세요.")
        print(e)

# 기업명으로 종목코드 알아내기
def get_corp_code(text):
    input_corp_name = text
    with open('data.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        corp_code_wrap = []
        for row in reader:
            corp_name = row['기업명']
            corp_code = row['종목코드']
            if corp_name:
                # 기업명과 동일한 종목코드를 발견한다면 현재 주가 조회하기
                if input_corp_name == corp_name.lower():
                    price = get_price(corp_code)
                    return [price]
                elif input_corp_name in corp_name.lower():
                    corp_code_wrap.append(corp_code+" "+corp_name)

    return corp_code_wrap

class Telegram(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(Telegram, self).__init__(seed_tuple, timeout)

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type is 'text':
            chat_id = msg['chat']['id']
            text = msg['text']

            if text == "/start":
                self.sender.sendMessage("안녕하세요. 주식한당 bot입니다.\n종목코드 및 기업명을 입력하세요.")

            elif re.match(r'^\d+$', text):
                stock_price = get_price(text)
                self.sender.sendMessage(stock_price)

            # get string not corp code
            else:
                corp_codes = get_corp_code(text)
                if len(corp_codes) >= 1:
                    self.sender.sendMessage("\n".join(corp_codes))

                else:
                    self.sender.sendMessage("해당 단어를 포함하는 기업명이 없습니다. 다시 입력하세요.")

TOKEN = config.TOKEN

bot = telepot.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(Telegram, timeout=100)),
])
bot.notifyOnMessage(run_forever=True)
