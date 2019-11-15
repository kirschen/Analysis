'''TMVA wrapper
'''

# standard imports
import os, sys
import ROOT
ROOT.gROOT.SetBatch(True)
import random
import ctypes
import copy

from array                 import array
from root_numpy            import ROOT_VERSION
from operator              import attrgetter

# Analysis
from Analysis.TMVA.helpers  import *

# RootTools
from RootTools.core.standard import *

# Logging
if __name__=="__main__":
    import Analysis.Tools.logger as logger
    logger = logger.get_logger("INFO", logFile = None )
else:
    import logging
    logger = logging.getLogger(__name__)

# example methods

default_factory_settings = [ "!V", "!Silent", "Color", "DrawProgressBar", "Transformations=I;D;P;G,D", "AnalysisType=Classification" ]

example_methods = {
    "cutOpt": { 
        "type"                : ROOT.TMVA.Types.kCuts,
        "name"                : "cutOpt",
        "color"               : ROOT.kRed,
        "options"             : ["!H","!V","VarTransform=None","CreateMVAPdfs=True","FitMethod=GA","EffMethod=EffSel","VarProp=NotEnforced","CutRangeMin=-1","CutRangeMax=-1"],
        },
    "MLP":{
        "type"                : ROOT.TMVA.Types.kMLP,
        "name"                : "MLP21",
        "layers"              : [1],
        "color"               : ROOT.kRed,
        "options"             : ["!H","!V","VarTransform=Norm,Deco","NeuronType=sigmoid","NCycles=10000","TrainingMethod=BP","LearningRate=0.03", "DecayRate=0.01","Sampling=0.3","SamplingEpoch=0.8","ConvergenceTests=1","CreateMVAPdfs=True","TestRate=10" ],
        },
    "BDT":{
        "type"                : ROOT.TMVA.Types.kBDT,
        "name"                : "BDT",
        "color"               : ROOT.kBlue,
        "options"             : ["!H","!V","NTrees=1000","BoostType=Grad","Shrinkage=0.20","UseBaggedBoost","GradBaggingFraction=0.5","SeparationType=GiniIndex","nCuts=500","PruneMethod=NoPruning","MaxDepth=5"]
        },
}

class Wrapper:
    def __init__( self, signal, backgrounds, mva_variables, output_directory, plot_directory, label="MVA", fractionTraining=0.5):

        # Samples
        self.signal              = signal      # Sample object
        self.backgrounds         = backgrounds # list of Sample objects
        self.samples             = [signal] + backgrounds

        self.label               = label
        self.fractionTraining    = float(fractionTraining)
        self.setup               = {}
        self.read_variables      = []
        self.mva_variables       = mva_variables
        self.calc_variables      = []
        self.output_directory    = os.path.join( output_directory if output_directory else mva_directory, self.label )
        self.dataFile            = os.path.join( self.output_directory, self.label + ".root" )
        self.mvaOutFile          = os.path.join( self.output_directory, self.label + "_MVAOutput.root" )
        self.mvaWeightDir        = "weights"
        self.configFile          = self.dataFile.replace(".root", ".pkl")
        self.max_nEvents_trainings = None
        self.plot_directory      = os.path.join( plot_directory, "MVA", self.label )

        self.tree                = None

        randomSeed = 1
        random.seed( randomSeed )

        if not os.path.isdir( self.plot_directory ):
            os.makedirs( self.plot_directory )

        if not os.path.isdir( self.output_directory ):
            os.makedirs( self.output_directory )

        if not os.path.isdir( self.mvaWeightDir ):
            os.makedirs( self.mvaWeightDir )

    def createTestAndTrainingSample( self, read_variables=[], sequence = [], weightString="1", overwrite = False):
        ''' Creates a single background and a single signal sample for training purposes
        '''
        self.read_variables = read_variables
        self.sequence       = sequence 
        self.weightString   = weightString

        # return if the samples are done already
        if not overwrite and os.path.isfile( self.dataFile ):
            self.trainingAndTestSample = Sample.fromFiles("TrainingAndTestSample", files = [self.dataFile])
            return self.trainingAndTestSample
    
        # Get yields and counts for all samples, because we want to mix the events according to their yield
        for s in self.samples:
            s._yield = s.getYieldFromDraw( weightString=self.weightString )["val"]
            s.count  = int(s.getYieldFromDraw( weightString="(1)" )["val"])
            logger.info( "Found %i events for sample %s", s.count, s.name )

        # calculate training sample sizes and mix weighted backgrounds according to lumi yields
        #   finds nbBkg1,...,nBkgN such that nBkg1+...+nBkgN is maximal while respecting
        #   nBkg1+nBkg2+...+nBkgN<=nSigTraining, nBkg1:nBkg2:...:nBkgN=yBkg1:yBkg2:...:yBkgN
        #   and nBkg1<=self.fractionTraining*nBkg1Max, ...., self.fractionTraining*nBkgNMax<=nBkgNMax

        # Check we're OK overall
        maxSignalCount = int( self.fractionTraining * self.signal.count )
        assert maxSignalCount > 0, "Too few signal events. Training events: %i"%maxSignalCount
        maxBkgYield = float( max( [ b._yield for b in self.backgrounds ] ) )
        assert maxBkgYield > 0, "Maximum background yield non-positive: %f"%maxBkgYield

        # maximum number of training events that are available in each sample
        for background in self.backgrounds:
            background.maxTrainingEvents = int( self.fractionTraining * background.count )
            assert background.maxTrainingEvents > 0, "Not enough training events in bkg sample: %s" % background.name
            # compute the average weight in the background sample 
            background.average_weight = float( background._yield ) / int( self.fractionTraining * background.count )

        background_with_max_average_weight = max(self.backgrounds, key=attrgetter('average_weight'))

        # The maximum number of training events per sample consistent with the requirements
        maxAchievableBkg = [ int( self.fractionTraining * background.count * (background._yield/background_with_max_average_weight._yield) ) for background in self.backgrounds ]

        # Case1: We have more signal than the combined background
        #        The background samples limit. 
        if sum( maxAchievableBkg ) < maxSignalCount:
            logger.info("Backgrounds limit training statistic.")
            self.signal.max_nEvents_training = sum(maxAchievableBkg)
            for background in self.backgrounds:
                background.max_nEvents_training = int( self.fractionTraining * background.count * (background._yield/background_with_max_average_weight._yield) )
        # Case2: We have more background than the signal
        #        The signal sample limits. 
        else:
            logger.info("Signal limits training statistic.")
            self.signal.max_nEvents_training = maxSignalCount
            for background in self.backgrounds:
                background.max_nEvents_training = int( self.fractionTraining * background.count * (background._yield/background_with_max_average_weight._yield)*(maxSignalCount/float(sum(maxAchievableBkg))))

        for i_sample, sample in enumerate( self.samples ):
            logger.info( "Sample %20s using %8i events out of %8i which are %i%%.", sample.name, sample.max_nEvents_training, sample.count, round(100*sample.max_nEvents_training/float(sample.count)) )

        # determine randomized training event sequence
        for sample in self.samples:
            sample.training_test_list = [1]*sample.max_nEvents_training + [0]*(sample.count-sample.max_nEvents_training)
            random.shuffle( sample.training_test_list )

        # Now write a single ntuple with one tree that contains
        # the correct number of background events and also contains isSignal and isTraining

        # make random list of bkg and signal positions of the correct length for random loop:
        sig_bkg_list = []
        for i_sample, sample in enumerate(self.samples):
            sig_bkg_list.extend( [i_sample]*sample.count )
            sample.reader = sample.treeReader( \
                variables = map( TreeVariable.fromString, read_variables),
                )
            sample.reader.start()

        random.shuffle(sig_bkg_list)

        def filler( event ):
            # get a random reader
            event.isTraining = isTraining
            event.isSignal   = isSignal
            # write mva variables
            for name, func in self.mva_variables.iteritems():
                setattr( event, name, func(reader.event) )

        # Create a maker. Maker class will be compiled. 
        maker = TreeMaker(
            sequence  = [ filler ],
            variables = map(TreeVariable.fromString, ["isTraining/I", "isSignal/I"] + ["%s/F"%var for var in self.mva_variables.keys()] ), 
            treeName = "Events"
            )

        maker.start()
#        # Do the thing
#        reader.start()
#
        counter = 0
        while len(sig_bkg_list):
            # determine random sample
            i_sample = sig_bkg_list.pop(0) 
            # get its reader
            reader = self.samples[i_sample].reader
            reader.run()
            for func in self.sequence:
                func(reader.event)
            # determine whether training or test
            isTraining = self.samples[i_sample].training_test_list.pop(0) 
            isSignal   = (i_sample == 0)
                
            maker.run()
            
            counter += 1
            if counter%10000 == 0: 
                logger.info("Written %i events.", counter)

        nEventsTotal = maker.tree.GetEntries()

        tmp_directory = ROOT.gDirectory
        outputfile = ROOT.TFile.Open(self.dataFile, 'recreate')
        maker.tree.Write()
        outputfile.Close()
        tmp_directory.cd()
        logger.info( "Written %s", self.dataFile)
#
#      # Destroy the TTree
        maker.clear()
        logger.info( "Written %i events to %s",  nEventsTotal, self.dataFile )

        self.trainingAndTestSample = Sample.fromFiles("TrainingAndTestSample", files = [self.dataFile])
        return self.trainingAndTestSample

    def loadDatasetForTMVA( self ):

        if not self.tree:
            self.tree             = getAnyObjFromFile( self.dataFile, 'Events' )

        return { 'tree':self.tree,
               }


    def addMethod( self, method ):
        # for MLP add HiddenLayer option that is of the form N,x,y,z,... where N is the number of variables and x,y,z the "layers" key
        if method["type"]==ROOT.TMVA.Types.kMLP:
            method["options"].append( "HiddenLayers=%s" % ",".join( map( str, [len( self.mva_variables.keys() )] + method["layers"] )) )

        if not hasattr( self, "methods" ):
            self.methods = []

        self.methods.append( method )


    def trainMVA( self, factory_settings = default_factory_settings):

        data = self.loadDatasetForTMVA()
        rootGDirectory = ROOT.gDirectory.CurrentDirectory().GetName()+":/"

        ROOT.TMVA.Tools.Instance()
        ROOT.TMVA.gConfig().GetIONames().fWeightFileDir = self.mvaWeightDir
        ROOT.TMVA.gConfig().GetVariablePlotting().fNbinsXOfROCCurve = 200
        ROOT.TMVA.gConfig().GetVariablePlotting().fMaxNumOfAllowedVariablesForScatterPlots = 2
        
        fout    = ROOT.TFile( self.mvaOutFile, "RECREATE" )
        factory = ROOT.TMVA.Factory( "TMVAClassification", fout, ":".join(factory_settings) )
        factory.DeleteAllMethods()

        dataloader = ROOT.TMVA.DataLoader('.') if ROOT_VERSION >= '6.07/04' else factory

        for key in self.mva_variables.keys():
            dataloader.AddVariable(key, 'F')

        bkgTestTree  = data["tree"].CopyTree("isTraining==0&&isSignal==0")
        sigTestTree  = data["tree"].CopyTree("isTraining==0&&isSignal==1")
        bkgTrainTree = data["tree"].CopyTree("isTraining==1&&isSignal==0")
        sigTrainTree = data["tree"].CopyTree("isTraining==1&&isSignal==1")
        dataloader.AddBackgroundTree( bkgTrainTree, 1.0, "Training" )
        dataloader.AddBackgroundTree( bkgTestTree,  1.0, "Test" )
        dataloader.AddSignalTree(     sigTrainTree, 1.0, "Training" )
        dataloader.AddSignalTree(     sigTestTree,  1.0, "Test" )

        BookMethod = factory.BookMethod if ROOT_VERSION >= '6.07/04' else ROOT.TMVA.Factory.BookMethod
        for method in self.methods:
            args = (dataloader, method["type"], method["name"], ":".join(method["options"]))
            methodBook = BookMethod(*args)

        factory.TrainAllMethods()
        factory.TestAllMethods()
        factory.EvaluateAllMethods()

        fout.Close()

    def plotEvaluation( self ):

        nbinsFine = 2000

        testTree  = getAnyObjFromFile( self.mvaOutFile, "TestTree" )
        trainTree = getAnyObjFromFile( self.mvaOutFile, "TrainTree" )

        for method in self.methods:

            method["h_sig_test"]      = ROOT.TH1F( "h_sig_test",      "h_sig_test",      20, 0, 1.)
            method["h_bkg_test"]      = ROOT.TH1F( "h_bkg_test",      "h_bkg_test",      20, 0, 1.)
            method["h_sig_test_fine"] = ROOT.TH1F( "h_sig_test_fine", "h_sig_test_fine", nbinsFine, 0, 1.)
            method["h_bkg_test_fine"] = ROOT.TH1F( "h_bkg_test_fine", "h_bkg_test_fine", nbinsFine, 0, 1.)
            method["h_sig_test"]     .style = styles.lineStyle(ROOT.kRed, dashed = True) 
            method["h_bkg_test"]     .style = styles.lineStyle(ROOT.kBlue, dashed = True) 
            method["h_sig_test_fine"].style = styles.lineStyle(ROOT.kRed, dashed = True) 
            method["h_bkg_test_fine"].style = styles.lineStyle(ROOT.kBlue, dashed = True) 
            method["h_sig_test"]      .legendText = method["name"] + " sig test" 
            method["h_bkg_test"]      .legendText = method["name"] + " bkg test" 

            testTree.Draw( method["name"]+">>+h_sig_test",      "classID==1", "goff")
            testTree.Draw( method["name"]+">>+h_bkg_test",      "classID==0", "goff")
            testTree.Draw( method["name"]+">>+h_sig_test_fine", "classID==1", "goff")
            testTree.Draw( method["name"]+">>+h_bkg_test_fine", "classID==0", "goff")

            method["h_sig_train"]      = ROOT.TH1F( "h_sig_train",      "h_sig_train",      20, 0, 1.)
            method["h_bkg_train"]      = ROOT.TH1F( "h_bkg_train",      "h_bkg_train",      20, 0, 1.)
            method["h_sig_train_fine"] = ROOT.TH1F( "h_sig_train_fine", "h_sig_train_fine", nbinsFine, 0, 1.)
            method["h_bkg_train_fine"] = ROOT.TH1F( "h_bkg_train_fine", "h_bkg_train_fine", nbinsFine, 0, 1.)
            method["h_sig_train"]     .style = styles.lineStyle(ROOT.kRed) 
            method["h_bkg_train"]     .style = styles.lineStyle(ROOT.kBlue) 
            method["h_sig_train_fine"].style = styles.lineStyle(ROOT.kRed) 
            method["h_bkg_train_fine"].style = styles.lineStyle(ROOT.kBlue) 
            method["h_sig_train"]     .legendText = method["name"] + " sig train" 
            method["h_bkg_train"]     .legendText = method["name"] + " bkg train" 

            trainTree.Draw( method["name"]+">>+h_sig_train",      "classID==1", "goff")
            trainTree.Draw( method["name"]+">>+h_bkg_train",      "classID==0", "goff")
            trainTree.Draw( method["name"]+">>+h_sig_train_fine", "classID==1", "goff")
            trainTree.Draw( method["name"]+">>+h_bkg_train_fine", "classID==0", "goff")

            method["FOM"] = self.getFOMPlot( method["h_bkg_test_fine"], method["h_sig_test_fine"] )
            method["FOM"]["central"].SetLineColor( method["color"] )
            method["FOM"]["central"].SetTitle("FoM "+method["name"])

            plotting.draw(
                Plot.fromHisto(name = "discriminator_"+method["name"], 
                    histos = [[ method["h_sig_test"]], [ method["h_sig_train"]], [method["h_bkg_test"]], [method["h_bkg_train"]] ], 
                    texX = "Discriminator "+method["name"], texY = ""),
                plot_directory = self.plot_directory,  
                logX = False, logY = False, sorting = False,
                legend = ( (0.2, 0.75, 0.8, 0.9), 2),
                scaling = {1:0, 2:0, 3:0},
            )

        c1  = ROOT.TCanvas()
        c1.SetGrid()
        l   = ROOT.TLegend(.16, .13, 0.5, 0.35)
        l.SetFillColor(0)
        l.SetShadowColor(ROOT.kWhite)
        l.SetBorderSize(1)
        opt = ""
        #coord = [ 0, 0.8, 0.5, 1.0 ]
        coord = [ 0, 1, 0, 1 ]
        for method in self.methods:
            #method["FOM"]["central"].SetStats(False)
            method["FOM"]["central"].SetLineColor( method["color"] )
            method["FOM"]["central"].SetFillColor(0)
            method["FOM"]["central"].SetLineWidth( 2 )
            method["FOM"]["central"].SetMarkerColor( method["color"] )
            method["FOM"]["central"].SetMarkerStyle(0)
            method["FOM"]["central"].SetTitle("FoM "+method["name"])
            method["FOM"]["central"].GetXaxis().SetLimits(coord[0],coord[1])
            method["FOM"]["central"].GetYaxis().SetLimits(coord[2],coord[3])
            method["FOM"]["central"].GetXaxis().SetTitle('Signal efficiency')
            method["FOM"]["central"].GetYaxis().SetTitle('Background rejection')

            method["FOM"]["central"].Draw(opt)

            l.AddEntry(method["FOM"]["central"], method["name"])

            opt="L"
            if not method["type"]==ROOT.TMVA.Types.kCuts:
                method["FOM"]["plus"].SetLineStyle(3)
                method["FOM"]["minus"].SetLineStyle(3)
                method["FOM"]["plus"].SetLineWidth(2)
                method["FOM"]["minus"].SetLineWidth(2)
                method["FOM"]["plus"].SetLineColor(ROOT.kGray)
                method["FOM"]["minus"].SetLineColor(ROOT.kGray)
                #method["FOM"]["plus"].SetLineColor(method["color"])
                #method["FOM"]["minus"].SetLineColor(method["color"])
                method["FOM"]["plus"].Draw(opt)
                method["FOM"]["minus"].Draw(opt)
                l.AddEntry(method["FOM"]["plus"], method["name"]+" (#pm 1#sigma)", "LP")
            # Draw again, otherwise shadowed by error bands
            method["FOM"]["central"].Draw("same")
        l.Draw()
        for extension in ["pdf", "png", "root"]:
            c1.Print( os.path.join( self.plot_directory, "FOM_"+self.label+"."+extension) )

    def getFOMPlot( self, bgDisc, sigDisc ):

        assert bgDisc.GetNbinsX()==sigDisc.GetNbinsX(), "Need same binning for bkg and signal."

        zeros = []
        sigEff = []
        bkgRej = []
        sigEffPlus = []
        bkgRejPlus = []
        sigEffMinus = []
        bkgRejMinus = []
        normBkg = bgDisc.Integral()
        normSig = sigDisc.Integral()

        if not (normBkg>0 and normSig>0): return

        for i in range(1,1+bgDisc.GetNbinsX()):
            zeros.append(0.)
            bkgRej_v = bgDisc.Integral(1, i)
            bkgRej.append(bkgRej_v/float(normBkg))
            bkgRejPlus.append(  ROOT.TEfficiency.ClopperPearson(int(normBkg), int(bkgRej_v), 0.683,1))
            bkgRejMinus.append( ROOT.TEfficiency.ClopperPearson(int(normBkg), int(bkgRej_v), 0.683,0))
    
            sigEff_v = sigDisc.Integral(i+1, bgDisc.GetNbinsX())
            sigEff.append(sigEff_v/float(normSig))
            sigEffPlus. append( ROOT.TEfficiency.ClopperPearson(int(normSig), int(sigEff_v), 0.683,1))
            sigEffMinus.append( ROOT.TEfficiency.ClopperPearson(int(normSig), int(sigEff_v), 0.683,0))
        grCentral = ROOT.TGraphErrors(len(sigEff), array('d', sigEff), array('d', bkgRej), array('d',zeros), array('d', zeros))
        grPlus    = ROOT.TGraphErrors(len(sigEff), array('d', sigEffPlus), array('d', bkgRejPlus), array('d',zeros), array('d', zeros))
        grMinus   = ROOT.TGraphErrors(len(sigEff), array('d', sigEffMinus), array('d', bkgRejMinus), array('d',zeros), array('d', zeros))
        grCentral.GetXaxis().SetTitle('Signal efficiency')
        grCentral.GetYaxis().SetTitle('Background rejection')
        grCentral.SetMarkerColor(0)
        grCentral.SetMarkerStyle(0)
        grCentral.SetMarkerSize(0)
        grPlus.SetMarkerColor(0)
        grPlus.SetMarkerStyle(0)
        grPlus.SetMarkerSize(0)
        grMinus.SetMarkerColor(0)
        grMinus.SetMarkerStyle(0)
        grMinus.SetMarkerSize(0)

        return {'central':grCentral, 'plus':grPlus, 'minus':grMinus}
