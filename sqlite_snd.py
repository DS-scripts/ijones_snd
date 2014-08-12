#!/usr/bin/python

# -*- coding: utf-8 -*-

import sqlite3
import os
import logging

sqlitepath = "~/.ijones/p.sqlite"
program_name    = "IJ SND"
class sqlite_snd:
    def __init__(self,database=sqlitepath):
#        self.logger = logging.getLogger(program_name + ".sqlite")
        self.database = database
#        self.logger.debug("Database in use: %s" % database)
        self.create_connection()

    def create_connection(self):
        if not os.path.isfile(self.database ):
            basedir = os.path.split(self.database)[0]
            if not os.path.isdir(basedir):
                os.makedirs(basedir)
#        self.logger.debug("Creating connection")
        self.conn = sqlite3.connect(self.database)
#        self.logger.info("Database connection established")
        self.create_mastertable()

    def execute(self,sql):
#        self.logger.debug("Executing SQL statement: %s" % sql)
        try:
            self.conn.execute(sql)
            if sql.lstrip().upper().startswith("SELECT"):
                out = self.conn.execute(sql).fetchall()
                self.logger.debug("SQLFetch: %s" % out)
                return out
            self.conn.commit()

        except sqlite3.Error as e:
#            logger.critical("An error occurred: %s" % (e.args[0],))
        except:
#            logger.critical("Unexpected error: %s" % (sys.exc_info(),))

    def create_mastertable(self):
#        self.logger.debug("Checking if main table exists")
        sql="SELECT name FROM sqlite_master WHERE type='table' AND name='SND';"
        if len(self.execute(sql)) == 0:
#            self.logger.debug("Main table do not exists. Creating")
            self.execute('''CREATE TABLE SND
                (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
                PATH            TEXT        NOT NULL,
                MD5             TEXT        NOT NULL,
                SIZE            INTEGER     NOT NULL,
                CTIME           DATE        NOT NULL);''')
            self.logger.debug("Main table created successfully")
        self.execute("CREATE INDEX IF NOT EXISTS idxmd5  on SND (MD5);")
        self.execute("CREATE INDEX IF NOT EXISTS idxsize on SND (SIZE);")
        self.execute("CREATE INDEX IF NOT EXISTS idxpath on SND (PATH);")
#        self.logger.info("Main table and indexes available")
        return
