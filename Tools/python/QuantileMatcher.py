''' Implements the matching of quantiles. Given two binned distributions (TH1),
    it computes x' = CDF2^-1 ( CDF1 ( x ) )
'''

# Standard imports
import ROOT
import array
import uuid

# Logger
import logging
logger = logging.getLogger(__name__)

def transpose( h ):

    y = [h.GetBinContent( i ) for i in range( 1, 1+h.GetNbinsX() ) ]

    ret = ROOT.TH1D( h.GetName()+'_t', h.GetTitle()+'_t', len(y)-1, array.array('d', y) )
    for i in range( 1, 1+ret.GetNbinsX() ):
        ret.SetBinContent( i, h.GetBinLowEdge(i) )
   
    return ret 

class QuantileMatcher:

    def __init__( self, h1, h2, maxAbsU = None):
        if h1.Integral()<=0 or h2.Integral()<=0:
            raise RuntimeError( "Need positive normalization!" )

        self.h1 = h1
        self.h2 = h2


        self.maxAbsU = maxAbsU

        #for i in range(1, self.h1.GetNbinsX()+1):
        #    if abs(self.h1.GetBinLowEdge(i))>100:
        #        self.h1.SetBinContent(i, 0 )
        #        print i
        #for i in range(1, self.h2.GetNbinsX()+1):
        #    if abs(self.h2.GetBinLowEdge(i))>100:
        #        self.h2.SetBinContent(i, 0 )

        self.h1.Scale(1./self.h1.Integral()) 
        self.h2.Scale(1./self.h2.Integral())


        self.h1_cdf = self.h1.GetCumulative(True, str(uuid.uuid4())) 
        self.h2_cdf_inv = transpose( self.h2.GetCumulative(True, str(uuid.uuid4())) )

    def predict( self, u ):
        if self.maxAbsU is not None and abs(u) > self.maxAbsU:
            x = self.maxAbsU if u>0 else -self.maxAbsU 
        else:
            x = u
        
        delta = self.h2_cdf_inv.Interpolate(  self.h1_cdf.Interpolate( x ) ) - x

        return u+delta

    def prediction_histo( self, n_bins, u_low, h_high ):
        name = str(uuid.uuid4())
        h = ROOT.TH1F(name,name,  n_bins, u_low, h_high)
        for i in range(1, n_bins+1):
            h.SetBinContent( i, self.predict( h.GetBinLowEdge(i)) )
        return h 

    @staticmethod
    def __get_quantiles( histo, quantiles):
        thresholds = array.array('d', [ROOT.Double()] * len(quantiles) )
        histo.GetQuantiles( len(quantiles), thresholds, array.array('d', quantiles) )
        return thresholds 

    def get_h1_quantiles( self, quantiles = [ 0.31, 0.5, 0.68] ):
        return self.__get_quantiles( self.h1, quantiles)
    def get_h2_quantiles( self, quantiles = [ 0.31, 0.5, 0.68] ):
        return self.__get_quantiles( self.h2, quantiles)

if __name__=="__main__":
#    q = QuantileMatcher( h1, h2 )
    import pickle
    fitResults = pickle.load(file('/afs/hephy.at/data/rschoefbeck01/StopsDilepton/results/recoilCorrections/2018_postHEM_recoil_fitResults_SF.pkl'))
    h1, h2 = fitResults[(2,3)][(50,100)]['para']['mc']['TH1F'], fitResults[(2,3)][(50,100)]['para']['data']['TH1F']

    h1.Scale(1./h1.Integral()) 
    h2.Scale(1./h2.Integral())

    h1_cdf = h1.GetCumulative() 
    h2_cdf_inv = transpose( h2.GetCumulative() )

    qm = QuantileMatcher( h1, h2, maxAbsU=150)

    c1 = ROOT.TCanvas()
    h  = qm.prediction_histo(100,-200,200)
    h.Draw()
    h.GetXaxis().SetTitle( "raw u_{#parallel}")
    h.GetYaxis().SetTitle( "predicted u_{#parallel}")
    ROOT.gStyle.SetOptStat(0)
    ROOT.TLine(-200,-200,200,200)
    l=ROOT.TLine(-200,-200,200,200)
    l.Draw()
    c1.Print('/afs/hephy.at/user/r/rschoefbeck/www/etc/recoil_test.png')
