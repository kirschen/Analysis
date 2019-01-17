import ROOT
import os, math
from Analysis.Tools.u_float import *
from Analysis.Tools.helpers import getObjFromFile

# Logging
import logging
logger = logging.getLogger(__name__)

class PhotonReconstructionEfficiency:
    def __init__(self, year=2016):

        if year not in [ 2016, 2017, 2018 ]:
            raise Exception("Photon Reconstruction Eff for year %i not known"%year)

        self.dataDir = "$CMSSW_BASE/src/Analysis/Tools/data/photonSFData/"
        self.year = year

        if self.year == 2016:
            ## EGamma POG, https://twiki.cern.ch/twiki/bin/viewauth/CMS/EgammaIDRecipesRun2#Cut%20based%20photon%20identification
            g_file = 'g2016_EGM2D_BtoH_GT20GeV_RecoSF_Legacy2016.root'
            g_key  = "EGamma_SF2D"

        elif self.year == 2017:
            # UPDATE WHEN AVAILABLE
            g_file = 'g2016_EGM2D_BtoH_GT20GeV_RecoSF_Legacy2016.root'
            g_key  = "EGamma_SF2D"
            
        elif self.year == 2018:
            # UPDATE WHEN AVAILABLE
            g_file = 'g2016_EGM2D_BtoH_GT20GeV_RecoSF_Legacy2016.root'
            g_key  = "EGamma_SF2D"
            
        self.g_sf  = getObjFromFile( os.path.expandvars( os.path.join( self.dataDir, g_file ) ), g_key )

        assert self.g_sf, "Could not load ele SF histo %s from file %s."%( g_key, g_file )

        self.g_ptMax  = self.g_sf.GetYaxis().GetXmax()
        self.g_ptMin  = self.g_sf.GetYaxis().GetXmin()

        self.g_etaMax = self.g_sf.GetXaxis().GetXmax()
        self.g_etaMin = self.g_sf.GetXaxis().GetXmin()

    def getSF(self, pt, eta, sigma=0):

        if eta >= self.g_etaMax:
            logger.warning( "Supercluster eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.g_etaMin, self.g_etaMax )
            eta = self.g_etaMax - 0.01
        if eta <= self.g_etaMin:
            logger.warning( "Supercluster eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.g_etaMin, self.g_etaMax )
            eta = self.g_etaMin + 0.01

        # this is a bit awkward because of the seperate SFs for low pt electrons
        if   pt >= self.g_ptMax: pt = self.g_ptMax - 1 
        elif pt <  self.g_ptMin: pt = self.g_ptMin + 1

        val    = self.g_sf.GetBinContent( self.g_sf.FindBin(eta, pt) )
        valErr = self.g_sf.GetBinError(   self.g_sf.FindBin(eta, pt) )
            
        return val + sigma*valErr

