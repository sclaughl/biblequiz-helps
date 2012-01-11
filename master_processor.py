import os
import logging
import sqlite3
import pystache
import codecs

from chapter_processor import transform_to_dic, make_it_bold

log = logging.getLogger('master_processor')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

DB_FILE = os.path.join(os.getcwd(), 'ephesians.db')

''' Create an html file that consists of a table
    where each row is a verse with the first five words in bold
    and the first unique word combination highlighted. '''

def get_verses():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('select chapter, verse, verse_text from verses')
    return cur.fetchall()

def another_found(phrase, verse, verses_dic):
    return any(v['verse_text'].lower().startswith(phrase.lower()) and 
            v['chapter'] != verse['chapter'] and 
            v['verse'] != verse['verse'] for v in verses_dic['verses'])


def highlight_unique_phrases(verses_dic):
    log.debug('about to highlight unique phrases...')
    for verse in verses_dic['verses']:
        ''' Evaluate verse['verse_text'] like this...
                * take the first word
                * search all other verse['verse_text'] values to see if
                    another one begins with that word
                * if no matches then we are unique so put a span around it
                * otherwise add the next word and seach again  '''
        log.debug('evaluating verse %s' % verse)

        # intialize control variable
        phrase = []
        phrase_words = verse['verse_text'].split()
        phrase.append(phrase_words.pop(0))

        log.debug('checking phrase %s' % phrase)

        # test control variable
        while another_found(' '.join(phrase), verse, verses_dic):
            # in this case the phrase wasn't unique
            # add the next word to the phrase
            log.debug('%s was not a unique phrase' % phrase)
            phrase.append(phrase_words.pop(0))
        else:
            # in this case the phrase was unique
            # put a span around phrase (but inside strong)
            log.debug("%s is unique and needs a span around it" % phrase)


verses = get_verses()
verses_dic = transform_to_dic(verses)
make_it_bold(verses_dic)
highlight_unique_phrases(verses_dic)
template = open('chapter.mustache.html').read()
html = pystache.render(template, verses_dic)
f = codecs.open('artifacts/chapters-html/master.html', encoding='utf-8', mode='w')
f.write(pystache.render(template, verses_dic))
f.close()
