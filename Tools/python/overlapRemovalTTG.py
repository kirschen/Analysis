from Analysis.Tools.helpers         import deltaR

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

  if g['genPartIdxMother'] > 0:
    try:
        # This is safer than "genParticles[ g['genPartIdxMother'] ]", as the genParticles list can be sorted first, however it requires to add "index" in the dict before sorting
        mother1  = [ genParticle["index"] == g['genPartIdxMother'] for genParticle in genParticles ][0]
        parents += [ mother1['pdgId'] ] + getParentIds( mother1, genParticles )
    except:
        # when no 'status' selection is made for g, this can run in a kind of endless-loop, then python throws an Exception
        return parents
  return parents

def hasMesonMother( parentList ):
    if not parentList: return False
    return max( map( abs, parentList ) ) > 37

def photonFromTopDecay( parentList ):
    if not parentList:      return False  # empty list
    parentList = map( abs, parentList )
    if not 6 in parentList: return False  # ISR photon
    if parentList[0] == 6:  return False  # photon from top
    return True                           # photon from top decay

def getPhotonCategory( g, genparts ):

    # safe time if g is no photon or electron
    if g is None or abs(g['pdgId']) not in [11,22]: return 3

    isIsolated = isIsolatedPhoton( g, genparts, coneSize=0.2, ptCut=5, excludedPdgIds=[12,-12,14,-14,16,-16] )
    hasMeson   = hasMesonMother( getParentIds( g, genparts ) )

    if abs(g['pdgId']) == 22 and isIsolated and not hasMeson: return 0        # type 0: genuine photon:   isolated photon with no meson in parent list
    if abs(g['pdgId']) == 22 and isIsolated and hasMeson:     return 1        # type 1: hadronic photon:  isolated photon with meson in parent list
    if abs(g['pdgId']) == 11 and isIsolated and not hasMeson: return 2        # type 2: miss-Id electron: electron with deltaR and meson-mother requirement from genuine photon
    return 3                                                                        # type 3: hadronic fake:    none of the above ( e.g. non-isolated )
