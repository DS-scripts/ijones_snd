#!/usr/bin/python

# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import sqlite3
import logging

from optparse import OptionParser,OptionGroup

sqlitepath = "~/.ijones/p.sqlite"
program_name    = "IJ SND"

def parse():
    usage   = "usage: %prog [options] [SOURCE1] [SOURCE2] ..."
    epilogue = "When no source is defined, use ."
    version = "%s 0.1beta" % program_name
    parser = OptionParser(usage = usage, version = version, epilog = epilogue)
    parser.set_defaults(dryrun=True)

    parser.add_option("-v", "--verbose",
                              action="count", dest="verbose", default=0,
                                                help="Increase verbosity")
    parser.add_option("-q", "--quiet",
                              action="store_const", dest="verbose",const = -1,
                                                help="Ultra quiet mode")
    parser.add_option("-r", "--relative",
                              action="store_true", dest="relative",default=False,
                                                help="Use relative Filepath instead of Full Qualified File Name")
    parser.add_option("--database",
                              action="store_const", dest="rdb",
                                                metavar="DATABASE",
                                                help="force usage of external database")
    dgroup = OptionGroup(parser, "Destroy Options",
                                "Caution: use these options at your own risk. "
                                "Compare source to database. "
                                "When no source is informed, '.' is used as default")
    dgroup.add_option("--live-destruction",
                              action="store_false", dest="dryrun",
                                                help="Use with destroy mode to perform a FULL DESTRUCTION OF ALL DATA, duplicated data anyways. [NOT IMPLEMENTED]")
    dgroup.add_option("--dry-run",
                              action="store_true", dest="dryrun",
                                                help="Use with destroy mode to perform a simulation [Default]")
    dgroup.add_option("-d","--destroy",
                              action="store_true", dest="destroy",default=False,
                                                help="Careful, do not use with quiet options")
    sgroup = OptionGroup(parser, "Seek Options",
                                "Safe: These options do not harm your data")

    sgroup.add_option("-s","--seek",
                              action="store_true", dest="seek",default=False,
                                                help="Build/Update database")
    sgroup.add_option("-w","--wipe",
                              action="store_true", dest="wipe",default=False,
                                                help="Wipe clean entire database")
    parser.add_option_group(dgroup)
    parser.add_option_group(sgroup)

    if len(sys.argv[1:]) == 0:
        parser.print_help()
        sys.exit(1)

    # parser.print_help()
    return parser.parse_args()

class sqlite_snd:
    def __init__(self,database=sqlitepath):
        self.logger = logging.getLogger(program_name + ".sqlite")
        self.database = database
        self.logger.debug("Database in use: %s" % database)
        self.create_connection()

    def create_connection(self):
        if not os.path.isfile(self.database ):
            basedir = os.path.split(self.database)[0]
            if not os.path.isdir(basedir):
                os.makedirs(basedir)
        self.logger.debug("Creating connection")
        self.conn = sqlite3.connect(self.database)
        self.logger.info("Database connection established")
        self.create_mastertable()

    def execute(self,sql):
        self.logger.debug("Executing SQL statement: %s" % sql)
        try:
            self.conn.execute(sql)
            if sql.lstrip().upper().startswith("SELECT"):
                out = self.conn.execute(sql).fetchall()
                self.logger.debug("SQLFetch: %s" % out)
                return out
            self.conn.commit()

        except sqlite3.Error as e:
            logger.critical("An error occurred: %s" % (e.args[0],))
        except:
            logger.critical("Unexpected error: %s" % (sys.exc_info(),))

    def create_mastertable(self):
        self.logger.debug("Checking if main table exists")
        sql="SELECT name FROM sqlite_master WHERE type='table' AND name='SND';"
        if len(self.execute(sql)) == 0:
            self.logger.debug("Main table do not exists. Creating")
            self.execute('''CREATE TABLE SND
                (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
                PATH            TEXT        NOT NULL,
                MD5             TEXT        NOT NULL,
                SIZE            INTEGER     NOT NULL,
                CTIME           DATE        NOT NULL);''')
            self.logger.debug("Main table created successfully")
        self.execute("CREATE INDEX IF NOT EXISTS idxmd5  on SND (MD5);")
        self.execute("CREATE INDEX IF NOT EXISTS idxsize on SND (SIZE);")
        self.logger.info("Main table and indexes available")
        return

def get_md5(filepath):
    logger.debug("md5summing %s" % filepath)
    stdout = subprocess.Popen(['md5sum',filepath],stdout = subprocess.PIPE).communicate()[0].strip()
    logger.debug("got md5digest: %s" % stdout)
    stdoutsplit = stdout.split()
    if len(stdoutsplit) < 2:
        logger.error("Failed to get md5 for file %s" % filepath)
        return '0'
    else:
        return stdoutsplit[0]

def get_filelist(source):
    filelist = []
    for r,d,f in os.walk(source):
        logger.debug("Walking into: %s" % r)
        if options.relative:
            logger.debug("Relative mode selected")
            r = os.path.relpath(r)
        if not options.relative:
            logger.debug("Absolute mode selected")
            r = os.path.abspath(r)
        logger.debug("Root defined as: %s" % r)
        for filename in f:
            filepath = os.path.join(r,filename)
            logger.info("Using filepath: %s" % filepath)
            if os.path.islink(filepath):
                logger.warning("%s is link. Not following" % filepath)
                continue
            filelist.append(filepath)
    return filelist

def fix_filepath(filepath):
    return filepath.replace(" ","\ ")

def remove_file(filepath,msg = ""):
    filepath = fix_filepath(filepath)
    print "#/bin/rm -rf %s # %s" % (filepath,msg)

def ignore_dir(filepath):
    return False

def ignore_file(filepath):
    return False


def exists_in_db(filepath,md5):
    sql = "SELECT PATH FROM SND WHERE MD5='%s' " % (md5,)
    sqlout = sqlobj.execute(sql)
    if len(sqlout) == 0:
        return (False,"")
    for sqloutentry in sqlout:
        databasefilepath = unicode(sqloutentry[0])
        logger.debug("databasefilepath = %s" % (databasefilepath.__repr__(),))
        logger.debug("        filepath = %s" % (filepath.__repr__(),))
        logger.debug("filepath == databasefilepath: %s" % (filepath == databasefilepath,))
        if filepath == databasefilepath:
            logger.debug("File %s found in the database and is the same. skiping" % filepath)
            return (False,"")
    logger.debug("File %s found in the database as %s. removing from source" % (filepath,databasefilepath))
    return (True,"File found in DB as %s" %(databasefilepath,))

def destroy(sources,dryrun,sqlobj):
    logger.debug("Sources selected: %s" % sources)
    if len(sources) != 0:
        for source in sources:
            logger.info("Seeking through %s" % source)
            filelist = get_filelist(source)
            for filepath in filelist:
                msg = ""
                filepath = unicode(filepath)
                filename = unicode(os.path.split(filepath)[1])
                if ignore_dir(filepath):
                    logger.debug("directory for file %s ignored" % (filepath,))
                if ignore_file(filepath):
                    logger.debug("file %s ignored" % (filepath,))
                logger.debug("messing with file: %s" % filename)
                md5     = get_md5(filepath)
                logger.debug("MD5 for file %s is %s" % (filename,md5))
                remove,msg = exists_in_db(filepath,md5)
                if remove:
                    remove_file(filepath,msg)
    pass

def seek(sources,sqlobj):
    logger.debug("Sources selected: %s" % sources)
    for source in sources:
        logger.info("Seeking through %s" % source)
        filelist = get_filelist(source)
        for filepath in filelist:
            filename = os.path.split(filepath)[1]
            update = False
            logger.debug("messing with file: %s" % filename)
            logger.debug("Stating file %s" % filename)
            stat    = os.stat(filepath)
            size    = stat.st_size
            logger.debug("Size: %s b" % size)
            ctime   = stat.st_ctime
            logger.debug("Last metadata changed: %s sec since epoch" % ctime)
            sql = "SELECT CTIME,SIZE FROM SND WHERE PATH='%s' " % (filepath,)
            out = sqlobj.execute(sql)
            if len(out) == 1:
                sqlctime,sqlsize = out[0]
                if sqlctime == ctime and sqlsize == size:
                    logger.info("File %s already in the database and seems to be the same (ctime comparison) " % (filepath,))
                    continue
                else:
                    logger.warn("File %s already in the database and is different. updating" % (filepath,))
                    update = True
            md5     = get_md5(filepath)
            logger.debug("MD5 for file %s is %s" % (filename,md5))
            if update:
                sql = "UPDATE SND SET MD5='%s',SIZE='%s',CTIME='%s' WHERE PATH='%s';" % (md5,size,int(ctime),filepath)
            if not update:
                sql = "INSERT INTO SND (PATH,MD5,SIZE,CTIME) VALUES ('%s','%s',%s,%s)" % (filepath,md5,size,int(ctime))
            sqlobj.execute(sql)

def wipe(sqlobj):
    logger.info("Wiping database")
    sql = "DELETE FROM SND"
    sqlobj.execute(sql)
    logger.debug("Database wiped clean")
    return

if __name__ == "__main__":
    options,arguments = parse()

    ### LOG DEF ####################################################################
    loglvl = 40 - options.verbose*10
    if loglvl <= 0: loglvl = 1
    logger = logging.getLogger(program_name)
    logger.setLevel(loglvl)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    ch.setLevel(loglvl)
    logger.addHandler(ch)
    ################################################################################

    logger.debug("optparse options: %s" % options)
    logger.debug("optparse arguments: %s" % arguments)


    database = os.path.expanduser(sqlitepath)
    if options.rdb != None and options.destroy and not options.seek:
        database = options.rdb
        logger.info("User defined database : %s" % database)
        if not os.path.isfile(database):
            database = os.path.expanduser(sqlitepath)
            logger.warning("User defined database not found. Falling back to default: %s" % database)
    logger.debug("DataBase file: %s" % database)
    sqlobj = sqlite_snd(database)

    if options.wipe:
        logger.debug("Wipe mode")
        wipe(sqlobj)

    if options.seek:
        logger.debug("Seek mode active")
        sources = arguments
        if len(arguments) == 0:
            sources = [os.getcwd()]
        logger.info("Sources: %s" % sources)
        seek(sources,sqlobj)

    if options.destroy:
        sources = arguments
        if len(arguments) == 0:
            logger.info("Destroying database duplicates")
        if len(arguments) != 0:
            logger.info("Sources: %s" % sources)
        logger.debug("Destroy mode active")
        destroy(sources,options.dryrun,sqlobj)

    logger.info("Finish processing")
