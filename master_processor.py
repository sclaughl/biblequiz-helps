import os
import logging
import sqlite3
import pystache
import codecs
import unicodedata

from string import punctuation, lstrip

log = logging.getLogger('master_processor')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

DB_FILE = os.path.join(os.getcwd(), 'matthew13to21.db')

''' Create an html file that consists of a table
    where each row is a verse with the first five words in bold
    and the first unique word combination highlighted. '''

def get_verses():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('select book, chapter, verse, verse_text from verses')
    return cur.fetchall()

def strip_opening_quotes(s):
    s = lstrip(s)
    s = lstrip(s, '"')
    s = lstrip(s)
    s = lstrip(s, "'")
    s = lstrip(s)
    return s


def transform_to_dic(verses):
    dic = { 'book': 'The Gospel of Matthew', 'verses' : [] }
    for book, chapter, verse, text in verses:
        dic['verses'].append(
            {'book': book, 'chapter' : chapter, 'verse' : verse, 'verse_text' : strip_opening_quotes(text)}
        )
    return dic


def make_it_bold(verses_dic):
    ''' create a strong around first five words of each verse '''
    for verse in verses_dic['verses']:
        verse_text = verse['verse_text']
        verse['first_five'] = verse_text.split()[:5]
        verse['beyond_five'] = verse_text.split()[5:]
        verse['verse_text_modified'] = "<strong>%s</strong> %s" % (' '.join(verse['first_five']), ' '.join(verse['beyond_five']))


def normalize(string):
    exclude = set(punctuation)
    normalized = ''.join(ch for ch in string if ch not in exclude)
    normalized = ''.join(ch for ch in string if not unicodedata.category(ch).startswith('P'))
    normalized = normalized.lower()
    #log.debug('normalized |%s| to |%s|' % (string, normalized))
    return normalized


def another_found(phrase, verse, verses_dic):
    #return any(v['verse_text'].lower().startswith(phrase.lower()) and not
    return any(normalize(v['verse_text']).startswith(normalize(phrase)) and not
            (v['chapter'] == verse['chapter'] and v['verse'] == verse['verse'])
            for v in verses_dic['verses'])


def highlight_unique_phrases(verses_dic):
    log.debug('about to highlight unique phrases...')
    for verse in verses_dic['verses']:
        ''' Evaluate verse['verse_text'] like this...
                * take the first word
                * search all other verse['verse_text'] values to see if
                    another one begins with that word
                * if no matches then we are unique so put a span around it
                * otherwise add the next word and seach again  
            NOTE: we must ignore html, punctuation, and case when comparing '''

        log.debug('evaluating %s %s:%s' % (verse['book'], verse['chapter'], verse['verse']))

        # initialize control variable
        phrase = []
        phrase_words = verse['verse_text'].split()
        phrase.append(phrase_words.pop(0))

        # test control variable
        while another_found(' '.join(phrase), verse, verses_dic):
            # in this case the phrase wasn't unique
            # add the next word to the phrase
            log.debug('|%s| was not a unique phrase' % ' '.join(phrase))
            phrase.append(phrase_words.pop(0))
        else:
            # in this case the phrase was unique
            # put a span around phrase
            # if phrase is <= 5 words then span goes inside strong
            # if phrase is > 5 words then span goes outside strong
            log.debug("|%s| is unique and needs a span around it" % ' '.join(phrase))
            # need to figure out how to use phrase to update verse_text_modified
            log.debug(verse['verse_text_modified'])

            joined = ' '.join(phrase)
            orig = verse['verse_text_modified']
            if len(phrase) <= 5:
                verse['verse_text_modified'] = orig.replace(joined, "<span>%s</span>" % joined, 1)
            else:
                first_five = ' '.join(verse['first_five'])
                unique_remainder = ' '.join(phrase[5:])
                remainder = ' '.join(phrase_words)
                verse['verse_text_modified'] = "<span><strong>%s</strong> %s</span> %s" % (first_five, unique_remainder, remainder)
            log.debug(verse['verse_text_modified'])


if __name__ == "__main__":
    verses = get_verses()
    verses_dic = transform_to_dic(verses)
    make_it_bold(verses_dic)
    highlight_unique_phrases(verses_dic)
    template = open('chapter.mustache.html').read()
    html = pystache.render(template, verses_dic)
    f = codecs.open('artifacts/chapters-html/master.html', encoding='utf-8', mode='w')
    f.write(pystache.render(template, verses_dic))
    log.debug('wrote verses to template -- DONE!')
    f.close()
