 #!/usr/bin/python

 # -*- coding: utf-8 -*-

import sys
from bcolors        import bcolors
from ProgressBar    import ProgressBar


class usermsg:
    def __init__(self):
        pass

    def pbarinit(self, maxnum):
# initialize progress bar
        self.p = ProgressBar(maxnum)
        self.p.fill_char = '='
        self.count = 0

    def seekmode(self):
        print bcolors.cyan+">>> Seeking Mode "+bcolors.white+"["+bcolors.highlightmagenta+"enabled"+bcolors.reset+bcolors.white+"]"

    def seeking(self, source):
        sys.stdout.write("\r")
        sys.stdout.write(bcolors.green+"    Seeking in ")
        sys.stdout.write(bcolors.red+"%s" % source)
        sys.stdout.write(bcolors.green+" ............. ")
        sys.stdout.flush()

    def seekupdate(self, source):
        self.count += 1
        str1 = bcolors.green+"    Seeking in"+bcolors.red+" %s "%source
        str2 = str1+bcolors.green+"............. "+bcolors.yellow
        self.p.update_time(self.count)

        sys.stdout.write("\r")
        sys.stdout.write("%s%s" % (str2, self.p))
        sys.stdout.flush()

    def md5(self):
        sys.stdout.write(bcolors.blue+" MD5")

    def flist(self, source):
        sys.stdout.write("\r")
        sys.stdout.write(bcolors.green+"    Getting file list in ")
        sys.stdout.write(bcolors.red+"%s" % source)
        sys.stdout.write(bcolors.green+" ... ")
        sys.stdout.flush()

    def wiping(self):
        sys.stdout.write("\r")
        sys.stdout.write(bcolors.green+"    Wiping database")
        sys.stdout.write(bcolors.green+" ............. ")
        sys.stdout.flush()

    def cleaning(self):
        sys.stdout.write("\r")
        sys.stdout.write(bcolors.green+"    Cleaning database")
        sys.stdout.write(bcolors.green+" ............. ")
        sys.stdout.flush()

    def done(self):
        sys.stdout.write(bcolors.white+"["+bcolors.blue+"done"+bcolors.white+"]")
        sys.stdout.flush()
        print bcolors.reset

    def reset(self):
        print bcolors.reset
