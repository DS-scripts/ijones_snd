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


# -=-[STDOUT Colors]-=-
class bcolors:
    gray             = '\033[1;30m'
    red              = '\033[1;31m'
    green            = '\033[1;32m'
    yellow           = '\033[1;33m'
    blue             = '\033[1;34m'
    magenta          = '\033[1;35m'
    cyan             = '\033[1;36m'
    white            = '\033[1;37m'
    highlightgreen   = '\033[1;42m'
    highlightblue    = '\033[1;44m'
    highlightmagenta = '\033[1;45m'
    highlightcyan    = '\033[1;46m'
    highlightred     = '\033[1;48m'
    reset            = '\033[0m'

class progressbarClass:
    def __init__(self, finalcount, progresschar=None):
        import sys
        self.finalcount=finalcount
        self.blockcount=0
        #
        # See if caller passed me a character to use on the
        # progress bar (like "*").  If not use the block
        # character that makes it look like a real progress
        # bar.
        #
        if not progresschar: self.block=chr(178)
        else:                self.block=progresschar
        #
        # Get pointer to sys.stdout so I can use the write/flush
        # methods to display the progress bar.
        #
        self.f=sys.stdout
        #
        # If the final count is zero, don't start the progress gauge
        #
        if not self.finalcount : return
#        self.f.write('\n------------------ % Progress -------------------1\n')
#        self.f.write('    1    2    3    4    5    6    7    8    9    0\n')
#        self.f.write('----0----0----0----0----0----0----0----0----0----0\n')
        return

    def progress(self, count):
        #
        # Make sure I don't try to go off the end (e.g. >100%)
        #
        count=min(count, self.finalcount)
        #
        # If finalcount is zero, I'm done
        #
        if self.finalcount:
            percentcomplete=int(round(100*count/self.finalcount))
            if percentcomplete < 1: percentcomplete=1
        else:
            percentcomplete=100

        #print "percentcomplete=",percentcomplete
        blockcount=int(percentcomplete/2)
        #print "blockcount=",blockcount
        if blockcount > self.blockcount:
            for i in range(self.blockcount,blockcount):
                self.f.write(self.block)
                self.f.flush()

        if percentcomplete == 100: self.f.write(bcolors.green+" [Done]\n")
        self.blockcount=blockcount
        return

class ProgressBar1:
    def __init__(self, duration):
        self.duration = duration
        self.prog_bar = '[]'
        self.fill_char = '#'
        self.width = 40
        self.__update_amount(0)

    def animate(self):
        for i in range(self.duration):
            if sys.platform.lower().startswith('win'):
                print self, '\r',
            else:
                print self, chr(27) + '[A'
            self.update_time(i + 1)
        print self

    def update_time(self, elapsed_secs):
        self.__update_amount((elapsed_secs / float(self.duration)) * 100.0)
        self.prog_bar += '  %d/%s' % (elapsed_secs, self.duration)

    def __update_amount(self, new_amount):
        percent_done = int(round((new_amount / 100.0) * 100.0))
        all_full = self.width - 2
        num_hashes = int(round((percent_done / 100.0) * all_full))
        self.prog_bar = '[' + self.fill_char * num_hashes + ' ' * (all_full - num_hashes) + ']'
        pct_place = (len(self.prog_bar) / 2) - len(str(percent_done))
        pct_string = '%d%%' % percent_done
        self.prog_bar = self.prog_bar[0:pct_place] + \
            (pct_string + self.prog_bar[pct_place + len(pct_string):])

    def __str__(self):
        return str(self.prog_bar)


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
    sys.stdout.write("\r")
    sys.stdout.write(bcolors.green+"    Getting file list in ")
    sys.stdout.write(bcolors.red+"%s" % source)
    sys.stdout.write(bcolors.green+" ... ")
    sys.stdout.flush()
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
    sys.stdout.write(bcolors.white+"["+bcolors.blue+"done"+bcolors.white+"]")
    sys.stdout.flush()
    print bcolors.reset
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
    print bcolors.cyan+">>> Seeking Mode "+bcolors.white+"["+bcolors.highlightmagenta+"enabled"+bcolors.reset+bcolors.white+"]"
    for source in sources:
        sys.stdout.write("\r")
        sys.stdout.write(bcolors.green+"    Seeking in ")
        sys.stdout.write(bcolors.red+"%s" % source)
        sys.stdout.write(bcolors.green+" ............. ")
        sys.stdout.flush()

        logger.info("Seeking through %s" % source)
        filelist = get_filelist(source)
        count = 0           # Progress Bar counter

# -=- Progress Bar 1 (class progressbarClass) -=-----------------------
#        pb=progressbarClass(len(filelist),bcolors.yellow+"*")
# -=- End Progress Bar 1 -=--------------------------------------------

# -=- Progress Bar 2 (class ProgressBar1) -=---------------------------
        p = ProgressBar1(len(filelist))
        p.fill_char = '='
# -=- End Progress Bar 2 ----------------------------------------------

        for filepath in filelist:
            count+=1           # Increment for progress bar count
# -=- Progress Bar 1 (class progressbarClass) -=-----------------------
#            pb.progress(count)
# -=- End Progress Bar 1

# -=- Progress Bar 2 (class ProgressBar1) -=---------------------------
            str1 = bcolors.green+"    Seeking in"+bcolors.red+" %s "%source
            str2 = str1+bcolors.green+"............. "+bcolors.yellow
            p.update_time(count)
            sys.stdout.write("\r")
            sys.stdout.write("%s%s" % (str2, p))
            sys.stdout.flush()
# -=- End Progress Bar 2 -=-------------------------------------------
            filename = os.path.split(filepath)[1]
            update = False
            logger.debug("messing with file: %s" % filename)
            logger.debug("Stating file %s" % filename)
            stat    = os.stat(filepath)
            size    = stat.st_size
            logger.debug("Size: %s b" % size)
            ctime   = int(stat.st_ctime)
            logger.debug("Last metadata changed: %s sec since epoch" % ctime)
            sql = "SELECT CTIME,SIZE FROM SND WHERE PATH='%s' " % (filepath,)
            out = sqlobj.execute(sql)
            if len(out) == 1:
                sqlctime,sqlsize = out[0]
                if sqlctime == ctime and sqlsize == size:
                    logger.info("File %s already in the database and seems to be the same (ctime comparison and size) " % (filepath,))
                    continue
                else:
                    if sqlctime != ctime:
                        logger.warn("File %s already in the database and ctime is different db/real -> %s/%s" % (filepath,sqlctime,ctime))
                    if sqlsize != size:
                        logger.warn("File %s already in the database and size is different db/real -> %s/%s" % (filepath,sqlsize,size))
                    update = True
            md5     = get_md5(filepath)
            logger.debug("MD5 for file %s is %s" % (filename,md5))
            if update:
                sql = "UPDATE SND SET MD5='%s',SIZE='%s',CTIME='%s' WHERE PATH='%s';" % (md5,size,int(ctime),filepath)
            if not update:
                sql = "INSERT INTO SND (PATH,MD5,SIZE,CTIME) VALUES ('%s','%s',%s,%s)" % (filepath,md5,size,int(ctime))
            sqlobj.execute(sql)
        print (bcolors.reset+" ")
    print (bcolors.reset+" ")

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
