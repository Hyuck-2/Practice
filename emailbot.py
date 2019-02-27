import requests
import re
import sqlite3
import time
import random
from bs4 import BeautifulSoup

sql = './email_harvest.sqlite'
email_re = r'[a-zA-Z0-9.-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]*[a-zA-Z]+'
url_re = r'@(https?|ftp)://(-\.)?([^\s/?\.#-]+\.?)+(/[^\s]*)?$@iS'

while True:
    print('Loading data from DB...')
    conn = sqlite3.connect(sql)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS email_harvest(id INTEGER NOT NULL UNIQUE PRIMARY KEY, source CHAR(200) NOT NULL, email CHAR(50) NOT NULL UNIQUE)')
    cur.execute('CREATE TABLE IF NOT EXISTS webpages(id INTEGER NOT NULL UNIQUE PRIMARY KEY, links CHAR(200) NOT NULL UNIQUE, visited INTEGER)')
    source = ''

    cur.execute('SELECT links FROM webpages WHERE visited = 0 ORDER BY id ASC LIMIT 1')
    link = cur.fetchall()
    if link:
        source = link[0][0]
        cur.execute('UPDATE webpages SET visited = 1 WHERE links = \'{}\''.format(source))

    if not source:
        source = input('Enter an url for me to start crawl around from: ')
        cur.execute("INSERT OR IGNORE INTO webpages(links, visited) VALUES(\'{}\', 1)".format(source))

    if not source.startswith('https://'):
        source = 'https://' + source

    cur.close()
    conn.close()

    try:
        print('Connecting to the page...')
        page = requests.get(source)
        content = page.content
        print(content[:50])
    except:
        print('Somehting went wrong...')
        continue

    print('Looking at the webpage...')
    if isinstance(content, bytes):
        content = content.decode()

    print('Sorting out emails and links...')
    soup = BeautifulSoup(content, 'html.parser')
    links = set([x['href'] for x in soup.find_all('a') if x['href'].startswith('https://')])
    emails = re.findall(email_re, content)
    count_email = 0
    count_link = len(links)

    conn = sqlite3.connect(sql)
    cur = conn.cursor()

    for email in emails:
        cur.execute("INSERT OR IGNORE INTO email_harvest(source, email) VALUES(\'{}\', \'{}\')".format(source[:200], email.lower()))
        count_email += 1

    for link in links:
        cur.execute("INSERT OR IGNORE INTO webpages(links, visited) VALUES(\'{}\', 0)".format(link))

    conn.commit()
    cur.close()
    conn.close()

    print('='*20)
    print('{} emails, {} links have been collected from {}...'.format(count_email, count_link, source))
    print('='*20)
    rand = random.randrange(20, 30)
    time.sleep(rand)
