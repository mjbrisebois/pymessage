#!/usr/bin/python

import json
import datetime
import logging

logging.basicConfig(**{
    "level":	logging.DEBUG,
    "datefmt":	'%m-%d %H:%M:%S',
    "format":	'%(asctime)s.%(msecs).03d %(threadName)10.10s %(name)-15.15s %(funcName)-15.15s %(levelname)-8.8s %(message)s',
})
log		= logging.getLogger( __file__ )

from address_book	import AddressBook
from collections	import OrderedDict
from utils		import sqlite

AB		= AddressBook( '31bb7ba8914766d4ba40d6dfb6113c8b614be442' )
conn		= sqlite.connect('3d0d7e5fb2ce288813306e4d4636395e047a3d28')
c		= conn.cursor()

# Ideally we want:
#   - a list of people that we can reference by phone or email
#   - a list of people that we can reference by id
#   - a list of chats we can reference by chat_identifier each containing the list of persons
#     involved with that chat

# chat_dict keys are the chat_identifier
chat_dict	= OrderedDict()


def load_chats():
    global person_dict

    c.execute("""
  SELECT *
    FROM (
           SELECT c.*, m.*, MAX(m.rowid)
             FROM message m
             JOIN chat_message_join cmj
               ON cmj.message_id = m.rowid
             JOIN chat c
               ON c.rowid = cmj.chat_id
            GROUP BY c.chat_identifier
         ) c
   ORDER BY date DESC
""")

    for row in c.fetchall():
        for blob in ['attributedBody', 'properties']:
            if blob in row:
                del row[blob]
        key		= row['chat_identifier']
        chat_dict[key]	= row
    print "Loaded %d chats" % (len(chat_dict),)

    c.execute("""
  SELECT c.chat_identifier, h.*
    FROM handle h
    JOIN chat_handle_join chj
      ON chj.handle_id = h.rowid
    JOIN chat c
      ON c.rowid = chj.chat_id
   GROUP BY h.id,c.chat_identifier
""")
    results		= c.fetchall()
    for row in results:
        for blob in ['attributedBody', 'properties']:
            if blob in row:
                del row[blob]
        key		= row['chat_identifier']
        person		= AB[row['id']]
        if not person:
            person	= row['id']
        else:
            person.setdefault('chats', []).append(chat_dict[key])

        chat_dict[key].setdefault('persons', []).append(person)
    print "Loaded %d handles" % (len(results),)
load_chats()

def date( d, format="%Y-%m-%d %H:%M:%S" ):
    return datetime.datetime.fromtimestamp( 978307200 + int(d) ).strftime(format)
    
def chat_list():
    global chat_dict

    for c_id,chat in chat_dict.iteritems():
        people_str	= " : ".join([p['First'] if type(p) is dict else p for p in chat['persons']])
        date_str	= date(chat['date'])
        text		= chat['text'].strip().replace("\n"," ")
        print "%40.40s : %-25.25s %-20.20s %-100.100s%s" % (chat['chat_identifier'], people_str, date_str, text, "" if len(text) <= 100 else "..." )

def person_chats( p_identifier ):
    person		= AB[p_identifier]
    if person:
        for chat in person.get('chats', []):
            date_str	= date(chat['date'])
            print "%40.40s %-20.20s : %-100.100s" % (chat['chat_identifier'], date_str, chat['text'] )

def get_messages_for_chat( chat_identifier ):
    c.execute("""
  SELECT m.*, h.id
    FROM chat c
    JOIN chat_message_join cmj
      ON cmj.chat_id = c.rowid
    JOIN message m
      ON m.rowid = cmj.message_id
    LEFT JOIN handle h
      ON m.handle_id = h.rowid
   WHERE c.chat_identifier = ?
   ORDER BY m.date ASC
""", (chat_identifier,))
    return c.fetchall()
    

def show_conversation( chat_identifier ):
    loglevel		= logging.root.getEffectiveLevel()
    logging.root.setLevel( logging.ERROR )
    messages		= get_messages_for_chat( chat_identifier )
    chat		= chat_dict[chat_identifier]
    width		= 60

    print "Found %d messages for chat: %s : %s" % (len(messages), chat_identifier, chat['ROWID'] )
    for m in messages:
        date_str	= date(m['date'])
        person		= AB[m['id'] or "matthew@b"]
        name		= "%s %s" % (person['First'], person['Last']) if person else m['id']
        text		= m['text'].replace("\n", " ")
        more_text	= None
        if len(text) > width:
            i		= text[:width].rfind(' ')
            more_text	= text[i:].strip()
            text	= text[:i].strip()
        if m['id']:
            print "%-20.20s %-19.19s | %-100.60s |" % ( name, date_str, text )
        else:
            if more_text:
                print "%-20.20s %-19.19s | %39.39s %-60.60s | %-20.20s" % ( "", date_str, "", text, name )
            else:
                print "%-20.20s %-19.19s | %39.39s %60.60s | %-20.20s" % ( "", date_str, "", text, name )
        while more_text:
            text		= more_text
            more_text		= None
            if len(text) > 100:
                i		= text[:width].rfind(' ')
                more_text	= text[i:].strip()
                text		= text[:i].strip()
            if m['id']:
                print "%20.20s %19.19s | %-100.60s |" % ( "", "", text )
            else:
                print "%20.20s %19.19s | %39.39s %-60.60s |" % ( "", "", "", text )
        print "%20.20s %19.19s | %-100.60s |" % ( "", "", "" )
    logging.root.setLevel( loglevel )
            

for c_id,chat in chat_dict.iteritems():
    if c_id.startswith('chat'):
        ask		= "Show chat %s with %s: y/N? " % ( c_id, ", ".join([ "%s %s" % (p['First'], p['Last']) if type(p) is dict else p for p in chat['persons']]) )
        aswr		= raw_input(ask)
        if aswr.lower() in ["y"]:
            show_conversation( c_id )

