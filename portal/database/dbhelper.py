#!/usr/bin/python
#
# Copyright 2004 Thomas Fogwill (tfogwill@users.sourceforge.net)
#
# This file is part of the translate web portal.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA	02111-1307	USA

"""helper code for the translate portal database."""

from translate.portal.database.connection import connectionParams
import pg
import logging
      
def openConnection():
        return pg.DB(user=connectionParams.get('user',None),
            dbname=connectionParams.get('dbname',None),
            passwd=connectionParams.get('passwd',None),
            port=int( connectionParams.get('port','-1')),
            opt=connectionParams.get('opt',None),
            tty=connectionParams.get('tty',None))

def executeQuery(sql):
    """executeQuery(sql) -> execute a SELECT query"""
    logging.debug("Executing query: " + sql)
    pool = ConnectionPool.getInstance()
    try:
        db = pool.getConnection()            
        results = db.query(sql).dictresult()          
    except pg.error,e:
        logging.error(e)
        if db: pool.releaseConnection(db)
        raise
    if db: pool.releaseConnection(db)
    return results
    
def retrieve(cls,criteria={},orderby=[]):
    """retrieve(cls,criteria={},orderby=[]) -> Retrieve a list of 
    objects based on the given criteria (where clause),
    ordered ASC by the specified columns (orderby).
     - criteria can be a dict, or a list of tuples
     - orderby is a list
     - cls is a class
    """    
    if (len(criteria)):
        if isinstance(criteria,dict): criteria = criteria.items()
        conditions = [" AND ".join(["%s LIKE '%s'" % (str(k),v) for k,v in criteria if isinstance(v,str)]),
            " AND ".join(["%s=%s" % (str(k),str(v)) for k,v in criteria if not isinstance(v,str)])
        ]
    whereclause = len(criteria) and " WHERE " + " AND ".join([c for c in conditions if len(c)]) or ""
    orderbyclause = len(orderby) and " ORDER BY " + ",".join(orderby) or ""
    sql = "SELECT * FROM " + cls.TABLE + whereclause + orderbyclause    
    results = executeQuery(sql)
    return [cls(values) for values in results]

def fetchByPK(cls,pk):
    """fetchByPK(cls,pk) -> Fetch and object (by primary key) from the 
    database. The type of object to fetch is indicated by cls
     - cls is a class
    """
    obj = None
    if pk == None: 
        return None
    try:
        sql = 'SELECT * FROM ' + cls.TABLE + ' WHERE ' + cls.ID_COL + ' = ' + str(pk)
        results = executeQuery(sql)
        if len(results) > 0:
            obj = cls(results[0])      
    except pg.error,e:
        logging.error(e)
        raise
    return obj



###############################################################################
# A wrapper to "turn on" callable static (class) methods 
###############################################################################
class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable



###############################################################################
# Database connection pool (singleton)
###############################################################################
class ConnectionPool:
    import threading
    __lock = threading.Lock()
    __instance = None
    
    """A connection pool to manage and cache database connections"""
    def __init__(self):
        #only 1 instance allowed
        if ConnectionPool.__instance:
            raise ConnectionPool.__instance
        self.connections = []
        self.available = []
        ConnectionPool.__instance = self
        
    def getInstance():
        "Get the single instance of the pool"
        if ConnectionPool.__instance == None:
            ConnectionPool.__instance = ConnectionPool()
        return ConnectionPool.__instance
    #make getInstance callable on the class (i.e. static)
    getInstance = Callable(getInstance)
        
    def getConnection(self):
        "Get a connection from the pool"
        ConnectionPool.__lock.acquire()
        self.debugPrint('before get')
        if len(self.available) == 0 and len(self.connections) < connectionParams['maxpoolsize']:
            db = openConnection()
            self.connections.append(db)
            self.available.append(db)
        conn = None
        if self.available: 
            conn = self.available.pop()
        ConnectionPool.__lock.release()
        return conn
        
    def releaseConnection(self, connection):
        "Release a connection back to the pool"
        ConnectionPool.__lock.acquire()
        self.debugPrint('before release')
        if connection in self.connections:
            if len(self.connections) > connectionParams['minpoolsize']:                
                self.connections.remove(connection)
                connection.close()
            else:  
                #only return connections that are still useful to us (i.e. not closed)              
                try:
                    connection.reset()
                    self.available.append(connection) 
                except pg.error,e:
                    logging.error('Could not reset and release connection: ' + e)
        self.debugPrint('after release')
        ConnectionPool.__lock.release()
        
    def debugPrint(self, message):
        logging.debug('ConnectionPool.debug: ' + message)
        logging.debug('connections: %d' % len(self.connections))
        logging.debug('available: %d' % len(self.available))
        out = len(self.connections) - len(self.available)
        logging.debug('out: %d' % out)
        logging.debug('min/max: %s/%s' % (connectionParams['minpoolsize'],connectionParams['maxpoolsize']))

       
###############################################################################
# fin.
############################################################################### 