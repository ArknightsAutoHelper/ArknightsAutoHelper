from bs4 import BeautifulSoup
import requests

html = requests.get(r'https://prts.wiki/w/%E5%90%8E%E5%8B%A4%E6%8A%80%E8%83%BD%E4%B8%80%E8%A7%88', headers={'user-agent': 'Mozilla/5.0'}).content

s = BeautifulSoup(html, 'html.parser')
imgs = s.select('img[alt*="Bskill"]')
imgset = set()

for img in imgs:
    imgset.add('https://prts.wiki' + img['data-src'])

with open('index.txt', 'w', encoding='utf-8') as f:
    for imgurl in imgset:
        f.write(imgurl + '\n')

import os
os.system('wget -i index.txt')
