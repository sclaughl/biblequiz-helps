import logging
import urllib2
import os
import sqlite3
from BeautifulSoup import BeautifulSoup

# configure logging
log = logging.getLogger('ephesians_loader')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler()) # write log to stderr

# configure database -- delete it if it exists
DB_FILE = os.path.join(os.getcwd(),'ephesians.db')
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

def get_html_for_scripture(chapter):
    log.debug("about to dl page")
    f = urllib2.urlopen("http://www.youversion.com/bible/chapter/niv84/eph/%s" % chapter)
    return BeautifulSoup(f, convertEntities=BeautifulSoup.HTML_ENTITIES)

def process_chapter(chapter, soup):
    log.debug("page dl'ed and parsed successfully")
    log.debug("finding spans that mark out verses")
    verse_spans = soup.findAll('span', 'verse')
    log.debug("found %r verse spans" % len(verse_spans))

    log.debug("evaluating verse spans...")
    for current, next_verse in zip(verse_spans, verse_spans[1:]):
        log.debug("beginning evaluation from verse span %s" % current)
        log.debug("initializing accumulater for this verse")
        accumulater = ''

        #import pdb; pdb.set_trace()
        while current != next_verse:
            if is_useful(current):
                log.debug("%s was deemed useful and will be processed" % current)
                accumulater = process_tag(current, accumulater)
                
            current = current.nextSibling
            log.debug("within the current verse span, moving to %s" % current)

        log.info(accumulater)
        c = conn.cursor()
        verse_num = int(accumulater.split()[0])
        verse_text = accumulater.lstrip(str(verse_num)).lstrip()
        c.execute("insert into verses values ('ephesians', ?, ?, ?)", (chapter, verse_num, verse_text))
        conn.commit()
        c.close()
        

    # we still need to handle the final verse span
    accumulater = process_tag(verse_spans[-1])
    log.info(accumulater)
    c = conn.cursor()
    verse_num = int(accumulater.split()[0])
    verse_text = accumulater.lstrip(str(verse_num)).lstrip()
    c.execute("insert into verses values ('ephesians', ?, ?, ?)", (chapter, verse_num, verse_text))
    conn.commit()
    c.close()

for chapter in range(1,7):
    soup = get_html_for_scripture(chapter)
    process_chapter(chapter, soup)

