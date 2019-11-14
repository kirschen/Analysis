#!/usr/bin/env python

#from Analysis.MVA   import *
from               MVA           import *
from TopEFT.Tools.user           import plot_directory
from TopEFT.Tools.user           import mva_directory as output_directory
from TopEFT.Tools.cutInterpreter import *

# Arguments
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--plot_directory',     action='store',             default=None)
argParser.add_argument('--selection',          action='store', type=str,   default="quadlepTWZ-onZ1-noZ2")#-btag1-njet1p")#None)
argParser.add_argument('--label',              action='store', type=str,   default="MVA")
argParser.add_argument('--type',               action='store', type=str,   default="BDT")
argParser.add_argument('--trainingFraction',   action='store', type=float, default=0.5)
argParser.add_argument('--small',              action='store_true')
argParser.add_argument('--overwrite',          action='store_true')
argParser.add_argument('--createPkl',          action='store_true')

args = argParser.parse_args()

args.label += "_%s"%args.type

if args.plot_directory == None:
    args.plot_directory = plot_directory

if args.selection == None:
    selectionString = "(1)"
else:
    selectionString = cutInterpreter.cutString( args.selection )
print selectionString

#define samples
from TopEFT.samples.cmgTuples_Summer16_mAODv2_postProcessed import *

signal  = TWZ
backgrounds = [ TTZtoLLNuNu ]

weightString = "weight"
read_variables = [\
                    "weight/F",
                    "nLeptons_tight_4l/I",
                    "nBTag/I",
                    "met_pt/F",
                    "ht/F",
                    "Z1_mass_4l/F",
                    "Z2_mass_4l/F",
                    ]

calc_variables = [\
                   ]

mva_settings = [ "!V", "!Silent", "Color", "DrawProgressBar", "Transformations=I;D;P;G,D", "AnalysisType=Classification" ]
mva_variables =  [\
#                    "nBTag",
#                    "nJetSelected",
                    "met_pt",
#                    "Z2_mass_4l",
                    "ht",
#                    "jet1_pt",
                 ]

mva = MVA( signal, backgrounds, output_directory, plot_directory, selectionString, label=args.label, fractionTraining=args.trainingFraction, overwrite=args.overwrite, createPkl=args.createPkl, nMax=1000 if args.small else -1 )
mva.prepareSampleSettings( read_variables=read_variables, calc_variables=calc_variables, selectionString=args.selection, weightString=weightString )
mva.prepareSampleSettings( read_variables=read_variables, calc_variables=calc_variables, weightString=weightString )
mva.createSample()
mva.prepareMVASettings( mva_variables=mva_variables, mva_settings=mva_settings, type=args.type )
data, bkgTestTree, sigTestTree, bkgTrainTree, sigTrainTree = mva.runMVA()
#mva.plotEvaluation()

