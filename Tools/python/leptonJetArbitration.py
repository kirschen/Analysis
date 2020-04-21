# Jet Lepton cross cleaning as used in CMG-tools

# https://github.com/CERN-PH-CMG/cmg-cmssw/blob/0fdfc10e2a2d4732cbb5d540b46543498cb6d006/PhysicsTools/Heppy/python/analyzers/objects/JetAnalyzer.py#L25-L49

from Analysis.Tools.helpers import deltaR2

def cleanJetsAndLeptons(jets, leptons, deltaR=0.4, arbitration = (lambda jet, lepton: lepton) ):
    # threshold
    dr2 = deltaR**2
    # Assume jets and leptons are all good
    goodjet = [ True for jet in jets ]
    goodlep = [ True for lep in leptons ]
    for i_lep, lep in enumerate(leptons):
        i_jet_best, d2min = -1, dr2
        for i_jet, jet in enumerate(jets):
            d2i = deltaR2(lep, jet)
            if d2i < dr2:
                choice = arbitration(jet,lep)
                if choice == jet:
                   # if the two match, and we prefer the jet, then drop the lepton and be done
                   goodlep[i_lep] = False
                   break 
                elif choice == (jet,lep) or choice == (lep,jet):
                   # asked to keep both, so we don't consider this match
                   continue
            # find best match
            if d2i < d2min:
                i_jet_best, d2min = i_jet, d2i
        # this lepton has been killed by a jet, then we clean the jet that best matches it
        if not goodlep[i_lep]: continue 
        if i_jet_best != -1: goodjet[i_jet_best] = False
    return ( [ jet for (i_jet, jet) in enumerate(jets)    if goodjet[i_jet] == True ], 
             [ lep for (i_lep, lep) in enumerate(leptons) if goodlep[i_lep] == True ])
