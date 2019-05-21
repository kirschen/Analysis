#!/usr/bin/env python
import os, sys
import subprocess

redir = "root://hephyse.oeaw.ac.at/"

def getDPMFiles( path ):
    """ get all files in dpm directory
    """
    p = subprocess.Popen( ["dpns-ls %s" %path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    return [ item.rstrip("\n") for item in p.stdout.readlines() ]

def convertToPathList( path, local=False ):
    """ convert path with ending * to list of pathes with all possible files
    """
    dirPath   = "/".join( path.split("/")[:-1] ) + "/"
    fileParts = path.split("/")[-1].split("*") if not path.split("/")[-1] == "*" else [""]

    if len(fileParts) > 1:
        # copy abc*fg*jkl*
        pathList = []
        allFiles = os.listdir(dirPath) if local else getDPMFiles(dirPath)
        for file in allFiles:
            subString = file
            copyFile  = True
            # check if all parts are contained in filename in the right order
            for part in fileParts:
                if not part: continue
                if not part in subString:
                    copyFile = False
                    break
                subString = "".join( subString.split( part )[1:] )
            if copyFile:
                pathList.append( os.path.join( dirPath, file ) )

    elif fileParts[0] == "":
        allFiles = os.listdir(dirPath) if local else getDPMFiles(dirPath)
        pathList  = [ os.path.join( dirPath, file ) for file in allFiles ]
    else:
        pathList  = [ os.path.join( dirPath, fileParts[0] ) ]

    return pathList

def removeDPMFiles( path ):
    """ remove dpm dir or file (only for user dirs)
    """

    if not os.environ["USER"] in path:
        logger.info( "ATTENTION: DO NOT REMOVE FILES FROM OTHERS DPM DIRECTORIES: %s"%path )
        logger.info( "EXITING" )
        sys.exit(1)

    rmPathList = convertToPathList( path )

    for rmPath in rmPathList:
        logger.info( "Removing %s"%rmPath )
        os.system( "/usr/bin/rfrm -rf %s"%rmPath )

def checkDPMDirExists( path ):

    if path.endswith("*"):
        logger.info( "Cannot create directory: %s"%path )
        sys.exit(1)

    checkDir  = getDPMFiles( path )
    dirExists = len( [ item for item in checkDir if not "No such file or directory" in item ] ) > 0
    return dirExists

def makeDPMDir( path ):
    """ create a dpm dir
    """

    if checkDPMDirExists( path ):
        logger.info( "Directory exists: %s"%path )
    else:
        motherPath = "/".join( path.split("/")[:-1] )
        if not checkDPMDirExists( motherPath ):
            makeDPMDir( motherPath )
        logger.info( "Creating directory: %s"%path )
        os.system( "dpns-mkdir %s"%path )        

def isFile( path ):
    """ check if path is a file
    """

    return "." in path.split("/")[-1]

def copyDPMFiles( fromPath, toPath, toLocal=False, fromLocal=False ):
    """ copy files or directories including subdirectories
    """

    fromPathList = convertToPathList( fromPath, local=fromLocal )
    if toLocal:
        if not os.path.isdir( toPath ): os.makedirs( toPath )
    else:
        makeDPMDir( toPath )

    for file in fromPathList:
        if isFile( file ):
            logger.info( "Copying %s to %s"%( file, toPath ) )
            cmd = "xrdcp -r %s%s %s%s"%(redir if not fromLocal else "", file, redir if not toLocal else "", toPath)
            os.system( cmd )
        else:
            subdir          = file.split("/")[-1]
            subFromPath     = os.path.join( file,   "*" )
            subToPath       = os.path.join( toPath, subdir+"/" )
#            logger.info( "Creating subdirectory %s"%subToPath )
            copyDPMFiles( subFromPath, subToPath, toLocal=toLocal, fromLocal=fromLocal )


if __name__ == "__main__":

    # User specific
    from Analysis.Tools.user import dpm_directory

    def get_parser():
        ''' Argument parser for post-processing module.
        '''
        import argparse
        argParser = argparse.ArgumentParser(description = "Argument parser for nanoPostProcessing")
        argParser.add_argument('--ls',        action='store',      type=str,          help="list dpm path content")
        argParser.add_argument('--cp',        action='store',      type=str, nargs=2, help="copy dpm files")
        argParser.add_argument('--fromLocal', action='store_true',                    help="copy from local directory")
        argParser.add_argument('--toLocal',   action='store_true',                    help="copy to local directory")
        argParser.add_argument('--mkdir',     action='store',      type=str,          help="make dpm dir")
        argParser.add_argument('--rm',        action='store',      type=str,          help="dpm path to remove")
        return argParser

    args = get_parser().parse_args()

    # Logging
    if __name__=="__main__":
        import Analysis.Tools.logger as logger
        logger = logger.get_logger("INFO", logFile = None )
        import RootTools.core.logger as logger_rt
        logger_rt = logger_rt.get_logger("INFO", logFile = None )

    else:
        import logging
        logger = logging.getLogger(__name__)


    if args.ls:
        if not args.ls.startswith("/dpm/"):
            args.ls = os.path.join( dpm_directory, args.ls )

        for file in getDPMFiles( args.ls ):
            print file

    elif args.cp:
        fromPath, toPath = args.cp

        if not fromPath.startswith("/dpm/") and not args.fromLocal:
            fromPath = os.path.join( dpm_directory, fromPath )
        if not toPath.startswith("/dpm/") and not args.toLocal:
            toPath = os.path.join( dpm_directory, toPath )

        copyDPMFiles( fromPath, toPath, toLocal=args.toLocal, fromLocal=args.fromLocal )

    elif args.mkdir:
        if not args.mkdir.startswith("/dpm/"):
            args.mkdir = os.path.join( dpm_directory, args.mkdir )

        makeDPMDir( args.mkdir )

    elif args.rm:
        if not args.rm.startswith("/dpm/"):
            args.rm = os.path.join( dpm_directory, args.rm )

        removeDPMFiles( args.rm )

