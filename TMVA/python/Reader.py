'''TMVA wrapper
'''

# standard imports
import os, sys
import ROOT
ROOT.gROOT.SetBatch(True)
import random
import ctypes
import copy

from array                 import array
from root_numpy            import ROOT_VERSION
from operator              import attrgetter

# Analysis.TMVA
from Analysis.TMVA.helpers  import *
from Analysis.TMVA.defaults import default_methods, default_factory_settings

# RootTools
from RootTools.core.standard import *

# Logging
if __name__=="__main__":
    import Analysis.Tools.logger as logger
    logger = logger.get_logger("INFO", logFile = None )
else:
    import logging
    logger = logging.getLogger(__name__)

# example methods

class Reader:
    def __init__( self, mva_variables, weight_directory, label ):#output_directory, label):

        self.read_variables      = []
        self.mva_variables       = mva_variables
        self.label               = label

        self.weight_directory    = weight_directory

        # Need to keep track of sequence!
        self.mva_variable_names  = mva_variables.keys() 
        self.mva_variable_names  .sort() 

#        self.output_directory    = os.path.join( output_directory, self.label )
#        self.mvaOutFile          = os.path.join( self.output_directory, self.label + "_MVAOutput.root" )
#        self.mvaWeightDir        = "weights" #os.path.join( self.output_directory, "weights" )
        self.output_directory    = os.path.join( self.weight_directory, self.label )
        self.mvaOutFile          = os.path.join( self.weight_directory, self.label + "_MVAOutput.root" )
        self.mvaWeightDir        = self.weight_directory

    def addMethod( self, method ):
        # for MLP add HiddenLayer option that is of the form N,x,y,z,... where N is the number of variables and x,y,z the "layers" key
        if method["type"]==ROOT.TMVA.Types.kMLP:
            #method["options"].append( "HiddenLayers=%s" % ",".join( map( str, [len( self.mva_variable_names )] + method["layers"] )) )
             method["options"].append( "HiddenLayers=%s" % method["layers"]  )
        if not hasattr( self, "methods" ):
            self.methods = []

        self.methods.append( method )

    def evaluate(self, names=None, **kwargs):
        # all methods we evaluate for

        ret_scalar = False
        if type(names)==type(""):
            names = [ names ]
            ret_scalar = True
        elif names is None:
            names = [ method['name'] for method in self.methods ]
        else:
            names = names 

        if not hasattr( self, "reader" ):

            import ctypes
            p_c_float  = ctypes.c_float  * 1
            p_c_double = ctypes.c_double * 1

            defaultObs = { "F":p_c_float(0.), "D":p_c_double(0.), "I":ctypes.c_int(0) }

            self.reader      = ROOT.TMVA.Reader()
            for key in self.mva_variable_names:
                self.reader.AddVariable(key, defaultObs["F"])

            for method in self.methods:
                self.reader.BookMVA( method["name"], os.path.join( self.mvaWeightDir, "TMVAClassification_%s.weights.xml" % method["name"] ) )

            self.var_proxies = {}
            self.mva_reader_inputs = ROOT.std.vector('float')()

        self.mva_reader_inputs.clear()
        for var in self.mva_variable_names:
            self.mva_reader_inputs.push_back( kwargs[var] )
        if ret_scalar: 
            return self.reader.EvaluateMVA( self.mva_reader_inputs, names[0])
        else:
            return [ self.reader.EvaluateMVA( self.mva_reader_inputs, name_) for name_ in names ]

