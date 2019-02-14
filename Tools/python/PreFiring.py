import ROOT
import os

preFiringPath       = '$CMSSW_BASE/src/Analysis/Tools/data/L1Prefiring/'
SingleMuon_File     = 'UnprefirableEventList_SingleMuon_Run2017BtoF.root'
SingleElectron_File = 'UnprefirableEventList_SingleElectron_Run2017BtoF.root'
JetHT_File          = 'UnprefirableEventList_JetHT_Run2016BtoH.root'
HighEGJet_File      = 'UnprefirableEventList_HighEGJet_Run2017G.root'
LowEGJet_File       = 'UnprefirableEventList_LowEGJet_Run2017G.root'

class PreFiring:

    def __init__( self, PD ):

        if "SingleMuon" in PD:
            self.preFiringFile = os.path.expandvars( os.path.join( preFiringPath, SingleMuon_File ) )
        elif "SingleElectron" in PD:
            self.preFiringFile = os.path.expandvars( os.path.join( preFiringPath, SingleElectron_File ) )
        elif "JetHT" in PD:
            self.preFiringFile = os.path.expandvars( os.path.join( preFiringPath, JetHT_File ) )
        elif "LowEGJet" in PD:
            self.preFiringFile = os.path.expandvars( os.path.join( preFiringPath, LowEGJet_File ) )
        elif "HighEGJet" in PD:
            self.preFiringFile = os.path.expandvars( os.path.join( preFiringPath, HighEGJet_File ) )
        else:
            raise Exception("UnPreFirable Events not known for sample %s"%PD)
            

    def getUnPreFirableEvents( self ):
        # Read Prefiring File
        f = ROOT.TFile.Open( self.preFiringFile )
        return [ ( int(event.event), int(event.run), int(event.lumi) ) for event in f.tree ]

