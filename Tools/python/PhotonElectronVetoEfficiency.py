import ROOT
import os

from Analysis.Tools.helpers import getObjFromFile
from Analysis.Tools.u_float import u_float

# Logging
import logging
logger = logging.getLogger(__name__)

# UPDATE 2017/2018 WHEN AVAILABLE, for all years the same?
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/EgammaIDRecipesRun2#Cut%20based%20photon%20identification
g_keys = [( "g2016_ScalingFactors_80X_Summer16.root", "Scaling_Factors_CSEV_R9 Inclusive"   ),
          ( "g2016_ScalingFactors_80X_Summer16.root", "Scaling_Factors_HasPix_R9 Inclusive" )]

class PhotonElectronVetoEfficiency:
    def __init__( self ):
        self.dataDir = "$CMSSW_BASE/src/Analysis/Tools/data/photonSFData"
        self.g_sf = [ getObjFromFile(os.path.expandvars(os.path.join(self.dataDir, file)), key) for (file, key) in g_keys ]

        for effMap in self.g_sf: assert effMap

    def getPartialSF( self, effMap, pt, eta ):
        sf  = effMap.GetBinContent( effMap.FindBin(eta, pt) )
        err = effMap.GetBinError(   effMap.FindBin(eta, pt) )
        return u_float(sf, err)

    def mult( self, list ):
        res = list[0]
        for i in list[1:]: res = res*i
        return res

    def getSF( self, pt, eta, sigma=0 ):
        if pt       >= 200: pt  = 199
        if abs(eta) >= 2.5: eta = 2.49 
        sf = self.mult( [ self.getPartialSF( effMap, pt, abs(eta) ) for effMap in self.g_sf ] )

        return (1+sf.sigma*sigma)*sf.val

