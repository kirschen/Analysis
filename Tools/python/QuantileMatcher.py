''' Implements the matching of quantiles. Given two binned distributions (TH1),
    it computes x' = CDF2^-1 ( CDF1 ( x ) )
'''

# Standard imports
import ROOT
import array

# Logger
import logging
logger = logging.getLogger(__name__)

def transpose( h ):

    y = [h.GetBinContent( i ) for i in range( 1, 1+h.GetNbinsX() ) ]

    ret = ROOT.TH1D( h.GetName()+'_t', h.GetTitle()+'_t', len(y)-1, array.array('d', y) )
    for i in range( 1, 2+ret.GetNbinsX() ):
        ret.SetBinContent( i, h.GetBinLowEdge(i) )
   
    return ret 


class QuantileMatcher:

    def __init__( self, h1, h2 ):
        if h1.Integral()<=0 or h2.Integral()<=0:
            raise RuntimeError( "Need positive normalization!" )

        self.h1 = h1
        self.h2 = h2

        self.h1.Scale(1./self.h1.Integral()) 
        self.h2.Scale(1./self.h2.Integral())

        self.h1_cdf = h1.GetCumulative() 
        self.h2_cdf_inv = transpose( h2.GetCumulative() )

    def predict( self, x ):
        return self.h2_cdf_inv.GetBinContent(self.h2_cdf_inv.FindBin( self.h1_cdf.GetBinContent(self.h1_cdf.FindBin( x )) ))

if __name__=="__main__":
#    q = QuantileMatcher( h1, h2 )
    import pickle
    fitResults = pickle.load(file('/afs/hephy.at/user/r/rschoefbeck/www/StopsDilepton/recoil_v2/2018/lepSel-btag0-relIso0.12-looseLeptonVeto-mll20-onZ/recoil_fitResults_SF.pkl'))
    h1, h2 = fitResults[(2,3)][(50,100)]['para']['mc']['TH1F'], fitResults[(2,3)][(50,100)]['para']['data']['TH1F']

    h1.Scale(1./h1.Integral()) 
    h2.Scale(1./h2.Integral())

    h1_cdf = h1.GetCumulative() 
    h2_cdf_inv = transpose( h2.GetCumulative() )

    qm = QuantileMatcher( h1, h2 )
