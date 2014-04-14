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
from chats		import Chats

AB		= AddressBook( '31bb7ba8914766d4ba40d6dfb6113c8b614be442' )
chat_dict	= Chats( '3d0d7e5fb2ce288813306e4d4636395e047a3d28', AddressBook=AB )

# Ideally we want:
#   - a list of people that we can reference by phone or email
#   - a list of people that we can reference by id
#   - a list of chats we can reference by chat_identifier each containing the list of persons
#     involved with that chat

def date( d, format="%Y-%m-%d %H:%M:%S" ):
    return datetime.datetime.fromtimestamp( 978307200 + int(d) ).strftime(format)
    
def chat_list():
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


def show_conversation( chat_identifier ):
    loglevel		= logging.root.getEffectiveLevel()
    logging.root.setLevel( logging.ERROR )
    messages		= chat_dict.get_messages( chat_identifier )
    chat		= chat_dict[chat_identifier]
    width		= 60
    last_name		= None

    print "Found %d messages for chat: %s : %s" % (len(messages), chat_identifier, chat['ROWID'] )
    for m in messages:
        date_str	= date( m['date'] )
        person		= AB[m['id'] if m['is_from_me'] == 0 else "matthew@b"]
        name		= "%s %s" % (person['First'], person['Last']) if person else m['id']
        text		= m['text'].replace("\n", " ")
        more_text	= None

        text		= text.encode('utf-8', 'xmlcharrefreplace')
        name		= name.encode('utf-8', 'xmlcharrefreplace')
        if last_name != name:
            display_name	= name
            date_str		= date( m['date'] )
        else:
            display_name	= ""
            date_str		= ""


        if len(text) > width:
            i		= text[:width].rfind(' ')
            more_text	= text[i:].strip()
            text	= text[:i].strip()

        if more_text or ( last_name != name and last_name is not None ):
            print "%20.20s %19.19s | %-100.60s |" % ( "", "", "" )

        if m['is_from_me'] == 0:
            print "%-20.20s %-19.19s | %-100.60s |" % ( display_name, date_str, text )
        else:
            if more_text:
                print "%-20.20s %-19.19s | %39.39s %-60.60s | %-19.19s  %-20.20s" % ( "", "", "", text, date_str, display_name )
            else:
                print "%-20.20s %-19.19s | %39.39s %60.60s | %-19.19s  %-20.20s" % ( "", "", "", text, date_str, display_name )
        while more_text:
            text		= more_text
            more_text		= None
            if len(text) > 100:
                i		= text[:width].rfind(' ')
                more_text	= text[i:].strip()
                text		= text[:i].strip()
            if m['is_from_me'] == 0:
                print "%20.20s %19.19s | %-100.60s |" % ( "", "", text )
            else:
                print "%20.20s %19.19s | %39.39s %-60.60s |" % ( "", "", "", text )

        last_name	= name
    logging.root.setLevel( loglevel )

try:
    for c_id,chat in chat_dict.iteritems():
        if c_id.startswith('chat'):
            ask		= "Show chat %s with %s: y/N? " % ( c_id, ", ".join([ "%s %s" % (p['First'], p['Last']) if type(p) is dict else p for p in chat['persons']]) )
            aswr		= raw_input(ask)
            if aswr.lower() in ["y"]:
                show_conversation( c_id )
except IOError as exc:
    # This error happens when piping python output to less.
    pass
except Exception as exc:
    raise


