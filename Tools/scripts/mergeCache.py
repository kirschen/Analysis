#!/usr/bin/env python
"""
Usage:
mergeCache.py <directory> 
"""

# Standard imports
import os
from Analysis.Tools.MergingDirDB import MergingDirDB

# Parser
from optparse import OptionParser
parser = OptionParser()
parser.add_option('--logLevel',  choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'], default='INFO', help="Log level for logging" )
parser.add_option('--noDelete', dest="noDelete", default=False, action='store_true', help="Delete tmp files?")

(options,args) = parser.parse_args()

# Logging
import Analysis.Tools.logger as logger
logger  = logger.get_logger(options.logLevel, logFile = None)

def test_if_cache( directory ):
    if os.path.isdir( directory ):
        if 'merged' in os.listdir( directory ):
            return True
        if any([ x.startswith('tmp_') for x in os.listdir( directory ) ]):
            return True
    return False

if __name__ == '__main__':
    if not len(args) == 1:
        raise Exception("Only one argument accepted! Instead this was given: %s"%args)

    dirs = []
    if test_if_cache( args[0] ):
        dirs.append( args[0] )
    for (dirpath, dirnames, filenames) in os.walk(args[0]):
        for dirname in dirnames:
            print os.path.join( args[0], dirpath, dirname )
            if test_if_cache( os.path.join( args[0], dirpath, dirname ) ):
                dirs.append( os.path.join( args[0], dirpath, dirname ) )
    
    for dir in dirs:
        logger.info( "Now merging %s", dir )
        db = MergingDirDB( dir )
        db.merge( clear = not options.noDelete )
