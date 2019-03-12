'''
Getting weights + variations for L1 Prefiring, based on:
https://lathomas.web.cern.ch/lathomas/TSGStuff/L1Prefiring/PrefiringMaps_2016and2017/
CMSSW Producer can be found in:
https://github.com/cms-sw/cmssw/blob/793d75e56fbb6ab0e04069498f91f261c98e1a52/PhysicsTools/PatUtils/plugins/L1ECALPrefiringWeightProducer.cc
Twiki page:
https://twiki.cern.ch/twiki/bin/viewauth/CMS/L1ECALPrefiringWeightRecipe
'''

import os
import math
from Analysis.Tools.helpers import getObjFromFile, deltaR

class L1PrefireWeight:
    def __init__(self, year, syst=0.2):
        if year == 2016:
            self.phEff  = getObjFromFile(os.path.expandvars('$CMSSW_BASE/src/Analysis/Tools/data/L1Prefiring/L1prefiring_photonpt_2016BtoH.root'), 'L1prefiring_photonpt_2016BtoH')
            self.jetEff = getObjFromFile(os.path.expandvars('$CMSSW_BASE/src/Analysis/Tools/data/L1Prefiring/L1prefiring_jetpt_2016BtoH.root'), 'L1prefiring_jetpt_2016BtoH')
        elif year == 2017:
            self.phEff  = getObjFromFile(os.path.expandvars('$CMSSW_BASE/src/Analysis/Tools/data/L1Prefiring/L1prefiring_photonpt_2017BtoF.root'), 'L1prefiring_photonpt_2017BtoF')
            self.jetEff = getObjFromFile(os.path.expandvars('$CMSSW_BASE/src/Analysis/Tools/data/L1Prefiring/L1prefiring_jetpt_2017BtoF.root'), 'L1prefiring_jetpt_2017BtoF')
        else:
            self.phEff  = None
            self.jetEff = None

        if self.phEff:
            self.maxPtG = self.phEff.GetYaxis().GetXmax()
            self.maxPtJ = self.jetEff.GetYaxis().GetXmax()
        self.rel_syst = syst

    def getWeight(self, photons, jets):
        weight          = 1.
        weightUp        = 1.
        weightDown      = 1.
        overlapIndices  = []

        for jet in jets:
            if not 2.0 <= abs(jet['eta']) <= 3.0:
                continue
            
            pt_j = jet['pt']    if jet['pt']    < self.maxPtJ else self.maxPtJ - 1.
            if pt_j < 20: continue
            cleanJet = True

            # get overlap with photons
            for i,photon in enumerate(photons):
                if deltaR(photon, jet)<0.4:
                    cleanJet = False
                    overlapIndices.append(i)
                    pt_g = photon['pt'] if photon['pt'] < self.maxPtG else self.maxPtG - 1.
                    prefRatePh          = self.phEff.GetBinContent(self.phEff.GetXaxis().FindBin(photon['eta']), self.phEff.GetYaxis().FindBin(pt_g))
                    prefRatePh_stat     = self.phEff.GetBinError(self.phEff.GetXaxis().FindBin(photon['eta']), self.phEff.GetYaxis().FindBin(pt_g))
                    prefRateJet         = self.jetEff.GetBinContent(self.jetEff.GetXaxis().FindBin(jet['eta']), self.jetEff.GetYaxis().FindBin(pt_j))
                    prefRateJet_stat    = self.jetEff.GetBinError(self.jetEff.GetXaxis().FindBin(jet['eta']), self.jetEff.GetYaxis().FindBin(pt_j))

                    if prefRatePh > prefRateJet:
                        prefRate = prefRatePh
                        prefRate_stat = prefRatePh_stat
                    else:
                        prefRate = prefRateJet
                        prefRate_stat = prefRateJet_stat

            if cleanJet:
                prefRate        = self.jetEff.GetBinContent(self.jetEff.GetXaxis().FindBin(jet['eta']), self.jetEff.GetYaxis().FindBin(pt_j))
                prefRate_stat   = self.jetEff.GetBinError(self.jetEff.GetXaxis().FindBin(jet['eta']), self.jetEff.GetYaxis().FindBin(pt_j))

            weight      *= (1 - prefRate)
            weightUp    *= (1 - min(1, prefRate + math.sqrt(prefRate_stat**2 + (self.rel_syst * prefRate)**2) ) )
            weightDown  *= (1 - max(0, prefRate - math.sqrt(prefRate_stat**2 + (self.rel_syst * prefRate)**2) ) )


        for i, photon in enumerate(photons):
            if i not in overlapIndices:
                pt_g = photon['pt'] if photon['pt'] < self.maxPtG else self.maxPtG - 1.
                if pt_g < 20: continue
                prefRatePh          = self.phEff.GetBinContent(self.phEff.GetXaxis().FindBin(photon['eta']), self.phEff.GetYaxis().FindBin(pt_g))
                prefRatePh_stat     = self.phEff.GetBinError(self.phEff.GetXaxis().FindBin(photon['eta']), self.phEff.GetYaxis().FindBin(pt_g))
                
                weight      *= (1 - prefRatePh )
                weightUp    *= (1 - min(1, prefRatePh + math.sqrt(prefRatePh_stat**2 + (self.rel_syst * prefRatePh)**2) ) )
                weightDown  *= (1 - max(0, prefRatePh - math.sqrt(prefRatePh_stat**2 + (self.rel_syst * prefRatePh)**2) ) )

        return weight, weightUp, weightDown

