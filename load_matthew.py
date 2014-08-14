import logging
import urllib2
import os
import sqlite3
from bs4 import BeautifulSoup
from bs4.element import NavigableString

# configure logging
log = logging.getLogger('matthew_loader')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler()) # write log to stderr

# configure database -- delete it if it exists
DB_FILE = os.path.join(os.getcwd(),'matthew.db')
if (open(DB_FILE)):
    os.remove(DB_FILE)

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('create table verses (book text, chapter int, verse int, verse_text text)')
conn.commit()
c.close()

def get_soup_for_chapternum(chapter):
    try:
        url = "http://www.biblestudytools.com/matthew/%s.html" % chapter
        headers = {'User-Agent' : 'Mozilla/5.0'}
        req = urllib2.Request(url, None, headers)
        f = urllib2.urlopen(req)
        return BeautifulSoup(f)
    except urllib2.HTTPError, e:
        log.debug(e.fp.read())
        raise e

def process_chapter(chapternum, soup):
    chapter_verses = extract_verses_from_soup(chapternum, soup)
    for idx, cv in enumerate(chapter_verses):
        #log.debug( "MT %s:%s %s" % (chapternum, idx+1, cv))
        c = conn.cursor()
        c.execute("insert into verses values ('matthew', ?, ?, ?)", (chapternum, idx+1, cv))
        conn.commit()
        c.close()

def extract_verses_from_soup(chapternum, soup):
    text_verses = []
    verses = soup.find_all(class_='versetext')
    for verse in verses:
        accumulater = ''
        for child in verse.children:
            if isinstance(child, NavigableString):
                if len(child.strip())>0:
                    accumulater += "%s " % child.strip()
            elif child.get('class') and child['class'][0] == 'WordsOfChrist':
                for con in child.contents:
                    if isinstance(con, NavigableString):
                        if len(con.strip())>0:
                            accumulater += "%s " % con.strip()
        text_verses.append(accumulater.strip())
    return text_verses

for chapternum in range(1,11):
    soup = get_soup_for_chapternum(chapternum)
    process_chapter(chapternum, soup)

