import ROOT
import os

from Analysis.Tools.helpers import getObjFromFile
from Analysis.Tools.u_float import u_float

# Logging
import logging
logger = logging.getLogger(__name__)

class PhotonSF:
    def __init__(self, year=2016):

        if year not in [ 2016, 2017, 2018 ]:
            raise Exception("Lepton SF for year %i not known"%year)

        self.year    = year
        self.dataDir = "$CMSSW_BASE/src/Analysis/Tools/data/photonSFData/"

        if year == 2016:
            g_file = 'g2016_LegacyReReco_PhotonCutBasedMedium.root'
            g_key  = "EGamma_SF2D"

        elif year == 2017:
            g_file = 'g2017_PhotonsMedium.root'
            g_key  = "EGamma_SF2D"

        elif year == 2018:
            g_file = 'g2018_PhotonsMedium.root'
            g_key  = "EGamma_SF2D"

        self.g_sf = getObjFromFile( os.path.expandvars( os.path.join( self.dataDir, g_file ) ), g_key )
        assert self.g_sf, "Could not load gamma SF histo %s from file %s."%( g_key, g_file )

        self.g_ptMax = self.g_sf.GetYaxis().GetXmax()
        self.g_ptMin = self.g_sf.GetYaxis().GetXmin()

        self.g_etaMax = self.g_sf.GetXaxis().GetXmax()
        self.g_etaMin = self.g_sf.GetXaxis().GetXmin()

    def getSF(self, pt, eta, sigma=0):
        if eta >= self.g_etaMax:
            logger.warning( "Photon eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.g_etaMin, self.g_etaMax )
            eta = self.g_etaMax-0.01
        if eta <= self.g_etaMin:
            logger.warning( "Photon eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.g_etaMin, self.g_etaMax )
            eta = self.g_etaMin+0.01

        if   pt >= self.g_ptMax: pt = self.g_ptMax - 1
        elif pt <= self.g_ptMin: pt = self.g_ptMin + 1

        val    = self.g_sf.GetBinContent( self.g_sf.FindBin(eta, pt) )
        valErr = self.g_sf.GetBinError(   self.g_sf.FindBin(eta, pt) )

        return val + sigma*valErr

if __name__ == "__main__":

    sigma = 1
    print "2016"
    LSF = PhotonSF(year=2016)
    print LSF.getSF(20, 1, sigma=sigma)
    print LSF.getSF(20, -1, sigma=sigma)
    print LSF.getSF(20, 1, sigma=sigma)
    print LSF.getSF(20, -1, sigma=sigma)

    print LSF.getSF(200, 1, sigma=sigma)
    print LSF.getSF(200, -1, sigma=sigma)
    print LSF.getSF(200, 1, sigma=sigma)
    print LSF.getSF(200, -1, sigma=sigma)

    print LSF.getSF(20, 2.5, sigma=sigma)
    print LSF.getSF(20, -2.5, sigma=sigma)
    print LSF.getSF(20, 2.5, sigma=sigma)
    print LSF.getSF(20, -2.5, sigma=sigma)

    print LSF.getSF(200, 2.5, sigma=sigma)
    print LSF.getSF(200, -2.5, sigma=sigma)
    print LSF.getSF(200, 2.5, sigma=sigma)
    print LSF.getSF(200, -2.5, sigma=sigma)

    print "2017"
    LSF = PhotonSF(year=2017)
    print LSF.getSF(20, 1, sigma=sigma)
    print LSF.getSF(20, -1, sigma=sigma)
    print LSF.getSF(20, 1, sigma=sigma)
    print LSF.getSF(20, -1, sigma=sigma)

    print LSF.getSF(200, 1, sigma=sigma)
    print LSF.getSF(200, -1, sigma=sigma)
    print LSF.getSF(200, 1, sigma=sigma)
    print LSF.getSF(200, -1, sigma=sigma)

    print LSF.getSF(20, 2.5, sigma=sigma)
    print LSF.getSF(20, -2.5, sigma=sigma)
    print LSF.getSF(20, 2.5, sigma=sigma)
    print LSF.getSF(20, -2.5, sigma=sigma)

    print LSF.getSF(200, 2.5, sigma=sigma)
    print LSF.getSF(200, -2.5, sigma=sigma)
    print LSF.getSF(200, 2.5, sigma=sigma)
    print LSF.getSF(200, -2.5, sigma=sigma)

    print "2018"
    LSF = PhotonSF(year=2018)
    print LSF.getSF(20, 1, sigma=sigma)
    print LSF.getSF(20, -1, sigma=sigma)
    print LSF.getSF(20, 1, sigma=sigma)
    print LSF.getSF(20, -1, sigma=sigma)

    print LSF.getSF(200, 1, sigma=sigma)
    print LSF.getSF(200, -1, sigma=sigma)
    print LSF.getSF(200, 1, sigma=sigma)
    print LSF.getSF(200, -1, sigma=sigma)

    print LSF.getSF(20, 2.5, sigma=sigma)
    print LSF.getSF(20, -2.5, sigma=sigma)
    print LSF.getSF(20, 2.5, sigma=sigma)
    print LSF.getSF(20, -2.5, sigma=sigma)

    print LSF.getSF(200, 2.5, sigma=sigma)
    print LSF.getSF(200, -2.5, sigma=sigma)
    print LSF.getSF(200, 2.5, sigma=sigma)
    print LSF.getSF(200, -2.5, sigma=sigma)

