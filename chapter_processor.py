import os
import logging
import sqlite3
import pystache
import codecs

log = logging.getLogger('chapter_processor')
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

DB_FILE = os.path.join(os.getcwd(), 'romans.db')

''' Given a chapter of romans, create an html file that consists of a table
    where each row is a verse with the first five words in bold. '''

def get_verses(chapter):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('select book, chapter, verse, verse_text from verses where chapter = ?', (chapter,))
    return cur.fetchall()


def transform_to_dic(verses):
    dic = { 'verses' : [] }
    for book, chapter, verse, text in verses:
        dic['verses'].append(
            {'book': book, 'chapter' : chapter, 'verse' : verse, 'verse_text' : text}
        )
    return dic


def make_it_bold(verses_dic):
    ''' create a strong around first five words of each verse '''
    for verse in verses_dic['verses']:
        verse['verse_text_modified'] = "<strong>%s</strong> %s" % (' '.join(verse['verse_text'].split()[:5]), ' '.join(verse['verse_text'].split()[5:]))


def create_html_page_for_chapter(chapter):
    ''' read the verses out of the database '''
    verses = get_verses(chapter)
    verses_dic = transform_to_dic(verses)

    make_it_bold(verses_dic)
 
    template = open('chapter.mustache.html').read()
    html = pystache.render(template, verses_dic)
    if not os.path.exists('artifacts/chapters-html'):
        os.makedirs('artifacts/chapters-html')
    f = codecs.open('artifacts/chapters-html/romans%s.html' % chapter, encoding='utf-8', mode='w')
    f.write(pystache.render(template, verses_dic))
    f.close()

if __name__ == "__main__":
    for chapter in range(1,9):
        create_html_page_for_chapter(chapter)
