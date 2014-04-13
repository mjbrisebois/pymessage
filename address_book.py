#!/usr/bin/python

from collections	import OrderedDict as odict
from utils		import sqlite
import logging

log		= logging.getLogger( __name__ )

class AddressBook( dict ):

    def __init__( self, db_name ):
        self.conn		= sqlite.connect( db_name )
        self.c			= self.conn.cursor()
        self._ordered_by_first	= []
        self._person_by_id	= {}
        self._search		= odict()

        self.c.execute("""
  SELECT c15Phone, c16Email, p.*
    FROM ABPersonFullTextSearch_content ps
    JOIN ABPerson p
      ON p.rowid = ps.rowid
   ORDER BY First
""")

        for row in self.c.fetchall():
            for blob in ['ExternalRepresentation']:
                if blob in row:
                    del row[blob]
            pid				= int( row['ROWID'] )
            phone_search		= row['c15Phone']
            email_search		= row['c16Email']
            key				= "%s %s" % (phone_search or "", email_search or "")
            self._ordered_by_first.append(pid)
            self._person_by_id[pid]	= row
            self._search[key]		= row

    def search( self, key, limit=None ):
        if type(key) is int:
            return self._person_by_id.get( key )
        people		= []
        for search in self._search.keys():
            if key in search:
                person		= self._search[search]
                people.append(person)

        log.info("limit = %s and len(people) = %d", limit, len(people))
        if limit is None or limit > 1:
            result		= people if limit is None else people[:limit]
        elif people:
            result		= people[0]
        else:
            result		= None

        self[key]		= result
        return result

    def __getitem__( self, key ):
        if key in self:
            r			= super(AddressBook, self).__getitem__( key )
            log.debug("Found %s in self: returning %s", key, type(r))
            return r
        else:
            return self.search( key, limit=1 )
        
if __name__ == "__main__":
    import json, types
    AB		= AddressBook( '31bb7ba8914766d4ba40d6dfb6113c8b614be442' )

    # Tests require that Address Book contains multiple contacts with gmail addresses.
    assert type( AB["gmail.com"] )		is dict
    assert type( AB.search("gmail.com") )	is list
