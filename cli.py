#!/usr/bin/python

# -*- coding: utf-8 -*-

import sys

from optparse import OptionParser,OptionGroup

def parse(version):
    usage   = "usage: %prog [options] [SOURCE1] [SOURCE2] ..."
    epilogue = "When no source is defined, use ."
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
    dgroup.add_option("-d", "--destroy",
                        action="store_true", dest="destroy",default=False,
                        help="Careful, do not use with quiet options")
    dgroup.add_option("-f", "--file",
                        dest="destroy_filename", default=None, metavar="FILE",
                        help="Redirect destruction commands to FILE")
    sgroup = OptionGroup(parser, "Seek Options",
                                "Safe: These options do not harm your data")

    sgroup.add_option("-s", "--seek",
                        action="store_true", dest="seek",default=False,
                        help="Build/Update database")
    sgroup.add_option("-w", "--wipe",
                        action="store_true", dest="wipe",default=False,
                        help="Wipe clean entire database")
    cgroup = OptionGroup(parser, "Clear Options",)

    cgroup.add_option("-c", "--clear",
                        action="store_true", dest="clear",default=False,
                        help="Clear the database")
    parser.add_option_group(dgroup)
    parser.add_option_group(sgroup)
    parser.add_option_group(cgroup)

    if len(sys.argv[1:]) == 0:
        parser.print_help()
        sys.exit(1)

    # parser.print_help()
    return parser.parse_args()

