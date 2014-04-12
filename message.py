#!/usr/bin/python

import json
import datetime
import sqlite3		as sql

from collections	import OrderedDict

def db_connect( db ):
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]]	= row[idx]
        return d
    conn		= sql.connect(db)
    conn.row_factory	= dict_factory    
    return conn

conn		= db_connect('3d0d7e5fb2ce288813306e4d4636395e047a3d28')
addr_conn	= db_connect('31bb7ba8914766d4ba40d6dfb6113c8b614be442')
addr_c		= addr_conn.cursor()
c		= conn.cursor()

def exec_print(c, query, limit=None):
    print query
    c.execute(query)

    for row in c.fetchall() if limit is None else range( limit ):
        if limit is not None:
            row	= c.fetchone()
        if not row:
            break
        try:
            for blob in ['attributedBody', 'properties', 'ExternalRepresentation']:
                if blob in row:
                    del row[blob]
            print json.dumps( row, indent=4 )
        except Exception as exc:
            print exc    

def find_user( name=None, phone=None, email=None ):
    """ABPersons contains the person list and ABMultiValue contains the information that has
    multiple values (phone, email...).

    """
    global addr_c, c
    #exec_print(addr_c, "select * from ABPerson where First like '%"+name+"%'")
    exec_print(addr_c, "select * from ABMultiValue where record_id = 127")
    #exec_print(c, "select *, count(*) as message_count from chat where chat_identifier like '%"+name+"%' or chat_identifier like '%"+phone+"%'")

def recent_messages():
    global c
    exec_print(c, "select * from message order by date desc limit 1")

def recent_messages():
    global c
    exec_print(c, "select * from message order by date desc limit 1")

# Ideally we want:
#   - a list of people that we can reference by phone or email
#   - a list of people that we can reference by id
#   - a list of chats we can reference by chat_identifier each containing the list of persons
#     involved with that chat

# person_dict keys are the search strings for phone and email
person_dict	= {}
# person_dict keys are the person id
person_id_dict	= {}
# chat_dict keys are the chat_identifier
chat_dict	= OrderedDict()

def load_persons():
    global person_dict

    addr_c.execute("""
  SELECT c15Phone, c16Email, p.*
    FROM ABPersonFullTextSearch_content ps
    JOIN ABPerson p
      ON p.rowid = ps.rowid
""")

    for row in addr_c.fetchall():
        for blob in ['ExternalRepresentation']:
            if blob in row:
                del row[blob]
        key			= " ".join([ row['c15Phone'] or "", row['c16Email'] or "" ])
        person_dict[key]	= row
        key			= row['ROWID']
        person_id_dict[key]	= row
    print "Loaded %d persons" % (len(person_dict))
load_persons()

def contact( p_id ):
    for key in person_dict.keys():
        if p_id in key:
            return person_dict[key]
    return None

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
        person		= contact(row['id'])
        if not person:
            person	= row['id']
        else:
            p_id	= person['ROWID']
            person_id_dict[p_id].setdefault('chats', []).append(chat_dict[key])
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
    person		= contact(p_identifier)
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
    messages		= get_messages_for_chat( chat_identifier )
    chat		= chat_dict[chat_identifier]
    width		= 60

    print "Found %d messages for chat: %s : %s" % (len(messages), chat_identifier, chat['ROWID'] )
    for m in messages:
        date_str	= date(m['date'])
        person		= contact( m['id'] or "matthew@b" )
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
            

#person_chats( 'curtis' )
#chat_list()
for c_id,chat in chat_dict.iteritems():
    if c_id.startswith('chat'):
        ask		= "Show chat %s with %s: y/N? " % ( c_id, ", ".join([p['First'] if type(p) is dict else p for p in chat['persons']]) )
        aswr		= raw_input(ask)
        if aswr.lower() in ["y"]:
            show_conversation( c_id )

