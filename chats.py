#!/usr/bin/python

from collections	import OrderedDict as odict
from utils		import sqlite
import logging

log		= logging.getLogger( __name__ )

class Chats( odict ):
    blobs	= ( 'attributedBody', 'properties' )

    def __init__( self, db_name, AddressBook=None ):
        super( Chats, self ).__init__()
        self.AddressBook	= AddressBook
        self.conn		= sqlite.connect( db_name )
        self.c			= self.conn.cursor()
        self._search		= {}

        self.c.execute("""
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

        for row in self.c.fetchall():
            for blob in self.blobs:
                if blob in row:
                    del row[blob]
            key			= row['chat_identifier']
            self[key]		= row

            self.c.execute("""
  SELECT c.chat_identifier, h.*
    FROM handle h
    JOIN chat_handle_join chj
      ON chj.handle_id = h.rowid
    JOIN chat c
      ON c.rowid = chj.chat_id
   GROUP BY h.id,c.chat_identifier
""")
        results			= self.c.fetchall()
        for row in results:
            for blob in ['attributedBody', 'properties']:
                if blob in row:
                    del row[blob]
            p_id		= row['id']
            person		= p_id
            key			= row['chat_identifier']
            chat		= self[key]

            if self.AddressBook is not None:
                person		= self.AddressBook.person_has_chat( p_id, chat )
    
            chat.setdefault('persons', []).append(person)

    def get_messages( self, key ):
        self.c.execute("""
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
""", (key,))
        return self.c.fetchall()

if __name__ == "__main__":
    import json, types
    chat_dict		= Chats( '3d0d7e5fb2ce288813306e4d4636395e047a3d28' )
