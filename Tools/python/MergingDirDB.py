''' Implementation of a directory based results DB for CMS analyses
    Supports merging and does not destroy afs volumes.

'''

# Standard imports
import os
import pickle
import uuid

# Logger
import logging
logger = logging.getLogger(__name__)

# Try to read a result from a single file. 
def read_key_from_file( f, key ):
    if os.path.exists( f ):
        try:
            tmp = pickle.load(file(f))
            if tmp.has_key( key ):
                return tmp[ key ]
        except IOError:
            pass # Nothing found
    return None

# Try to read a result from a single file. 
def read_dict_from_file( f ):
    if os.path.exists(f):
        try:
            return pickle.load(file(f))
        except IOError:
            pass # Something wrong 
    return None

class MergingDirDB:
    def __init__( self, directory ):
        '''
        Will create the directory if it doesn't exist 
        '''
        # work directory
        self.directory = directory
        # dictinary where the instance stores its unique 
        self.data_dict  = {}

        # create directory
        if not os.path.isdir( self.directory ):
            os.makedirs( self.directory ) 

        # make a unique pkl file to write for this process
        self.unique_tmp_file = 'tmp_'+str(uuid.uuid4()) 

## Let's try WITHOUT done/tmp for the moment
#    def flush( self ):
#        # Rename the current tmp_file to 'done_...' and make a new tmp file
#        tmp_file  = os.path.join( self.directory, self.unique_tmp_file )
#        
#        done_file = os.path.join( self.directory, 'done_' + self.unique_tmp_file.lstrip('tmp_') )
#
#        if os.path.exists( tmp_file ):
#            os.rename( tmp_file, done_file )
#        
#        self.unique_tmp_file = 'tmp_'+str(uuid.uuid4()) 

    def add(self, key, data, overwrite=False):

        if not overwrite:
            if self.read_from_all_files(key) is not None:
                logger.warning( "Already found key %r . Do not store data.", key )
                return data

        # Add data to private dictinary and store the file
        self.data_dict[key] = data 
        pickle.dump( self.data_dict, file( os.path.join( self.directory, self.unique_tmp_file), 'w' ) )
        logger.debug( "Added key %r to file %s", key, os.path.join( self.directory, self.unique_tmp_file) )
        return data

    def get(self, key):
        ''' Get all entries in the database matching the provided key.
        '''

        if self.data_dict.has_key( key ): return self.data_dict[ key ]
        # if we don't alread have the key, load it from all files and remember it in case you're asked again:
        return self.read_from_all_files( key )

    def contains(self, key):
        ''' Get all entries in the database matching the provided key.
        '''
        return self.get(key) is not None

    # Here we collect all files from other processes. 
    def tmp_files( self ):
        return [ os.path.join( self.directory, f ) for f in os.listdir(self.directory) if f.startswith( 'tmp_') ]

    # Here we find  all files that are already merged.
    # Merging should happen while NO jobs are running (because they are reading the merge file) 
    def merged_file( self ):
        merged_file = os.path.join( self.directory, 'merged' )
        return merged_file

    def read_from_all_files( self, key ):
        '''Read from all files that could possibly contain
           the result and return the newest according to unix modification time'''
        results = [] 
        for f in self.tmp_files() + [self.merged_file()]:
            result =  read_key_from_file( f, key )
            if result is not None:
                results.append( [ result, os.path.getmtime( f ) ] )
        if len(results)==0: return None
        results.sort( key = lambda r:r[1] )
        if len(results)>1:
            logger.warning( "Found %i results with different timestamp for key %r . Return newest.", len(results), key )
        return results[-1][0]
        
    def merge( self, clear = False):
        if os.path.exists( self.merged_file() ):
            result = read_dict_from_file( self.merged_file() )
        else:
            result = {}
        # result will be 'none' if loading from an existing merge file failed.
        # That will result in an error below which is what we want, because in that case we don't want to write anything
        results = []
        for f in self.tmp_files():
            results.append( (f, os.path.getmtime( f )) )
        results.sort( key = lambda r:r[1] )
        for _result, _ in results:
            result.update( pickle.load(file(_result)) )
        pickle.dump(result, file(self.merged_file(), 'w'))

        
        if clear and os.path.exists( self.merged_file() ):
            try:
                pickle.load(file( self.merged_file()))
            except:
                logger.error( "Could not load merged pickle file %s. Will not delete tmp files.",  self.merged_file() )
                return
            logger.info( "Merged pkl file %s seems OK, will delete tmp files.", self.merged_file() )
            for f in self.tmp_files():
                os.remove( f )

if __name__ == "__main__":
    import Analysis.Tools.logger as logger
    logger    = logger.get_logger( "DEBUG", logFile = None)

    import ROOT

    dirDB = MergingDirDB("./test2")

    #dirDB.add('x',1)
    #dirDB.add('y',2, overwrite=True)
    #dirDB.merge()
