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
        self.correction_data = pickle.load(file('/afs/hephy.at/user/r/rschoefbeck/www/StopsDilepton/recoil_v2/2018/lepSel-btag0-relIso0.12-looseLeptonVeto-mll20-onZ/recoil_fitResults_SF.pkl'))

        self.njet_bins = self.correction_data.keys()
        self.max_njet  = max( map( max, self.njet_bins )) 
        self.min_njet  = min( map( min, self.njet_bins )) 

        self.qt_bins = self.correction_data[self.njet_bins[0]].keys()
        self.max_qt  = max( map( max, self.qt_bins )) 
        self.min_qt  = min( map( min, self.qt_bins )) 

        if self.min_qt!=0:
            logger.error( "Minimum qt at %3.2f! Should be 0", self.min_qt )

        self.para_matcher = { nj_bin: {qt_bin: QuantileMatcher(self.correction_data[nj_bin][qt_bin]['para']['mc']['TH1F'], self.correction_data[nj_bin][qt_bin]['para']['data']['TH1F']) for qt_bin in self.qt_bins} for nj_bin in self.njet_bins } 
        self.perp_matcher = { nj_bin: {qt_bin: QuantileMatcher(self.correction_data[nj_bin][qt_bin]['perp']['mc']['TH1F'], self.correction_data[nj_bin][qt_bin]['perp']['data']['TH1F']) for qt_bin in self.qt_bins} for nj_bin in self.njet_bins } 

        logger.info( "Constructed para and perp matchers: %i njet bins and %i qt bins", len(self.njet_bins), len(self.qt_bins) )

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

    def qt_bin( self, qt ):
        # too low qt: don't return interval
        if qt<self.min_qt:
            return None

        # too high qt: return last interval
        if qt>=self.max_qt:
            qt = self.max_qt-1

        # find interval
        for iv in self.qt_bins:
            if qt>=iv[0] and qt<iv[1]:
                return iv

    def predict_para(self, njet, qt, u_para ):
        njet_bin   = self.njet_bin( njet )
        qt_bin = self.qt_bin( qt )

        if njet_bin and qt_bin:
            return self.para_matcher[njet_bin][qt_bin].predict( u_para )

    def predict_perp(self, njet, qt, u_perp ):
        njet_bin   = self.njet_bin( njet )
        qt_bin = self.qt_bin( qt )

        if njet_bin and qt_bin:
            return self.perp_matcher[njet_bin][qt_bin].predict( u_perp )

if __name__=="__main__":
    import Analysis.Tools.logger as logger
    logger    = logger.get_logger( "DEBUG", logFile = None)

    filename = '/afs/hephy.at/user/r/rschoefbeck/www/StopsDilepton/recoil_v2/2018/lepSel-btag0-relIso0.12-looseLeptonVeto-mll20-onZ/recoil_fitResults_SF.pkl'

    recoilCorrector = RecoilCorrector( filename )
