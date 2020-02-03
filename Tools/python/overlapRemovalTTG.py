
import ROOT
import copy
from math import isnan

from Analysis.Tools.helpers         import deltaR

""" 
Make sure you use nMax = 1000 (or large number) when reading in genParts from nanoAOD using VectorTreeVariable.fromString('GenPart[%s]'%variables, nMax = 1000)
These functions use gen-matching where the references to ALL gen particles are needed

""" 

def isIsolatedPhoton( g, genparts, coneSize=0.2, ptCut=5, excludedPdgIds=[ 12, -12, 14, -14, 16, -16 ] ):
    for other in genparts:
        if other['pdgId']              == 22:       continue   # Avoid photon or generator copies of it
        if other['pdgId'] in excludedPdgIds:        continue   # Avoid particles you don't want to consider (e.g. neutrinos)
        if abs( other['pt'] - g['pt'] ) < 0.0001:   continue   # Same particle
        if other['status']             != 1:        continue   # Only final state particles
        if other['pt']                  < ptCut:    continue   # pt > 5
        if deltaR( g, other )           > coneSize: continue   # check deltaR
        return False
    return True

# Run through parents in genparticles, and return list of their pdgId
def getParentIds( g, genParticles ):
  parents = []

  if g['genPartIdxMother'] >= 0:
    try:
        # This is safer than "genParticles[ g['genPartIdxMother'] ]", as the genParticles list can be sorted first, however it requires to add "index" in the dict before sorting
        mother1  = [ genParticle for genParticle in genParticles if genParticle["index"] == g['genPartIdxMother'] ][0]
        parents += [ mother1['pdgId'] ] + getParentIds( mother1, genParticles )
    except:
        # when no 'status' selection is made for g, this can run in a kind of endless-loop, then python throws an Exception
        return parents
  return parents

def hasMesonMother( parentList ):
    if not parentList: return False
    maxParentID = max( map( abs, parentList ) )
    return maxParentID > 37 and maxParentID < 999

def photonFromTopDecay( parentList ):
    if not parentList:      return False  # empty list
    parentList = map( abs, parentList )
    if not 6 in parentList: return False  # ISR photon
    if parentList[0] == 6:  return False  # photon from top
    return True                           # photon from top decay

def photonFromLepton( parentList ):
    if not parentList:               return False  # empty list
    if hasMesonMother( parentList ): return False

    parentList = map( abs, parentList )
    parentList = filter( lambda pdg: pdg != 22, parentList )

    if not parentList:                                     return False # empty list
    if not any( pdg in [11,13,15] for pdg in parentList ): return False # lepton in parent list
    if not parentList[0] in [11,13,15]:                    return False # photon radiated from the lepteon
    return True                           # photon from top decay

def getPhotonCategory( g, genparts ):

    # safe time if g is no photon or electron
    if not g or abs(g['pdgId']) not in [11,22]: return 3

#    isIsolated = isIsolatedPhoton( g, genparts, coneSize=0.2, ptCut=5, excludedPdgIds=[12,-12,14,-14,16,-16] )
    parentList = getParentIds( g, genparts )
    hasMeson   = hasMesonMother( parentList )

    # type 4: magic photons: no gen-particle close by. These get categorized in getAdvancedPhotonCategory()
    if abs(g['pdgId']) == 22 and not hasMeson: return 0  # type 0: genuine photon:   photon with no meson in parent list
    if abs(g['pdgId']) == 22 and hasMeson:     return 1  # type 1: hadronic photon:  photon with meson in parent list
    if abs(g['pdgId']) == 11:                  return 2  # type 2: mis-Id electron:  electron with meson-mother requirement from genuine photon
    return 3

def hasLeptonMother( g, genparts ):
    if not g: return 0
    parentList = getParentIds( g, genparts )
    return int( photonFromLepton( parentList ) )

def getPhotonMother( g, genparts ):
    if not g: return -1

    parentList = getParentIds( g, genparts )
    if not parentList: return -1
    parentList = filter( lambda pdg: pdg != 22, parentList )
    if not parentList: return -1

    return int( parentList[0] )

def getAdvancedPhotonCategory( recoPart, genParts, coneSize=0.2, ptCut=5., excludedPdgIds=[ 12, -12, 14, -14, 16, -16 ] ):

    # nanoAOD genMatch found, just take that, do standard categorization
    if recoPart['genPartIdx'] >= 0:
        gen = filter( lambda g: g['index']==recoPart['genPartIdx'], genParts )[0]
        return getPhotonCategory( gen, genParts ) # standard photon categories

    rec = { val:recoPart[val] for val in ["pt","eta","phi","genPartIdx"] }
    # no reco particles to match
    if any( map( isnan, rec.values() ) ): return 3 # fakes

    # no gen particles to match
    if not genParts: return 4 # magic photons

    # do not only focus on status 1 particles, you need everything
    gParts = filter( lambda p: p['status']>0 and p['pt']>ptCut and p['pdgId'] not in excludedPdgIds, genParts )

    # no filtered gen particles to match
    if not gParts: return 4 # magic photons

    # else do a delta R matching to all gen particles
    # examples are tau- -> pi- pi0 nu_tau with pi0 -> gamma gamma
    # when pT(pi-) is small, and the two gen photons get reconstructed as one reco photon
    # and pT(gen gamma_1) ~ pT(gen gamma_2) and pT(reco gamma) > pT(gen gamma_1) + pT(gen gamma_2)
    # the nanoAOD gen matching has a problem due to the 50% pT cut in the matching algorithm
    # thus check for these kind of events with deltaR matching

    genAll  = [ (g, deltaR( recoPart, g )) for g in gParts ]
    genCone = filter( lambda (gen, dr): dr < coneSize, genAll ) if coneSize > 0 else genAll

    # no gen particle in deltaR cone
    if not genCone: return 4 # magic photons

    genCone.sort( key=lambda (gen, dr): dr )
    genConePdgIDs = [ abs(gen["pdgId"]) for (gen, dr) in genCone ]

    # pi0 and photon in dR cone
    if 111 in genConePdgIDs and 22 in genConePdgIDs:
        return 1 # hadronics, photon from pi0 decay
#        photon = filter( lambda (gen, dr): gen["pdgId"]==22, genCone )[0]
#        return photon["index"]

    return 3 # fake, gen particles close by, not pion decay, no nanoAOD gen-matching

def addParticle( to, add ):
    # add particle "add" to particle "to"
    toP  = ROOT.TLorentzVector()
    addP = ROOT.TLorentzVector()

    # add particles using TLorentzVector
    toP.SetPtEtaPhiM(  to['pt'],  to['eta'],  to['phi'],  0 )
    addP.SetPtEtaPhiM( add['pt'], add['eta'], add['phi'], 0 )
    comb = toP + addP

    # clone the properties of the to-particle and change its pt, eta, phi
    combParticle        = copy.copy(to)
    combParticle["pt"]  = comb.Pt()
    combParticle["eta"] = comb.Eta()
    combParticle["phi"] = comb.Phi()

    return combParticle

def addParticlesInCone( to, add, coneSize=0. ):
    # add particles from the add collection to particles from the to collection, if they are within a certain coneSize
    # one of the worst functions ever, sorry
    if coneSize <= 0: return copy.copy(to), copy.copy(add)

    add_ = copy.copy(add)
    to_  = []

    for t in to:

        removeIndex = []
        t_comb      = copy.copy(t)

        for i, a in enumerate( add_ ):
            if deltaR( t, a ) > coneSize: continue # no close particle, no particle to add
            t_comb = addParticle( t_comb, a )
            removeIndex.append(i)
            
        to_.append( t_comb )
        add_ = [ g for i, g in enumerate( add_ ) if i not in removeIndex ]

    return to_, add_

def calculateGenIso( g, genParts, coneSize=0.3, ptCut=5., excludedPdgIds=[ 12, -12, 14, -14, 16, -16 ], chgIso=False ):

    if g["pt"] == 0: return 999.

    # select gen particles to consider
    gParts = filter( lambda p: p['status'] == 1 and p['pt']>ptCut and p['pdgId'] not in excludedPdgIds and not (p['pt']==g['pt'] and p['eta']==g['eta'] and p['phi']==g['phi']), genParts )

    # filter gen particles in cone
    gParts = [ (p, deltaR( g, p )) for p in gParts ]
    gParts = filter( lambda (p, dr): dr < coneSize, gParts ) if coneSize > 0 else gParts
    if not gParts: return 0.

    if chgIso:
        gParts = filter( lambda (p, dr): p["pdgId"] not in [22,111,130,310,311,2112], gParts )
        if not gParts: return 0.

    print [p["pdgId"] for (p,dr) in gParts]

    pTCone = sum( [p["pt"] for (p, dr) in gParts] )
    return pTCone/g["pt"]

