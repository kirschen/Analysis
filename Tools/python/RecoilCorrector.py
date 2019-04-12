''' RecoilCorrector based on QuantileMatcher
'''

# Standard imports
import ROOT
import array
import pickle

# Analysis
from Analysis.Tools.QuantileMatcher import QuantileMatcher

# Logger
import logging
logger = logging.getLogger(__name__)

class RecoilCorrector:

    def __init__(self, filename ):
        self.filename    = filename
        self.recoil_data = pickle.load(file('/afs/hephy.at/user/r/rschoefbeck/www/StopsDilepton/recoil_v2/2018/lepSel-btag0-relIso0.12-looseLeptonVeto-mll20-onZ/recoil_fitResults_SF.pkl'))

        self.njet_bins = self.recoil_data.keys()
        self.max_njet  = max( map( max, self.njet_bins )) 
        self.min_njet  = min( map( min, self.njet_bins )) 

        self.recoil_bins = self.recoil_data[self.njet_bins[0]].keys()
        self.max_recoil  = max( map( max, self.recoil_bins )) 
        self.min_recoil  = min( map( min, self.recoil_bins )) 

        if self.min_recoil!=0:
            logger.error( "Minimum recoil at %3.2f! Should be 0", self.min_recoil )

        self.para_matcher = { nj_bin: {recoil_bin: QuantileMatcher(self.recoil_data[nj_bin][recoil_bin]['para']['mc']['TH1F'], self.recoil_data[nj_bin][recoil_bin]['para']['data']['TH1F']) for recoil_bin in self.recoil_bins} for nj_bin in self.njet_bins } 
        self.perp_matcher = { nj_bin: {recoil_bin: QuantileMatcher(self.recoil_data[nj_bin][recoil_bin]['perp']['mc']['TH1F'], self.recoil_data[nj_bin][recoil_bin]['perp']['data']['TH1F']) for recoil_bin in self.recoil_bins} for nj_bin in self.njet_bins } 

        logger.info( "Constructed para and perp matchers: %i njet bins and %i recoil bins", len(self.njet_bins), len(self.recoil_bins) )

    def njet_bin( self, njet ):
        # too low njet: don't return interval
        if njet<self.min_njet:
            return None
        # too high njet: return last interval
        if njet>=self.max_njet:
            njet = self.max_njet-1

        # find interval
        for iv in self.njet_bins:
            if njet>=iv[0] and njet<iv[1]:
                return iv

    def recoil_bin( self, recoil ):
        # too low recoil: don't return interval
        if recoil<self.min_recoil:
            return None

        # too high recoil: return last interval
        if recoil>=self.max_recoil:
            recoil = self.max_recoil-1

        # find interval
        for iv in self.recoil_bins:
            if recoil>=iv[0] and recoil<iv[1]:
                return iv

    def predict_para(self, njet, recoil, u_para ):
        njet_bin   = self.njet_bin( njet )
        recoil_bin = self.recoil_bin( recoil )

        if njet_bin and recoil_bin:
            return self.para_matcher[njet_bin][recoil_bin].predict( u_para )

    def predict_perp(self, njet, recoil, u_perp ):
        njet_bin   = self.njet_bin( njet )
        recoil_bin = self.recoil_bin( recoil )

        if njet_bin and recoil_bin:
            return self.perp_matcher[njet_bin][recoil_bin].predict( u_perp )

if __name__=="__main__":
    import Analysis.Tools.logger as logger
    logger    = logger.get_logger( "DEBUG", logFile = None)

    filename = '/afs/hephy.at/user/r/rschoefbeck/www/StopsDilepton/recoil_v2/2018/lepSel-btag0-relIso0.12-looseLeptonVeto-mll20-onZ/recoil_fitResults_SF.pkl'

    recoilCorrector = RecoilCorrector( filename )
