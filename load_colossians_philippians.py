import logging
import urllib2
import os
import sqlite3
from BeautifulSoup import BeautifulSoup

# configure logging
log = logging.getLogger('colossians_loader')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler()) # write log to stderr

# configure database -- delete it if it exists
DB_FILE = os.path.join(os.getcwd(),'colossians_philippians.db')
if (os.path.exists(DB_FILE) and open(DB_FILE)):
    os.remove(DB_FILE)

BOOKS = {
    'col' : 'colossians',
    'phil': 'philippians',
}

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('create table verses (book text, chapter int, verse int, verse_text text)')
conn.commit()
c.close()

def get_html_for_scripture(book, chapter):
    log.debug("about to dl page")
    f = urllib2.urlopen("http://www.youversion.com/bible/chapter/niv84/%s/%s" % (book,chapter))
    return BeautifulSoup(f, convertEntities=BeautifulSoup.HTML_ENTITIES)

def handle_verse(s):
    log.debug("handling %s" % s)
    if hasattr(s, 'name'):
        if s.name == 'br':
            return ""
    return s.strip()

def process_verse(verse):
    log.debug("processing verse %s" % verse)
    verse_no = verse.next.next
    handled_verse = map(handle_verse, verse.contents[1:])
    cleaned = [v for v in handled_verse if v != '']
    verse_text = " ".join(cleaned)
    return verse_no, verse_text
    pass

def process_chapter(book, chapter, soup):
    log.debug("page dl'ed and parsed successfully")
    log.debug("we only care about the div with id='version_primary'")
    soup = soup.find('div', attrs={"id": "version_primary"})
    log.debug("soup narrowed to %s" % soup)
    log.debug("finding spans that mark out verses")
    verse_spans = soup.findAll('span', 'verse')
    log.debug("found %r verse spans" % len(verse_spans))

    log.debug("evaluating verse spans...")
    for verse_span in verse_spans:
        verse_num, verse_text = process_verse(verse_span)
        c = conn.cursor()
        c.execute("insert into verses values (?, ?, ?, ?)", (BOOKS[book], chapter, verse_num, verse_text))
        conn.commit()
        c.close()

for book_key in BOOKS.keys():
    for chapter in range(1,4):
        soup = get_html_for_scripture(book_key, chapter)
        process_chapter(book_key, chapter, soup)


