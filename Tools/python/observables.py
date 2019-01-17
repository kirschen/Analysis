''' Helper functions for Analysis
'''
#Standard imports
import ROOT
import itertools
from math                                       import pi, sqrt, cosh

# Logging
import logging
logger = logging.getLogger(__name__)

defaultValue = -999
mZ = 91.2

def cosThetaStar( Z_mass, Z_pt, Z_eta, Z_phi, l_pt, l_eta, l_phi ):

    Z   = ROOT.TVector3()
    l   = ROOT.TVector3()
    Z.SetPtEtaPhi( Z_pt, Z_eta, Z_phi )
    l.SetPtEtaPhi( l_pt, l_eta, l_phi )
    
    # get cos(theta) and the lorentz factor, calculate cos(theta*)
    cosTheta = Z*l / (sqrt(Z*Z) * sqrt(l*l))
    gamma   = sqrt( 1 + Z_pt**2/Z_mass**2 * cosh(Z_eta)**2 )
    beta    = sqrt( 1 - 1/gamma**2 )
    return (-beta + cosTheta) / (1 - beta*cosTheta)

def deltaPhi(phi1, phi2):
    dphi = phi2-phi1
    if  dphi > pi:
        dphi -= 2.0*pi
    if dphi <= -pi:
        dphi += 2.0*pi
    return abs(dphi)

def deltaR2(l1, l2):
    return deltaPhi(l1['phi'], l2['phi'])**2 + (l1['eta'] - l2['eta'])**2

def deltaR(l1, l2):
    return sqrt(deltaR2(l1,l2))

# Returns (closest mass, index1, index2)
def closestOSDLMassToMZ(leptons):
    inds = range(len(leptons))
    vecs = [ ROOT.TLorentzVector() for i in inds ]
    for i, v in enumerate(vecs):
        v.SetPtEtaPhiM(leptons[i]['pt'], leptons[i]['eta'], leptons[i]['phi'], 0.)
    dlMasses = [((vecs[comb[0]] + vecs[comb[1]]).M(), comb[0], comb[1])  for comb in itertools.combinations(inds, 2) if leptons[comb[0]]['pdgId']*leptons[comb[1]]['pdgId'] < 0 and abs(leptons[comb[0]]['pdgId']) == abs(leptons[comb[1]]['pdgId']) ]
    return min(dlMasses, key=lambda (m,i1,i2):abs(m-mZ)) if len(dlMasses)>0 else (defaultValue, -1, -1)

def getMinDLMass(leptons):
    inds = range(len(leptons))
    vecs = [ ROOT.TLorentzVector() for i in inds ]
    for i, v in enumerate(vecs):
        v.SetPtEtaPhiM(leptons[i]['pt'], leptons[i]['eta'], leptons[i]['phi'], 0.)
    dlMasses = [((vecs[comb[0]] + vecs[comb[1]]).M(), comb[0], comb[1])  for comb in itertools.combinations(inds, 2) ]
    return min(dlMasses), dlMasses

def getGenZ(genparts):
    for g in genparts:
        if g['pdgId'] != 23:  continue					# pdgId == 23 for Z
        if g['status'] != 62: continue					# status 62 is last gencopy before it decays into ll/nunu
        return g
    return None

def getGenPhoton(genparts):
    for g in genparts:								# Type 0: no photon
        if g['pdgId'] != 22:  continue					# pdgId == 22 for photons
        if g['status'] != 23: continue					# for photons, take status 23
        return g
    return None

def getGenB(genparts):
    for g in genparts:
        if abs(g['pdgId']) != 5: continue
        if g['status'] != 23:    continue
        return g
    return None

def m3( jets, nBJets=0, tagger='DeepCSV', year=2016 ):
    """ Calculate M3 Variable with a min amount of bJets in it
    """
    if len( jets ) < 3 or nBJets > 3 or nBJets > len( jets ): return defaultValue, -1, -1, -1

    vecs = []
    for i, j in enumerate( jets ):
        vec = ROOT.TLorentzVector()
        vec.SetPtEtaPhiM( j['pt'], j['eta'], j['phi'], 0. )
        vecs.append( ( i, vec ) )

    maxSumPt   = 0
    m3         = defaultValue
    i1, i2, i3 = -1, -1, -1

    from Analysis.Tools.objectSelection import isBJet

    for j3_comb in itertools.combinations( vecs, 3 ):
        if nBJets > 0:
            nBs = sum( [ isBJet( jets[v[0]], tagger=tagger, year=year ) for v in j3_comb ] )
            if nBs != nBJets: continue

        vecSum = sum( [ v[1] for v in j3_comb ], ROOT.TLorentzVector() )
        if vecSum.Pt() > maxSumPt:
            maxSumPt   = vecSum.Pt()
            m3         = vecSum.M()
            i1, i2, i3 = [ v[0] for v in j3_comb ]

    return m3, i1, i2, i3


