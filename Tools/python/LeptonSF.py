import ROOT
import os
from math import sqrt

from Analysis.Tools.helpers import getObjFromFile
from Analysis.Tools.u_float import u_float

# 2016 Lumi Ratios
lumiRatio2016_BCDEF = 19.717640795 / 35.863818448
lumiRatio2016_GH    = 16.146177653 / 35.863818448


keys_mu2016_BCDEF = { "medium":[( "muon2016_RunBCDEF_SF_ID.root",  "NUM_MediumID_DEN_genTracks_eta_pt"   ),
                                ( "muon2016_RunBCDEF_SF_ISO.root", "NUM_TightRelIso_DEN_MediumID_eta_pt" )],
                      "tight": [( "muon2016_RunBCDEF_SF_ID.root",  "NUM_TightID_DEN_genTracks_eta_pt"   ),
                                ( "muon2016_RunBCDEF_SF_ISO.root", "NUM_TightRelIso_DEN_TightIDandIPCut_eta_pt" )]
                    }

keys_mu2016_GH    = { "medium":[( "muon2016_RunGH_SF_ID.root",     "NUM_MediumID_DEN_genTracks_eta_pt"   ),
                                ( "muon2016_RunGH_SF_ISO.root",    "NUM_TightRelIso_DEN_MediumID_eta_pt" )],
                      "tight": [( "muon2016_RunGH_SF_ID.root",     "NUM_TightID_DEN_genTracks_eta_pt"   ),
                                ( "muon2016_RunGH_SF_ISO.root",    "NUM_TightRelIso_DEN_TightIDandIPCut_eta_pt" )]
                    }

keys_ele2016      = { "medium":[( "e2016_LegacyReReco_ElectronMedium.root", "EGamma_SF2D" )],
                      "tight": [( "e2016_LegacyReReco_ElectronTight.root", "EGamma_SF2D" )],
                    }

keys_mu2017       = { "medium":[( "muon2017_RunBCDEF_SF_ID.root",  "NUM_MediumID_DEN_genTracks_pt_abseta"   ),
                                ( "muon2017_RunBCDEF_SF_ISO.root", "NUM_TightRelIso_DEN_MediumID_pt_abseta" )],
                      "tight": [( "muon2017_RunBCDEF_SF_ID.root",  "NUM_TightID_DEN_genTracks_pt_abseta"   ),
                                ( "muon2017_RunBCDEF_SF_ISO.root", "NUM_TightRelIso_DEN_TightIDandIPCut_pt_abseta" )]
                    }

keys_ele2017      = { "medium":[( "e2017_ElectronMediumCutBased.root", "EGamma_SF2D" )],
                      "tight": [( "e2017_ElectronTight.root", "EGamma_SF2D" )]
                    }

keys_mu2018       = { "medium":[( "mu2018_RunABCD_SF_ID.root",  "NUM_MediumPromptID_DEN_TrackerMuons_pt_abseta"   ),
                                ( "mu2018_RunABCD_SF_ISO.root", "NUM_TightRelIso_DEN_MediumID_pt_abseta" )],
                      "tight": [( "mu2018_RunABCD_SF_ID.root",  "NUM_TightID_DEN_TrackerMuons_pt_abseta"   ),
                                ( "mu2018_RunABCD_SF_ISO.root", "NUM_TightRelIso_DEN_TightIDandIPCut_pt_abseta" )]
                    }


keys_ele2018      = { "medium":[( "e2018_ElectronMedium.root", "EGamma_SF2D" )],
                      "tight": [( "e2018_ElectronTight.root", "EGamma_SF2D" )]
                    }


class LeptonSF:

    def __init__(self, year=2016, ID=None):

        if year not in [ 2016, 2017, 2018 ]:
            raise Exception("Lepton SF for year %i not known"%year)

        self.dataDir = "$CMSSW_BASE/src/Analysis/Tools/data/leptonSFData"
        self.year    = year

        if year == 2016:

            if not ID in keys_mu2016_BCDEF.keys():
                raise Exception("Don't know ID %s"%ID)

            if not ID in keys_mu2016_GH.keys():
                raise Exception("Don't know ID %s"%ID)

            if not ID in keys_ele2016.keys():
                raise Exception("Don't know ID %s"%ID)

            self.mu_BCDEF = [ getObjFromFile(os.path.expandvars(os.path.join(self.dataDir, file)), key) for (file, key) in keys_mu2016_BCDEF[ID] ]
            self.mu_GH    = [ getObjFromFile(os.path.expandvars(os.path.join(self.dataDir, file)), key) for (file, key) in keys_mu2016_GH[ID]    ]
            self.ele      = [ getObjFromFile(os.path.expandvars(os.path.join(self.dataDir, file)), key) for (file, key) in keys_ele2016[ID]      ]

            for effMap in self.mu_BCDEF + self.mu_GH + self.ele: assert effMap

        elif year == 2017:

            if not ID in keys_mu2017.keys():
                raise Exception("Don't know ID %s"%ID)

            if not ID in keys_ele2017.keys():
                raise Exception("Don't know ID %s"%ID)

            self.mu       = [ getObjFromFile(os.path.expandvars(os.path.join(self.dataDir, file)), key) for (file, key) in keys_mu2017[ID]       ]
            self.ele      = [ getObjFromFile(os.path.expandvars(os.path.join(self.dataDir, file)), key) for (file, key) in keys_ele2017[ID]      ]

            for effMap in self.mu + self.ele: assert effMap

        elif year == 2018:

            if not ID in keys_mu2018.keys():
                raise Exception("Don't know ID %s"%ID)

            if not ID in keys_ele2018.keys():
                raise Exception("Don't know ID %s"%ID)

            self.mu       = [ getObjFromFile(os.path.expandvars(os.path.join(self.dataDir, file)), key) for (file, key) in keys_mu2018[ID]       ]
            self.ele      = [ getObjFromFile(os.path.expandvars(os.path.join(self.dataDir, file)), key) for (file, key) in keys_ele2018[ID]      ]

            for effMap in self.mu + self.ele: assert effMap

    def getPartialSF( self, effMap, pt, eta, reversed=False ):
        x = eta if not reversed else pt
        y = pt  if not reversed else eta
        sf  = effMap.GetBinContent( effMap.FindBin(x, y) )
        err = effMap.GetBinError(   effMap.FindBin(x, y) )
        return u_float(sf, err)

    def mult( self, list ):
        res = list[0]
        for i in list[1:]: res = res*i
        return res

    def getSF(self, pdgId, pt, eta, sigma=0):

        if abs(pdgId) not in [11,13]:
            raise Exception("Lepton SF for PdgId %i not known"%pdgId)

        if self.year == 2016 and abs(pdgId) == 13:
            if   pt  >=  120: pt  =   119
            if   pt  <=   20: pt  =    21
            if   eta >=  2.4: eta =  2.39 
            elif eta <= -2.4: eta = -2.39 

            sf_BCDEF = self.mult( [self.getPartialSF(effMap, pt, eta) for effMap in self.mu_BCDEF] )
            sf_GH    = self.mult( [self.getPartialSF(effMap, pt, eta) for effMap in self.mu_GH] )
            sf       = (sf_BCDEF.val*lumiRatio2016_BCDEF) + (sf_GH.val*lumiRatio2016_GH) # Scale SF by lumiRatio
            sigma    = sqrt( (sf_BCDEF.sigma*lumiRatio2016_BCDEF)**2 + (sf_GH.sigma*lumiRatio2016_GH)**2 ) # Scale SF by lumiRatio
#            sigma    = 0.03 # Recommendation for Moriond17
            sf       = u_float(sf, sigma)

        else:
            if abs(pdgId) == 13:
                absEta = abs(eta)
                if pt     >= 120: pt     =  119
                if pt     <=  20: pt     =   21
                if absEta >= 2.4: absEta = 2.39 

                sf = self.mult( [ self.getPartialSF( effMap, pt, absEta, reversed=True ) for effMap in self.mu ] )

            elif abs(pdgId) == 11:
                if   pt  >=  500: pt  =   499
                if   pt  <=   10: pt  =    11
                if   eta >=  2.5: eta =  2.49 
                elif eta <= -2.5: eta = -2.49 

                sf = self.mult( [ self.getPartialSF( effMap, pt, eta ) for effMap in self.ele ] )

        return (1+sf.sigma*sigma)*sf.val


if __name__ == "__main__":

    sigma = 0
    print "2016, medium"
    LSF = LeptonSF(year=2016, ID="medium")
    print LSF.getSF(11, 20, 1, sigma=sigma)
    print LSF.getSF(11, 20, -1, sigma=sigma)
    print LSF.getSF(13, 20, 1, sigma=sigma)
    print LSF.getSF(13, 20, -1, sigma=sigma)

    print LSF.getSF(11, 200, 1, sigma=sigma)
    print LSF.getSF(11, 200, -1, sigma=sigma)
    print LSF.getSF(13, 200, 1, sigma=sigma)
    print LSF.getSF(13, 200, -1, sigma=sigma)

    print LSF.getSF(11, 20, 2.5, sigma=sigma)
    print LSF.getSF(11, 20, -2.5, sigma=sigma)
    print LSF.getSF(13, 20, 2.5, sigma=sigma)
    print LSF.getSF(13, 20, -2.5, sigma=sigma)

    print LSF.getSF(11, 200, 2.5, sigma=sigma)
    print LSF.getSF(11, 200, -2.5, sigma=sigma)
    print LSF.getSF(13, 200, 2.5, sigma=sigma)
    print LSF.getSF(13, 200, -2.5, sigma=sigma)

    print "2016, tight"
    LSF = LeptonSF(year=2016, ID="tight")
    print LSF.getSF(11, 20, 1, sigma=sigma)
    print LSF.getSF(11, 20, -1, sigma=sigma)
    print LSF.getSF(13, 20, 1, sigma=sigma)
    print LSF.getSF(13, 20, -1, sigma=sigma)

    print LSF.getSF(11, 200, 1, sigma=sigma)
    print LSF.getSF(11, 200, -1, sigma=sigma)
    print LSF.getSF(13, 200, 1, sigma=sigma)
    print LSF.getSF(13, 200, -1, sigma=sigma)

    print LSF.getSF(11, 20, 2.5, sigma=sigma)
    print LSF.getSF(11, 20, -2.5, sigma=sigma)
    print LSF.getSF(13, 20, 2.5, sigma=sigma)
    print LSF.getSF(13, 20, -2.5, sigma=sigma)

    print LSF.getSF(11, 200, 2.5, sigma=sigma)
    print LSF.getSF(11, 200, -2.5, sigma=sigma)
    print LSF.getSF(13, 200, 2.5, sigma=sigma)
    print LSF.getSF(13, 200, -2.5, sigma=sigma)

    print "2017, medium"
    LSF = LeptonSF(year=2017, ID="medium")
    print LSF.getSF(11, 20, 1, sigma=sigma)
    print LSF.getSF(11, 20, -1, sigma=sigma)
    print LSF.getSF(13, 20, 1, sigma=sigma)
    print LSF.getSF(13, 20, -1, sigma=sigma)

    print LSF.getSF(11, 200, 1, sigma=sigma)
    print LSF.getSF(11, 200, -1, sigma=sigma)
    print LSF.getSF(13, 200, 1, sigma=sigma)
    print LSF.getSF(13, 200, -1, sigma=sigma)

    print LSF.getSF(11, 20, 2.5, sigma=sigma)
    print LSF.getSF(11, 20, -2.5, sigma=sigma)
    print LSF.getSF(13, 20, 2.5, sigma=sigma)
    print LSF.getSF(13, 20, -2.5, sigma=sigma)

    print LSF.getSF(11, 200, 2.5, sigma=sigma)
    print LSF.getSF(11, 200, -2.5, sigma=sigma)
    print LSF.getSF(13, 200, 2.5, sigma=sigma)
    print LSF.getSF(13, 200, -2.5, sigma=sigma)

    print "2017, tight"
    LSF = LeptonSF(year=2017, ID="tight")
    print LSF.getSF(11, 20, 1, sigma=sigma)
    print LSF.getSF(11, 20, -1, sigma=sigma)
    print LSF.getSF(13, 20, 1, sigma=sigma)
    print LSF.getSF(13, 20, -1, sigma=sigma)

    print LSF.getSF(11, 200, 1, sigma=sigma)
    print LSF.getSF(11, 200, -1, sigma=sigma)
    print LSF.getSF(13, 200, 1, sigma=sigma)
    print LSF.getSF(13, 200, -1, sigma=sigma)

    print LSF.getSF(11, 20, 2.5, sigma=sigma)
    print LSF.getSF(11, 20, -2.5, sigma=sigma)
    print LSF.getSF(13, 20, 2.5, sigma=sigma)
    print LSF.getSF(13, 20, -2.5, sigma=sigma)

    print LSF.getSF(11, 200, 2.5, sigma=sigma)
    print LSF.getSF(11, 200, -2.5, sigma=sigma)
    print LSF.getSF(13, 200, 2.5, sigma=sigma)
    print LSF.getSF(13, 200, -2.5, sigma=sigma)

    print "2018, medium"
    LSF = LeptonSF(year=2018, ID="medium")
    print LSF.getSF(11, 20, 1, sigma=sigma)
    print LSF.getSF(11, 20, -1, sigma=sigma)
    print LSF.getSF(13, 20, 1, sigma=sigma)
    print LSF.getSF(13, 20, -1, sigma=sigma)

    print LSF.getSF(11, 200, 1, sigma=sigma)
    print LSF.getSF(11, 200, -1, sigma=sigma)
    print LSF.getSF(13, 200, 1, sigma=sigma)
    print LSF.getSF(13, 200, -1, sigma=sigma)

    print LSF.getSF(11, 20, 2.5, sigma=sigma)
    print LSF.getSF(11, 20, -2.5, sigma=sigma)
    print LSF.getSF(13, 20, 2.5, sigma=sigma)
    print LSF.getSF(13, 20, -2.5, sigma=sigma)

    print LSF.getSF(11, 200, 2.5, sigma=sigma)
    print LSF.getSF(11, 200, -2.5, sigma=sigma)
    print LSF.getSF(13, 200, 2.5, sigma=sigma)
    print LSF.getSF(13, 200, -2.5, sigma=sigma)

    print "2018, tight"
    LSF = LeptonSF(year=2018, ID="tight")
    print LSF.getSF(11, 20, 1, sigma=sigma)
    print LSF.getSF(11, 20, -1, sigma=sigma)
    print LSF.getSF(13, 20, 1, sigma=sigma)
    print LSF.getSF(13, 20, -1, sigma=sigma)

    print LSF.getSF(11, 200, 1, sigma=sigma)
    print LSF.getSF(11, 200, -1, sigma=sigma)
    print LSF.getSF(13, 200, 1, sigma=sigma)
    print LSF.getSF(13, 200, -1, sigma=sigma)

    print LSF.getSF(11, 20, 2.5, sigma=sigma)
    print LSF.getSF(11, 20, -2.5, sigma=sigma)
    print LSF.getSF(13, 20, 2.5, sigma=sigma)
    print LSF.getSF(13, 20, -2.5, sigma=sigma)

    print LSF.getSF(11, 200, 2.5, sigma=sigma)
    print LSF.getSF(11, 200, -2.5, sigma=sigma)
    print LSF.getSF(13, 200, 2.5, sigma=sigma)
    print LSF.getSF(13, 200, -2.5, sigma=sigma)
