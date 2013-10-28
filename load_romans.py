import logging
import urllib2
import os
import sqlite3
from BeautifulSoup import BeautifulSoup

# configure logging
log = logging.getLogger('romans_loader')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler()) # write log to stderr

# configure database -- delete it if it exists
DB_FILE = os.path.join(os.getcwd(),'romans.db')
if (os.path.exists(DB_FILE) and open(DB_FILE)):
    os.remove(DB_FILE)

BOOKS = {
    'rom' : 'Romans',
}

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('create table verses (book text, chapter int, verse int, verse_text text)')
conn.commit()
c.close()

def get_html_for_scripture(book, chapter):
    log.debug("about to dl page")
    f = urllib2.urlopen("http://www.youversion.com/bible/chapter/niv/%s/%s" % (book,chapter))
    return BeautifulSoup(f, convertEntities=BeautifulSoup.HTML_ENTITIES)

def process_chapter(book, chapter, soup):
    """"
	Narrows the soup from whole page down to chapter content.
	Gets a list of verse spans
	For each verse, find the verse spans for this verse (usually one span but not always)
	    For each verse span, find children spans of class 'content' and accumulate the contents
    """
    soup = soup.find('div', attrs={"id": "version_primary"})
    log.debug("soup narrowed to %s" % soup)
    verse_spans = soup.findAll('span', 'verse')
    log.debug("found %r verse spans" % len(verse_spans))

    log.debug("evaluating verse spans...")
    verse = 1
    while True:
        verse_spans_for_this_verse = get_verse_spans_for_verse(verse, verse_spans)
        if not verse_spans_for_this_verse:
            log.debug("%s %s ends with verse %s", book, chapter, verse-1)
            break
	log.debug(verse_spans_for_this_verse)
        process_verse_contents(book, chapter, verse, verse_spans_for_this_verse)
        verse += 1

def process_verse_contents(book, chapter, verse_num, verse_spans):
    ess = ""
    for v in verse_spans:
        content_spans = v.findAll('span', 'content')
	for span in content_spans:
            ess += span.string
    log.debug("FINAL: %s", ess.strip())
    c = conn.cursor()
    c.execute("insert into verses values (?, ?, ?, ?)", (BOOKS[book], chapter, verse_num, ess.strip()))
    conn.commit()
    c.close()

def get_verse_spans_for_verse(verse_num, verse_spans):
    """Out of verse_spans, return list of spans for the given verse_num"""
    log.debug('finding verses for verse %d', verse_num)
    verse_spans_for_verse = []
    for vs in verse_spans:
        if vs['class'] == 'verse v%d' % verse_num:
            verse_spans_for_verse.append(vs)
        elif verse_spans_for_verse: # we've moved beyond the relevant verse_spans
            return verse_spans_for_verse
    return verse_spans_for_verse
       

for book_key in BOOKS.keys():
    for chapter in range(1,9):
        soup = get_html_for_scripture(book_key, chapter)
        process_chapter(book_key, chapter, soup)


