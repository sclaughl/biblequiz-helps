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

def is_useful(tag):
    ''' A tag is useful if it contains useful information, e.g. verse number or
        bible text. An example of non-useful information would be a footnote 
        or an empty p tag.'''
    if tag == u'\n': 
        log.debug("%s is not useful" % tag)
        return False

    return True

def process_tag(tag, accum=''):
    log.debug("processing tag %s; accum is %s" % (tag, accum))

    if type(tag).__name__ == 'NavigableString':
        log.debug("%s is a NavigableString" % tag)
        accum += tag.string.rstrip()
        log.debug("accum is now %s" % accum)
        return accum

    # check to see if this tag contains the verse number
    if tag.find('strong', attrs={'class' : 'verseno'}): 
        log.debug("%s contains the verse number" % tag.strong)
        accum += tag.a.renderContents().rstrip()
        log.debug("accum is now %s" % accum)

        log.debug("got the verse number, now going after the verse text")
        accum += tag.next.nextSibling.rstrip() + ' '
        return accum

    return accum

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
        log.debug( "MT %s:%s %s" % (chapternum, idx+1, cv))

def extract_verses_from_soup(chapternum, soup):
    text_verses = []
    #log.debug("finding spans that mark out verses")
    verses = soup.find_all(class_='versetext')
    #log.debug("found %r verse spans" % len(verses))
    for verse in verses:
        accumulater = ''
        for c in verse.children:
            if (isinstance(c, NavigableString) and len(c.strip())>0 ):
                accumulater += "%s " % c.strip()
        text_verses.append(accumulater.strip())
    return text_verses

                
    #log.debug("evaluating verse spans...")
    #for current, next_verse in zip(verse_spans, verse_spans[1:]):
    #    log.debug("beginning evaluation from verse span %s" % current)
    #    log.debug("initializing accumulater for this verse")
    #    accumulater = ''

    #    #import pdb; pdb.set_trace()
    #    while current != next_verse:
    #        if is_useful(current):
    #            log.debug("%s was deemed useful and will be processed" % current)
    #            accumulater = process_tag(current, accumulater)
    #            
    #        current = current.nextSibling
    #        log.debug("within the current verse span, moving to %s" % current)

    #    log.info(accumulater)
    #    c = conn.cursor()
    #    verse_num = int(accumulater.split()[0])
    #    verse_text = accumulater.lstrip(str(verse_num)).lstrip()
    #    c.execute("insert into verses values ('matthew', ?, ?, ?)", (chapter, verse_num, verse_text))
    #    conn.commit()
    #    c.close()
    #    

    ## we still need to handle the final verse span
    #accumulater = process_tag(verse_spans[-1])
    #log.info(accumulater)
    #c = conn.cursor()
    #verse_num = int(accumulater.split()[0])
    #verse_text = accumulater.lstrip(str(verse_num)).lstrip()
    #c.execute("insert into verses values ('matthew', ?, ?, ?)", (chapter, verse_num, verse_text))
    #conn.commit()
    #c.close()


for chapternum in range(1,11):
    soup = get_soup_for_chapternum(chapternum)
    process_chapter(chapternum, soup)

