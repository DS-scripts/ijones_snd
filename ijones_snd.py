#!/usr/bin/python

# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import sqlite3
import logging

from optparse       import OptionParser,OptionGroup
from bcolors        import bcolors
from ProgressBar    import ProgressBar
from cli            import parse
from sqlite_snd     import sqlite_snd

sqlitepath = "~/.ijones/p.sqlite"
program_name    = "IJ SND"
version = "%s 0.1beta" % program_name

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
    return filepath.replace(" ", r"\ ")

def remove_file(filepath, msg=""):
    filepath = fix_filepath(filepath)
    print "#/bin/rm -rf %s # %s" % (filepath, msg)

def ignore_dir(filepath):
    return False

def ignore_file(filepath):
    return False

def exists_in_db(filepath, md5):
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

def destroy(sources, dryrun, sqlobj):
    logger.debug("Sources selected: %s", sources)
    if len(sources) != 0:
        for source in sources:
            logger.info("Seeking through %s", source)
            filelist = get_filelist(source)
            for filepath in filelist:
                msg = ""
                filepath = unicode(filepath)
                filename = unicode(os.path.split(filepath)[1])
                if ignore_dir(filepath):
                    logger.debug("directory for file %s ignored", filepath)
                if ignore_file(filepath):
                    logger.debug("file %s ignored", filepath)
                logger.debug("messing with file: %s", filename)
                md5 = get_md5(filepath)
                logger.debug("MD5 for file %s is %s", filename, md5)
                remove, msg = exists_in_db(filepath, md5)
                if remove:
                    remove_file(filepath, msg)

    if len(sources) == 0:
        logger.info("Seeking through Database")
        sql = "SELECT MD5 FROM SND GROUP BY MD5 HAVING COUNT(MD5)>1"
        sqlout = sqlobj.execute(sql)
        for md5 in sqlout:
            logger.debug("Searching for duplicates with MD5=%s", md5)
            sql = "SELECT PATH,CTIME FROM SND WHERE MD5='%s' ORDER BY CTIME" % md5
            sqlout = sqlobj.execute(sql)
            file_to_keep, ctime_to_keep = sqlout[-1]
            logger.debug("Keeping file='%s', ctime='%s'",
                        file_to_keep, ctime_to_keep)
            for file_to_del, ctime_to_del in sqlout[:-1]:
                logger.debug("Deleting file='%s', ctime='%s'",
                            file_to_del, ctime_to_del)
                remove_file(file_to_del, msg="keeping %s, ctime:%s" %
                            (file_to_keep, ctime_to_keep))


def seek(sources, sqlobj):
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

# -=- Progress Bar (class ProgressBar1) -=---------------------------
        p = ProgressBar(len(filelist))
        p.fill_char = '='
# -=- End Progress Bar 2 ----------------------------------------------
        for filepath in filelist:
            count += 1           # Increment for progress bar count
# -=- Progress Bar (class ProgressBar1) -=---------------------------
            str1 = bcolors.green+"    Seeking in"+bcolors.red+" %s "%source
            str2 = str1+bcolors.green+"............. "+bcolors.yellow
            p.update_time(count)
            sys.stdout.write("\r")
            sys.stdout.write("%s%s" % (str2, p))
#            sys.stdout.flush()
# -=- End Progress Bar -=-------------------------------------------
            filename = os.path.split(filepath)[1]
            update = False
            logger.debug("messing with file: %s" % filename)
            logger.debug("Stating file %s" % filename)
            stat    = os.stat(filepath)
            size    = stat.st_size
            logger.debug("Size: %s b" % size)
            ctime   = int(stat.st_ctime)
            logger.debug("Last metadata changed: %s sec since epoch" % ctime)
            quote = "'"
            if filepath.find("'") >= 0: quote = '"'
            sql = "SELECT CTIME,SIZE FROM SND WHERE PATH=%s%s%s " % (quote,filepath,quote)
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
            sys.stdout.write(bcolors.blue+" MD5")
            md5     = get_md5(filepath)
#            sys.stdout.write("    ")
            sys.stdout.flush()
            logger.debug("MD5 for file %s is %s" % (filename,md5))
            if update:
                sql = "UPDATE SND SET MD5='%s',SIZE='%s',CTIME='%s' WHERE PATH=%s%s%s;" % (md5,size,int(ctime),quote,filepath,quote)
            if not update:
                sql = "INSERT INTO SND (PATH,MD5,SIZE,CTIME) VALUES (%s%s%s,'%s',%s,%s)" % (quote,filepath,quote,md5,size,int(ctime))
            sqlobj.execute(sql)
        print (bcolors.reset+" ")
    print (bcolors.reset+" ")

def wipe(sqlobj):
    logger.info("Wiping database")
    sql = "DELETE FROM SND"
    sqlobj.execute(sql)
    logger.debug("Database wiped clean")
    return

def clear(sources,sqlobj):
    logger.debug("Sources selected: %s" % sources)
    if len(sources) == 0: sources = [""]
    for source in sources:
        sys.stdout.write("\r")
        sys.stdout.write(bcolors.green+"    Clearing ")
        sys.stdout.write(bcolors.red+"%s" % source)
        sys.stdout.write(bcolors.green+" ............. ")
        sys.stdout.flush()
        logger.info("Clearing %s" % source)
        quote = "'"
        if source.find("'") >= 0: quote = '"'
        sql = "SELECT ID,PATH,CTIME,SIZE FROM SND WHERE PATH LIKE %s%s%s" % (quote,source + "%%",quote)
        out = sqlobj.execute(sql)
# -=- Progress Bar (class ProgressBar) -=---------------------------
        count = 0           # Progress Bar counter
        p = ProgressBar(len(out))
        p.fill_char = '='
# -=- End Progress Bar  ----------------------------------------------
        for sqlid,sqlpath,sqlctime,sqlsize in out:
# -=- Progress Bar (class ProgressBar) -=---------------------------
            count+=1           # Increment for progress bar count
            str1 = bcolors.green+"    Clearing "+bcolors.red+" %s "%source
            str2 = str1+bcolors.green+"............. "+bcolors.yellow
            p.update_time(count)
            sys.stdout.write("\r")
            sys.stdout.write("%s%s" % (str2, p))
            sys.stdout.flush()
# -=- End Progress Bar 2 -=-------------------------------------------
            if not os.path.exists(sqlpath):
                logger.debug("File %s not found. Deleting" % sqlpath)
                sqlobj.execute("DELETE FROM SND WHERE ID=%s" % (sqlid,))
                continue
            logger.debug("Stating file %s" % sqlpath)
            stat    = os.stat(sqlpath)
            size    = stat.st_size
            logger.debug("Size: %s b" % size)
            ctime   = int(stat.st_ctime)
            logger.debug("Last metadata changed: %s sec since epoch" % ctime)
            if sqlctime != ctime:
                logger.warn("File %s in the database has different ctime. Deleting db/real -> %s/%s" % (sqlpath,sqlctime,ctime))
                sqlobj.execute("DELETE FROM SND WHERE ID=%s" % (sqlid,))
            if sqlsize != size:
                logger.warn("File %s in the database has different size. Deleting db/real -> %s/%s" % (sqlpath,sqlsize,size))
                sqlobj.execute("DELETE FROM SND WHERE ID=%s" % (sqlid,))
    print

if __name__ == "__main__":
    options,arguments = parse(version)

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
    sqlobj = sqlite_snd(database, program_name)

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

    if options.clear:
        logger.debug("Clear mode active")
        sources = arguments
        # if len(arguments) == 0:
        #     sources = [os.getcwd()]
        logger.info("Sources: %s" % sources)
        clear(sources,sqlobj)
    logger.info("Finish processing")
