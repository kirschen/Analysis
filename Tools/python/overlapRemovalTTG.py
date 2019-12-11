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
    hasMeson   = hasMesonMother( getParentIds( g, genparts ) )

    if abs(g['pdgId']) == 22 and not hasMeson: return 0  # type 0: genuine photon:   photon with no meson in parent list
    if abs(g['pdgId']) == 22 and hasMeson:     return 1  # type 1: hadronic photon:  photon with meson in parent list
    if abs(g['pdgId']) == 11 and not hasMeson: return 2  # type 2: mis-Id electron:  electron with meson-mother requirement from genuine photon
    return 3

#    if abs(g['pdgId']) == 22 and isIsolated and hasMeson:     return 1        # type 1: hadronic photon:  isolated photon with meson in parent list
#    if abs(g['pdgId']) == 11 and isIsolated and not hasMeson: return 2       # type 2: mis-Id electron: electron with deltaR and meson-mother requirement from genuine photon

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

