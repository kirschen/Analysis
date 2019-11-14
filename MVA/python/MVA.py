import os, sys
import ROOT
ROOT.gROOT.SetBatch(True)
import random
import ctypes
import copy

from root_numpy                       import ROOT_VERSION
from helpers                          import *
from array                            import array
#from TTGammaEFT.Tools.user            import mva_directory
#from TTGammaEFT.Tools.user            import plot_directory as user_plot_directory
#from TTGammaEFT.Tools.cutInterpreter  import cutInterpreter

p_c_float  = ctypes.c_float  * 1
p_c_double = ctypes.c_double * 1
defaultObs = { "F":p_c_float(0.), "D":p_c_double(0.), "I":ctypes.c_int(0) }

# Logging
if __name__=="__main__":
    import Analysis.Tools.logger as logger
    logger = logger.get_logger("INFO", logFile = None )
else:
    import logging
    logger = logging.getLogger(__name__)
    ov = False

# Method settings
methodCutOpt                     = {}
methodCutOpt["type"]             = ROOT.TMVA.Types.kCuts
methodCutOpt["name"]             = "myCut"
methodCutOpt["lineColor"]        = ROOT.kRed
methodCutOpt["niceName"]         = "cutOptimized"
methodCutOpt["options"]          = ("!H","!V","VarTransform=None","CreateMVAPdfs=True","FitMethod=GA","EffMethod=EffSel","VarProp=NotEnforced","CutRangeMin=-1","CutRangeMax=-1")

addNeurons                       = [2,1]
methodMLP                        = {}
methodMLP["type"]                = ROOT.TMVA.Types.kMLP
methodMLP["name"]                = "MLP21"
methodMLP["lineColor"]           = ROOT.kBlack
methodMLP["drawStatUncertainty"] = True
methodMLP["niceName"]            = "MLP_{2,1}"
methodMLP["options"]             = ("!H","!V","VarTransform=Norm,Deco","NeuronType=sigmoid","NCycles=10000","TrainingMethod=BP","LearningRate=0.03", "DecayRate=0.01","HiddenLayers=INSERTHIDDENLAYERS","Sampling=0.3","SamplingEpoch=0.8","ConvergenceTests=1","CreateMVAPdfs=True","TestRate=10" )

methodBDT                        = {}
methodBDT["type"]                = ROOT.TMVA.Types.kBDT
methodBDT["name"]                = "BDT"
methodBDT["lineColor"]           = ROOT.kBlue
methodBDT["drawStatUncertainty"] = True
methodBDT["niceName"]            = "BDT"
#methodBDT["options"]             = ("!H","!V","NTrees=850","MinNodeSize=5%","MaxDepth=4","BoostType=AdaBoost","AdaBoostBeta=0.5","SeparationType=GiniIndex","nCuts=20","PruneMethod=NoPruning")
methodBDT["options"]             = ("!H","!V","NTrees=1000","BoostType=Grad","Shrinkage=0.20","UseBaggedBoost","GradBaggingFraction=0.5","SeparationType=GiniIndex","nCuts=500","PruneMethod=NoPruning","MaxDepth=5")

allMethods = {}
allMethods["BDT"]    = methodBDT
allMethods["cutOpt"] = methodCutOpt
allMethods["MLP"]    = methodMLP

class MVA:
    def __init__( self, signal, backgrounds, output_directory, plot_directory, selectionString, label="MVA", fractionTraining=0.5, overwrite=False, createPkl=True, nMax=-1 ):

#        self.year                = int(year)
        self.signal              = signal      # Sample object
        self.backgrounds         = backgrounds # list of Sample objects
        self.label               = label
        self.fractionTraining    = float(fractionTraining)
        self.overwrite           = overwrite
        self.createPkl           = createPkl
        self.nMax                = nMax
        self.setup               = {}
        self.method              = {}
        self.selectionString     = selectionString
        self.weightString        = "1"
        self.read_variables      = []
        self.mva_variables       = []
        self.calc_variables      = []
        self.output_directory    = os.path.join( output_directory if output_directory else mva_directory, self.label )
        self.dataFile            = os.path.join( self.output_directory, self.label + ".root" )
        self.mvaOutFile          = os.path.join( self.output_directory, self.label + "_MVAOutput.root" )
#        self.mvaWeightDir        = os.path.join( self.output_directory, self.label, "weights" )
        self.mvaWeightDir        = "weights"
        self.configFile          = self.dataFile.replace(".root", ".pkl")
        self.trainingSampleSizes = None
        self.plot_directory      = os.path.join( plot_directory if plot_directory else user_plot_directory, "MVA", self.label )

        self.tree                = None
        self.eListBkg            = None
        self.eListSig            = None
        self.eListBkgTraining    = None
        self.eListSigTraining    = None
        self.eListBkgTest        = None
        self.eListSigTest        = None

        randomSeed = 1
        random.seed( randomSeed )

        if not os.path.isdir( self.plot_directory ):
            os.makedirs( self.plot_directory )

        if not os.path.isdir( self.output_directory ):
            os.makedirs( self.output_directory )

        if not os.path.isdir( self.mvaWeightDir ):
            os.makedirs( self.mvaWeightDir )

    def setReadVariables( self, read_variables=[] ):
        # list of variablesnames to read from sample root files + type: [ name/type, ... ]
        self.read_variables = read_variables

    def setMVAVariables( self, mva_variables=[] ):
        # list of variablesnames to read from sample root files + type: [ name/type, ... ]
        self.mva_variables = mva_variables

    def setCalculateVariables( self, calc_variables=[] ):
        # list of tuples [ (name1, lambda x: ...), (name2, lambda x: ...) ]
        self.calc_variables = calc_variables

    #def setSelectionString( self, selectionString ):
     #   self.selectionString = cutInterpreter.cutString( selectionString ) if "-" in selectionString else selectionString

    def setWeightString( self, weightString ):
        self.weightString = weightString

    def createSetup( self ):

        self.setup["dataFile"]      = self.dataFile
        self.setup["preselection"]  = self.selectionString
        self.setup["obsFromInput"]  = self.read_variables
        self.setup["obsCalculated"] = self.calc_variables
        # probably these options should be changable in the future
        self.setup["plotTransformations"]         = [ "Id" ]#, "Deco", "PCA", "Gauss_Deco"]
        self.setup["makeCorrelationScatterPlots"] = False
        self.setup["plotMVAEffs"]                 = False #needs active X-forwarding since a QT Object is involved
        self.setup["TMVAOutputFile"]              = self.mvaOutFile
        self.setup["weightDir"]                   = self.mvaWeightDir
        self.setup["plot_directory"]              = self.plot_directory

        if self.createPkl:
            self.setup["dataSetConfigFile"] = self.configFile
            setupStripped                   = copy.deepcopy(self.setup)
            setupStripped["obsCalculated"]  = [ v[:-1] + ["removedFunction"] for v in self.calc_variables]
            pickle.dump( setupStripped, file( self.configFile, "w" ) )

    def getTrainingSampleSizes( self ):
        """ 
        finds nbBkg1,...,nBkgN such that nBkg1+...+nBkgN is maximal while respecting
        nBkg1+nBkg2+...+nBkgN<=nSigTraining, nBkg1:nBkg2:...:nBkgN=yBkg1:yBkg2:...:yBkgN
        and nBkg1<=self.fractionTraining*nBkg1Max, ...., self.fractionTraining*nBkgNMax<=nBkgNMax
        """
        maxSignalCount = int( self.fractionTraining * self.signal.count )
        assert maxSignalCount > 0, "Too few signal events. Training events: %i"%maxSignalCount

        maxBkgYield = float( max( [ b.yields for b in self.backgrounds ] ) )
        assert maxBkgYield > 0, "Maximum background yield non-positive: %f"%maxBkgYield

        maxTrainingEvents = [ int( self.fractionTraining * b.count ) for b in self.backgrounds ]
        for i, n in enumerate( maxTrainingEvents ):
            assert maxTrainingEvents > 0, "No training events found bkg sample nr. %i"%i

        weightList       = [ float( b.yields ) / int( self.fractionTraining * b.count ) for b in self.backgrounds ]
        maxWeightIndex   = weightList.index( max( weightList ) )
        maxAchievableBkg = [ int( self.fractionTraining * b.count * b.yields / self.backgrounds[maxWeightIndex].yields ) for b in self.backgrounds ]

        if sum( maxAchievableBkg ) < maxSignalCount:
            return { "backgrounds":maxAchievableBkg,"signal":sum(maxAchievableBkg) }
        else:
            fac = maxSignalCount / float( sum(maxAchievableBkg) )
            res = [ int( self.fractionTraining * b.count * b.yields / self.backgrounds[maxWeightIndex].yields * fac) for b in self.backgrounds ]
            return { "backgrounds":res, "signal":maxSignalCount }


    def prepareSamples( self ):

        if not self.overwrite and os.path.isfile( self.dataFile ):
            return

        for s in self.backgrounds + [self.signal]:

            # prepare additional variables
            s.yields = s.getYieldFromDraw( weightString=self.weightString, selectionString=self.selectionString )["val"]
            s.eList  = getEList( s.chain, self.selectionString )
            s.count  = s.eList.GetN()
            logger.info( "Found %i events for sample %s" %(s.count, s.name) )

            # use only needed branches
            s.chain.SetBranchStatus( "*", 0 )
            for v in [ x.split("/")[0] for x in self.read_variables ]:
                s.chain.SetBranchStatus( v, 1 )

        # calculate training sample sizes
        trainingSampleSizes = self.getTrainingSampleSizes()
        # determine randomized training events
        signalEvents               = getRandList( self.signal.count )
        self.signal.trainingEvents = [ self.signal.eList.GetEntry(j) for j in signalEvents[:trainingSampleSizes["signal"]] ]

        maxNTestEvents             = min( self.signal.count, int( trainingSampleSizes["signal"] / self.fractionTraining ) )
        self.signal.testEvents     = [ signal.eList.GetEntry(j) for j in signalEvents[trainingSampleSizes["signal"]:maxNTestEvents] ]

        for i, b in enumerate( self.backgrounds ):
            backgroundEvents = getRandList( b.count ) 
            b.trainingEvents = [ b.eList.GetEntry(j) for j in backgroundEvents[:trainingSampleSizes["backgrounds"][i]] ]
            maxNTestEvents   = min( b.count, 2*trainingSampleSizes["backgrounds"][i] )
            b.testEvents     = [ b.eList.GetEntry(j) for j in backgroundEvents[trainingSampleSizes["backgrounds"][i]:maxNTestEvents] ]


    def createTrainingSample( self ):
        """ 
        create ROOT::TTree objects from a signal (TChain and event lists for test and training) 
        and a list of backgrounds. self.read_variables and self.calc_variables specify the observables.
        """

        if not self.overwrite and os.path.isfile( self.dataFile ):
            return

        self.tree = ROOT.TTree( "Events", "Train and test tree" )

        # construct dataset
        obsType     = {}
        observables = {}
        for vn in self.read_variables:
            n              = getObsName(vn)
            obsType[n]     = getObsType(vn)
            observables[n] = copy.deepcopy(defaultObs[obsType[n]])

        for c in [self.signal.chain] + [b.chain for b in self.backgrounds]:
            for k in observables.keys():
                c.SetBranchAddress( k, observables[k] )

        for k in observables.keys():
            self.tree.Branch(k, observables[k], k+"/"+obsType[k])

        i_signal     = copy.deepcopy(defaultObs["I"])
        i_isTraining = copy.deepcopy(defaultObs["I"])
        self.tree.Branch( "isSignal",   ctypes.addressof( i_signal ),     "isSignal/I")
        self.tree.Branch( "isTraining", ctypes.addressof( i_isTraining ), "isTraining/I")

        addObs = {}
        for vn in [ v[0] for v in self.calc_variables ]:
            n          = getObsName(vn)
            obsType[n] = getObsType(vn)
            addObs[v]  = copy.deepcopy(defaultObs[obsType[v]])
            self.tree.Branch( v, ctypes.addressof( addObs[v] ), v+"/"+obsType[v] )

        i_signal.value     = 1
        i_isTraining.value = 1
        fillTree( self.tree, self.signal.chain, self.signal.trainingEvents, self.calc_variables, self.nMax )

        i_isTraining.value = 0
        fillTree( self.tree, self.signal.chain, self.signal.testEvents, self.calc_variables, self.nMax )

        i_signal.value = 0
        for j, b in enumerate( self.backgrounds ):
            i_isTraining.value = 1
            fillTree( self.tree, b.chain, b.trainingEvents, self.calc_variables, self.nMax )
            i_isTraining.value = 0
            fillTree( self.tree, b.chain, b.testEvents, self.calc_variables, self.nMax ) 

        self.eListBkg          = getEList( self.tree, "isSignal==0&&"                + self.selectionString, "eListBkg" )        
        self.eListSig          = getEList( self.tree, "isSignal==1&&"                + self.selectionString, "eListSig" )
        self.eListBkgTraining  = getEList( self.tree, "isTraining==1&&isSignal==0&&" + self.selectionString, "eListBkgTraining" )
        self.eListSigTraining  = getEList( self.tree, "isTraining==1&&isSignal==1&&" + self.selectionString, "eListSigTraining" )
        self.eListBkgTest      = getEList( self.tree, "isTraining==0&&isSignal==0&&" + self.selectionString, "eListBkgTest" )
        self.eListSigTest      = getEList( self.tree, "isTraining==0&&isSignal==1&&" + self.selectionString, "eListSigTest" )

        f = ROOT.TFile( self.dataFile, "recreate" )
        self.tree.Write()
        self.eListBkg.Write()
        self.eListSig.Write()
        self.eListBkgTraining.Write()
        self.eListSigTraining.Write()
        self.eListBkgTest.Write()
        self.eListSigTest.Write()
        f.Close()

    def prepareSampleSettings( self, read_variables=[], calc_variables=[], selectionString="(1)", weightString="1" ):
        self.setReadVariables( read_variables=read_variables )
        self.setCalculateVariables( calc_variables=calc_variables )
        #self.setSelectionString( selectionString )
        self.setWeightString( weightString )
        if self.createPkl:
            self.createSetup()

    def createSample( self ):
        self.prepareSamples()
        self.createTrainingSample()

    def prepareMVASettings( self, mva_variables=[], mva_settings=[], type="BDT" ):
        self.setMVAVariables( mva_variables=mva_variables )
        self.createMethod( mva_settings=mva_settings, type=type )

    def loadDatasetForTMVA( self ):

        if not self.tree:
            self.tree             = getAnyObjFromFile( self.dataFile, 'Events' )

        if not self.eListBkg:
            self.eListBkg         = getAnyObjFromFile( self.dataFile, 'eListBkg' )
        if not self.eListSig:
            self.eListSig         = getAnyObjFromFile( self.dataFile, 'eListSig' )

        if not self.eListBkgTraining:
            self.eListBkgTraining = getAnyObjFromFile( self.dataFile, 'eListBkgTraining' )
        if not self.eListSigTraining:
            self.eListSigTraining = getAnyObjFromFile( self.dataFile, 'eListSigTraining' )

        if not self.eListBkgTest:
            self.eListBkgTest     = getAnyObjFromFile( self.dataFile, 'eListBkgTest' )
        if not self.eListSigTest:
            self.eListSigTest     = getAnyObjFromFile( self.dataFile, 'eListSigTest' )

        return { 'tree':self.tree,
                 'eListBkg':self.eListBkg,
                 'eListSig':self.eListSig, 
                 'eListBkgTraining':self.eListBkgTraining,
                 'eListSigTraining':self.eListSigTraining,
                 'eListBkgTest':self.eListBkgTest,
                 'eListSigTest':self.eListSigTest,
               }


#    def getYield( self, readerInstance, method, cut, nnCutVal, weight='weight', weightFunc=None ):

#        res = 0.
#        l   = getEList( self.tree, cut )

#        for i in range( l.GetN() ):
#            self.tree.GetEntry( l.GetEntry(i) )
#            inputs = ROOT.std.vector('float')()
#    
#            for var in self.mva_variables:
#                val = self.tree.GetLeaf(var).GetValue()
#                inputs.push_back(val)

#            w = weightFunc(self.tree) if weightFunc else self.tree.GetLeaf(weight).GetValue()

#            if method['type'] != ROOT.TMVA.Types.kCuts:
#                nno = readerInstance.EvaluateMVA( inputs, method['name'] )
#                if nno >= nnCutVal: res += w
#            else:
#                nno = readerInstance.EvaluateMVA( inputs, method['name'], nnCutVal ) if nnCutVal>=0 else 1
#                if nno: res += w

#        del l
#        return res

    def createMethod( self, mva_settings, type ):

        if type=="MLP":
            nn_layers    = [ len( self.mva_variables ) + i for i in addNeurons ]
            hiddenLayers = ",".join( [ str(i) for i in nn_layers ] )
            self.method  = allMethods[type]
            for options in self.method["options"]:
                if "INSERTHIDDENLAYERS" in options:
                    options.replace( "INSERTHIDDENLAYERS", hiddenLayers )
                    break
        else:
            self.method  = allMethods[type]

        self.mva_settings = mva_settings

#        self.setup["methodConfigs"]      = copy.deepcopy([self.method])
#        self.setup["TMVAFactoryOptions"] = self.mva_settings

    def runMVA( self ):

        data = self.loadDatasetForTMVA()
        rootGDirectory = ROOT.gDirectory.CurrentDirectory().GetName()+":/"

        ROOT.TMVA.Tools.Instance()
        ROOT.TMVA.gConfig().GetIONames().fWeightFileDir = self.mvaWeightDir
        ROOT.TMVA.gConfig().GetVariablePlotting().fNbinsXOfROCCurve = 200
        ROOT.TMVA.gConfig().GetVariablePlotting().fMaxNumOfAllowedVariablesForScatterPlots = 2
        
        fout    = ROOT.TFile( self.mvaOutFile, "RECREATE" )
        factory = ROOT.TMVA.Factory( "TMVAClassification", fout, ":".join(self.mva_settings) )
        factory.DeleteAllMethods()

        dataloader = ROOT.TMVA.DataLoader('.') if ROOT_VERSION >= '6.07/04' else factory

        varType = {}
        for vn in self.read_variables + [ v[0] for v in self.calc_variables ]:
            varType[getObsName(vn)] = getObsType(vn)

        for v in self.mva_variables:
            print getObsName(v), varType[v]
            dataloader.AddVariable(getObsName(v), varType[v])

        bkgTestTree  = data["tree"].CopyTree("isTraining==0&&isSignal==0")
        sigTestTree  = data["tree"].CopyTree("isTraining==0&&isSignal==1")
        bkgTrainTree = data["tree"].CopyTree("isTraining==1&&isSignal==0")
        sigTrainTree = data["tree"].CopyTree("isTraining==1&&isSignal==1")
        dataloader.AddBackgroundTree( bkgTrainTree, 1.0, "Training" )
        dataloader.AddBackgroundTree( bkgTestTree,  1.0, "Test" )
        dataloader.AddSignalTree(     sigTrainTree, 1.0, "Training" )
        dataloader.AddSignalTree(     sigTestTree,  1.0, "Test" )

        args = (dataloader, self.method["type"], self.method["name"], ":".join(self.method["options"]))
        BookMethod = factory.BookMethod if ROOT_VERSION >= '6.07/04' else ROOT.TMVA.Factory.BookMethod
        methodBook = BookMethod(*args)

        factory.TrainAllMethods()
        factory.TestAllMethods()
        factory.EvaluateAllMethods()

        fout.Close()


    def getFOMPlot( self, bgDisc, sigDisc ):

        if not bgDisc.GetNbinsX()==sigDisc.GetNbinsX():
            return

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
        grCentral.SetLineColor(ROOT.kBlack)
        grCentral.SetMarkerStyle(0)
        grCentral.SetMarkerSize(0)
        grPlus.SetMarkerColor(0)
        grPlus.SetLineColor(ROOT.kBlue)
        grPlus.SetMarkerStyle(0)
        grPlus.SetMarkerSize(0)
        grMinus.SetMarkerColor(0)
        grMinus.SetLineColor(ROOT.kBlue)
        grMinus.SetMarkerStyle(0)
        grMinus.SetMarkerSize(0)

        return {'central':grCentral, 'plus':grPlus, 'minus':grMinus}


    def plotEvaluation( self ):

        stuff=[]
        mlpa_canvas = ROOT.TCanvas("mlpa_canvas", "Network analysis", 1200, 800)
        mlpa_canvas.SetFillColor(ROOT.kWhite)
        mlpa_canvas.Divide(2,2)
        nbinsFine = 2000

        for i, treeName in enumerate(["Test", "Train"]):
            l = ROOT.TLegend( .65, .80, 0.99, 0.99 )
            t = getAnyObjFromFile( self.mvaOutFile, treeName+"Tree" )
            mlpa_canvas.cd( 3+i )
            l.SetFillColor( ROOT.kWhite )
            l.SetShadowColor( ROOT.kWhite )
            l.SetBorderSize(1)

            self.method["hsig"+treeName]        = ROOT.TH1F( "hsig"+treeName,        "hsig"+treeName,        20, 0, 1.)
            self.method["hbg" +treeName]        = ROOT.TH1F( "hbg" +treeName,        "hbg" +treeName,        20, 0, 1.)
            self.method["hsig"+treeName+"Fine"] = ROOT.TH1F( "hsig"+treeName+"Fine", "hsig"+treeName+"Fine", nbinsFine, 0, 1.)
            self.method["hbg" +treeName+"Fine"] = ROOT.TH1F( "hbg" +treeName+"Fine", "hbg" +treeName+"Fine", nbinsFine, 0, 1.)

            t.Draw( self.method["name"]+">>+hsig"+treeName,        "classID==1", "goff")
            t.Draw( self.method["name"]+">>+hbg"+treeName,         "classID==0", "goff")
            t.Draw( self.method["name"]+">>+hsig"+treeName+"Fine", "classID==1", "goff")
            t.Draw( self.method["name"]+">>+hbg"+treeName+"Fine",  "classID==0", "goff")

            self.method["hsig"+treeName].SetLineColor(ROOT.kRed)
            self.method["hsig"+treeName].SetFillStyle(3003)
            self.method["hsig"+treeName].SetFillColor(ROOT.kRed)
            self.method["hsig"+treeName].SetStats(0)
            self.method["hsig"+treeName].SetMarkerSize(0)
            self.method["hsig"+treeName].SetMarkerStyle(0)
            self.method["hsig"+treeName].SetMarkerColor(ROOT.kRed)

            self.method["hbg"+treeName].SetLineColor(ROOT.kBlue)
            self.method["hbg"+treeName].SetFillStyle(3008)
            self.method["hbg"+treeName].SetFillColor(ROOT.kBlue)
            self.method["hbg"+treeName].SetMarkerSize(0)
            self.method["hbg"+treeName].SetMarkerStyle(0)
            self.method["hbg"+treeName].SetMarkerColor(ROOT.kBlue)
            self.method["hbg"+treeName].SetStats(0)
            self.method["hbg"+treeName].SetTitle("Classifier "+self.method["name"])
            self.method["hbg"+treeName].GetXaxis().SetTitle("Discriminator")
            self.method["hbg"+treeName].GetYaxis().SetRangeUser(0, 1.2*max(self.method["hbg"+treeName].GetMaximum(), self.method["hsig"+treeName].GetMaximum()))

            self.method["hbg"+treeName].Draw()
            self.method["hsig"+treeName].Draw("same")

            l.AddEntry(self.method["hbg"+treeName],  "Background "+treeName.replace("Tree",""))
            l.AddEntry(self.method["hsig"+treeName], "Signal "+treeName.replace("Tree",""))

            l.Draw()
            stuff.append(l)
            t.IsA().Destructor(t)
            del t

        pad = mlpa_canvas.cd(1)
        pad.SetGrid()
        l5  = ROOT.TLegend(.16, .13, 0.5, 0.35)
        opt = ""

        histFOM = getAnyObjFromFile( self.mvaOutFile, "MVA_"+self.method["name"]+"_rejBvsS" )
        stuff.append(histFOM)
        histFOM.SetStats(False)
        histFOM.SetLineColor(   self.method["lineColor"] )
        histFOM.SetLineWidth( 2 )
        histFOM.SetMarkerColor( self.method["lineColor"] )
        histFOM.SetMarkerStyle(0)
        histFOM.SetTitle("FoM "+self.method["name"])
        histFOM.Draw(opt)
        histFOM.GetXaxis().SetTitle('Signal efficiency')
        histFOM.GetYaxis().SetTitle('Background rejection')
        opt="same"
        l5.AddEntry(histFOM,self.method["niceName"])

        l5.SetFillColor(0)
        l5.SetShadowColor(ROOT.kWhite)
        l5.SetBorderSize(1)
#        l5.Draw()

        pad = mlpa_canvas.cd(2)
        pad.SetGrid()
        l3 = ROOT.TLegend(.16, .13, 0.5, 0.5)
        l3.SetFillColor(ROOT.kWhite)
        l3.SetShadowColor(ROOT.kWhite)
        l3.SetBorderSize(1)
        opt="AL"

#        self.method["FOMFromFile"] = getAnyObjFromFile( self.mvaOutFile, "MVA_"+self.method["name"]+"_rejBvsS" )
#        self.method["FOMFromFile"].SetStats(False)
#        self.method["FOMFromFile"].SetLineColor( self.method["lineColor"] )

        self.method["FOMFromTree"] = self.getFOMPlot( self.method["hbgTestFine"], self.method["hsigTestFine"] )
        self.method["FOMFromTree"]["central"].SetLineColor( self.method["lineColor"] )
        self.method["FOMFromTree"]["central"].SetTitle("FoM "+self.method["name"])

        coord = [ 0, 0.8, 0.5, 1.0 ]
        self.method["FOMFromTree"]["central"].GetXaxis().SetRangeUser(coord[0],coord[2])
        self.method["FOMFromTree"]["central"].GetYaxis().SetRangeUser(coord[1],coord[3])
        self.method["FOMFromTree"]["central"].Draw(opt)

        if not self.method["type"] == ROOT.TMVA.Types.kCuts:
            l3.AddEntry( self.method["FOMFromTree"]["central"], self.method["niceName"], "LP" )

        opt="L"
        if self.method.has_key("drawStatUncertainty") and self.method["drawStatUncertainty"]:
            if not self.method["type"]==ROOT.TMVA.Types.kCuts:
                self.method["FOMFromTree"]["plus"].SetLineStyle(3)
                self.method["FOMFromTree"]["minus"].SetLineStyle(3)
                self.method["FOMFromTree"]["plus"].SetLineWidth(2)
                self.method["FOMFromTree"]["minus"].SetLineWidth(2)
                self.method["FOMFromTree"]["plus"].Draw(opt)
                self.method["FOMFromTree"]["minus"].Draw(opt)
                l3.AddEntry(self.method["FOMFromTree"]["plus"], self.method["niceName"]+" (#pm 1#sigma)", "LP")

#        latexArgs = []
#        t = getAnyObjFromFile( self.mvaOutFile, "TestTree" )
#        fom_plots = {}

#        for fom_var, fom_var_range, fom_var_color in self.setup["fom_plot_vars"]:
#            fom_plots[fom_var] = self.getFOMPlot( getPlot(t,"classID==0", fom_var, [nbinsFine] +fom_var_range), getPlot(t, "classID==1", fom_var, [nbinsFine] + fom_var_range) )["central"]
#            if fom_plots[fom_var]:
#                fom_plots[fom_var].SetLineColor( fom_var_color )
#                fom_plots[fom_var].Draw("L")
#                l3.AddEntry(fom_plots[fom_var], fom_var, "LP")#

#            for k in fom_plots.keys():
#                fom_plots[k].Draw("L")

#        l3.Draw()

        for ending in [ ".pdf", ".png", ".root" ]:
            mlpa_canvas.Print( os.path.join( self.plot_directory, "validation" + ending ) )

        del mlpa_canvas

    def __del__( self ):
        del self.tree
        del self.eListBkg
        del self.eListSig
        del self.eListBkgTraining
        del self.eListSigTraining
        del self.eListBkgTest
        del self.eListSigTest

 



