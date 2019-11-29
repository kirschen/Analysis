# Still to do:
# remove single bins in region histograms
# sort region histograms
# nuisance histograms w/ +-x sigma up/down
#

""" 
Extracting pre- and post-fit information.
Parts stolen from:
https://github.com/HephySusySW/Workspace/blob/94X-master/DegenerateStopAnalysis/python/tools/sysTools.py
and
https://github.com/HephySusySW/Workspace/blob/94X-master/DegenerateStopAnalysis/python/tools/degTools.py

Uses information of the *.txt, *.shapeCard.txt, shapeCard_FD.root and _nuisances*.txt files
"""

# Standard imports
import os
import ROOT
ROOT.gROOT.SetBatch(True)
import math
import copy
import shutil
import uuid

from Analysis.Tools.u_float import u_float

from RootTools.core.standard import *
from RootTools.plot.helpers  import copyIndexPHP

# Logging
import logging
logger = logging.getLogger(__name__)


class CombineResults:

    def __init__( self, cardFile, plotDirectory, year, bkgOnly=False ):

        if not isinstance( cardFile, str ):
            raise ValueError( "CardFile input needs to be a string with the path to the cardFile" )
        if not cardFile.endswith(".txt") or "shapeCard" in cardFile or not os.path.exists( cardFile ):
            raise ValueError( "Please provide the path to the *.txt cardfile! Got: %s"%cardFile )

        self.year          = year
        self.bkgOnly       = bkgOnly
        self.cardFile      = cardFile

        self.shapeFile      = cardFile.replace(".txt","_shapeCard.txt" )
        if not os.path.exists( self.shapeFile ):
            logger.warning( "Shape card not found: %s"%self.shapeFile )
            logger.warning( "Continuing with limited options!" )
            self.shapeFile = None

        self.shapeRootFile = cardFile.replace(".txt","_shape.root" )
        if not os.path.exists( self.shapeRootFile ):
            logger.warning( "Root file of fit result not found: %s"%self.shapeRootFile )
            logger.warning( "Continuing with limited options!" )
            self.shapeRootFile = None

        self.rootCardFile = cardFile.replace(".txt","_shapeCard.root" )
        if not os.path.exists( self.rootCardFile ):
            logger.warning( "Root card file of fit result not found: %s"%self.rootCardFile )
            logger.warning( "Continuing with limited options!" )
            self.rootCardFile = None

        self.rootFile      = cardFile.replace(".txt","_shapeCard_FD.root" )
        if not os.path.exists( self.rootFile ):
            logger.warning( "Root file of fit result not found: %s"%self.rootFile )
            logger.warning( "Continuing with limited options!" )
            self.rootFile = None

        self.nuisanceFile  = cardFile.replace(".txt","_shapeCard_nuisances_full.txt")
        if not os.path.exists( self.nuisanceFile ):
            logger.warning( "Nuisance file of fit result not found: %s"%self.nuisanceFile )
            logger.warning( "Continuing with limited options!" )
            self.nuisanceFile = None

        self.plotDirectory = plotDirectory
        if not os.path.isdir( self.plotDirectory ):
            os.makedirs( self.plotDirectory )

        # set some defaults. If a method gets some of these variables, they will be filled
        # this safes some time if they are used multiple times
        self.tRootFile           = None # needed otherwise python looses the pointer to the root file
        self.binList             = None
        self.binLabels           = None
        self.processes           = None
        self.processList         = None
        self.fitResults          = None
        self.fittedUncertainties = None
        self.constrain           = None
        self.observations        = None
        self.nuisances           = None
        self.correlationHisto    = None
        self.estimates           = {"preFit":None, "postFit":None}
        self.uncertainties       = {"preFit":None, "postFit":None}
        self.pulls               = {"preFit":None, "postFit":None}
        self.covarianceHistos    = {"preFit":None, "postFit":None}
        self.regionHistos        = {"preFit":{"all":None}, "postFit":{"all":None}}
        self.sortedRegionHistos  = {"preFit":{"all":None}, "postFit":{"all":None}}
        self.regionFile          = {"preFit":{"all":None}, "postFit":{"all":None}}

#    def __private( self ):
#    def public( self ):

    def __getFitObject( self, key=None ):
        """ get the fit objects
        """
        # return safed fitResult if available
        if self.fitResults:
            if key and key in self.fitResults.keys(): return self.fitResults[key]
            elif not key:                             return self.fitResults

        if not self.rootFile:
            raise ValueError( "Root file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

        if not self.tRootFile:
            self.tRootFile = ROOT.TFile( self.rootFile, "READ")
        fits   = ["fit_b", "fit_s", "norm_prefit", "norm_fit_s", "norm_fit_b", "nuisances_prefit", "nuisances_prefit_res", "shapes_prefit", "shapes_fit_b", "shapes_fit_s", "overall_total_covar"]
        result = {}
        for fit in fits:
            result[fit] = copy.copy(self.tRootFile.Get(fit) )
        self.fitResults = result

        if key: return self.fitResults[key]
        else:   return self.fitResults

    def __filter( self, filterDict, var=None ):
        if not isinstance( filterDict, dict ) or not var: return filterDict
        return { key:val for key, val in filterDict.items() if key==var}
            
    def __filterDict( self, filterDict, bin=None, estimate=None, nuisance=None, systOnly=False ):
        filterDict = self.__filter( filterDict, var=bin )
        if not isinstance( filterDict, dict ): return filterDict
        for b, b_dict in filterDict.items():
            filterDict[b] = self.__filter( b_dict, var=estimate )
            if not isinstance( filterDict[b], dict ): continue
            for e, e_dict in filterDict[b].items():
                filterDict[b][e] = self.__filter( e_dict, var=nuisance )
                if not isinstance( filterDict[b][e], dict ): continue
                for n, nui in filterDict[b][e].items():
                    if systOnly and ("Stat" in nui or "prop" in nui):
                        del filterDict[b][e][n]
        return filterDict

    def __getConstrain( self, nuisance ):

        # just run over it once, safe the entries in a dictionary, use it if you need it
        if self.constrain and nuisance in self.constrain.keys():
            return self.constrain[nuisance]

        if not self.nuisanceFile:
            raise ValueError( "Nuisance file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

        nuisanceList = self.getNuisancesList()
        with open( self.nuisanceFile ) as f:
            for line in f:
                if not line.split(): continue
                if line.split()[0] not in nuisanceList: continue
                self.constrain[line.split()[0]] = float(line.split(",")[0 if self.bkgOnly else 1].split()[0].replace("*","").replace("!",""))

        if nuisance not in self.constrain.keys():
            # Sometimes a bin is not found in the nuisance file because its yield is 0
            self.constrain[nuisance] = 0.

        return self.constrain[nuisance]

    def __getFittedUncertainty( self, nuisance ):

        # just run over it once, safe the entries in a dictionary, use it if you need it
        if self.fittedUncertainties and nuisance in self.fittedUncertainties.keys():
            return self.fittedUncertainties[nuisance]

        if not self.nuisanceFile:
            raise ValueError( "Nuisance file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

        nuisanceList        = self.getNuisancesList()
        fittedUncertainties = {}
        with open(self.nuisanceFile) as f:
            for line in f:
                if not line.split(): continue
                if line.split()[0] not in nuisanceList: continue
                fittedUncertainties[line.split()[0]] = float(line.split(",")[0 if self.bkgOnly else 1].split()[0].replace("!","").replace("*",""))

        self.fittedUncertainties = fittedUncertainties

        if nuisance not in self.fittedUncertainties.keys():
            # Sometimes a bin is not found in the nuisance file because its yield is 0
            self.fittedUncertainties[nuisance] = 0.

        return self.fittedUncertainties[nuisance]

    def __getUncertaintiesFromCard( self, estimate, nuisance, bin, postFit=False ):
        binList   = self.getBinList( unique=False )
        estimates = self.getProcessList( unique=False )
        unc       = 0
        with open( self.cardFile ) as f:
            for line in f:
                if not line.split():            continue
                if line.split()[0] != nuisance: continue
                for i_bin, _bin in enumerate(binList):
                    if _bin != bin: continue
                    if estimates[i_bin] != estimate: continue
                    try:
                        unc = float(line.split()[2:][i_bin])-1
                        break
                    except:
                        return 0. # muted bin or -, cannot be converted to float
        
        return self.__getFittedUncertainty( nuisance ) * unc if postFit else unc


    def __getSubKey( self, plotBins=None, plotChannel=None ):
        subkey = "all"
        if   plotBins and plotChannel: subkey = "_".join(plotBins + [plotChannel])
        elif plotBins:                 subkey = "_".join(plotBins)
        elif plotChannel:              subkey = plotChannel
        return subkey

    def __getNuisanceYields( self, nuisance, postFit=False ):
        if nuisance not in unc["Bin0"]["signal"].keys():
            raise ValueError("Nuisance not in cardfile: %s. Use one of [%s]"%(nuisance, ", ".join(unc["Bin0"]["signal"].keys())))
        return { bin:self.__getNuisanceBinYield( nuisance=nuisance, bin=b, postFit=postFit ) for b in self.getBinList( unique=True ) }

    def __getNuisanceBinYield( self, nuisance, bin, postFit=False ):
        yields    = self.getEstimates(     postFit=postFit, bin=bin )
        unc       = self.getUncertainties( postFit=postFit, bin=bin, systOnly=False )
        processes = self.getProcessesPerBin( bin=bin )
        y, yup, ydown = 0, 0, 0
        for p in processes:
            yproc  = yields[p].val if p in yields.keys() else 0
            uproc  = unc[p][uncName]
            y     += yproc
            yup   += yproc*(1+uproc)
            ydown += yproc*(1-uproc)
        return {"up":yup, "down":ydown, "relUp":yup/y, "relDown":ydown/y, "yield":y}

    def getBinList( self, unique=False ):
        # ordered list of bins
        # return safed binList if available
        if self.binList:
            if unique:
                binList = list(set(self.binList))
                binList.sort()
                return binList
            return self.binList

        second = False
        with open( self.cardFile ) as f:
            for line in f:
                if len(line.split())==0: continue
                if line.split()[0].lower() == "bin" and not second:
                    second = True
                elif line.split()[0].lower() == "bin" and second:
                    binList = line.split()[1:]
                    self.binList = copy.copy(binList)
                    break

        if unique:
            binList = list(set(binList))
            binList.sort()
            return binList

        return self.binList

    def getBinLabels( self ):
        # return safed binList if available
        if self.binLabels: return self.binLabels

        binLabels = []
        with open( self.cardFile ) as f:
            for line in f:
                if line.startswith("# Bin"):
                    binLabels.append(line.split(": ")[1].split("\n")[0])
                elif line.startswith("#Muted"):
                    binLabels.append(line.split(": ")[2].split("\n")[0])
        self.binLabels = binLabels

        return self.binLabels

    def getNuisancesList( self, systOnly=False ):

        if self.nuisances:
            if systOnly:
                for i, n in enumerate(self.nuisances):
                    if "prop" in n or "Stat" in n:
                        return self.nuisances[:i]
            return self.nuisances

        fit       = self.__getFitObject( key="fit_b" if self.bkgOnly else "fit_s" )
        nuisance  = fit.floatParsInit()
        nuisances = []
        iter  = nuisance.createIterator()
        var   = iter.Next()

        while var:
            if var.GetName() != "r":
                nuisances.append( var.GetName() )
            var = iter.Next()

        self.nuisances = nuisances

        if systOnly:
            for i, n in enumerate(self.nuisances):
                if "prop" in n or "Stat" in n:
                    return self.nuisances[:i]

        return self.nuisances

    def getProcessList( self, unique=False ):
        # ordered list of processes over all bins
        # return safed binList if available
        if self.processList:
            if unique:
                processList = list(set(self.processList))
                processList.sort()
                return processList
            return self.processList

        if self.processList: return self.processList

        with open( self.cardFile ) as f:
            for line in f:
                if len(line.split())==0: continue
                if line.split()[0] == "process":
                    processList      = line.split()[1:]
                    self.processList = copy.copy(processList)
                    break

        if unique:
            processList = list(set(processList))
            processList.sort()
            return processList
        return self.processList

    def getProcessesPerBin( self, bin=None ):
        # return safed binList if available
        if self.processes:
            if bin: return self.processes[bin]
            return self.processes

        i           = 0
        bins        = self.getBinList( unique=True )
        procDict = {}

        with open( self.cardFile ) as f:
            for line in f:
                if len(line.split())==0: continue
                if line.split()[0] == "process":
                    if not self.processList:
                        self.processList = line.split()[1:]
                    # complex syntax needed to get the right order, set() mixes it up
                    procList = []
                    for proc in line.split()[i+1:]:
                        if proc not in procList:
                            procList.append(proc)
                        else:
                            procDict.update( {bins[i]:procList} )
                            procList = [proc]
                            i += 1
                    procDict.update( {bins[i]:procList} )
                    break
        self.processes = procDict
        if bin: return self.processes[bin]
        return self.processes

    def getPulls( self, nuisance=None, postFit=False ):
        # return safed pulls if available
        key = "postFit" if postFit else "preFit"
        if self.pulls[key]:
            if nuisance: return self.pulls[key][nuisance]
            else:        return self.pulls[key]

        fit   = self.__getFitObject( key="fit_b" if self.bkgOnly else "fit_s" )
        pull  = fit.floatParsFinal() if postFit else fit.floatParsInit()
        pulls = {}
        iter  = pull.createIterator()
        var   = iter.Next()

        while var:
            pulls.update( { var.GetName():u_float(var.getValV(), var.getError()) } )
            var = iter.Next()
        self.pulls[key] = pulls
        if nuisance: return self.pulls[key][nuisance]
        else:        return self.pulls[key]


    def getUncertainties( self, bin=None, estimate=None, nuisance=None, postFit=False, systOnly=False ):
        # return safed uncertainties if available
        key = "postFit" if postFit else "preFit"
        if self.uncertainties[key]:
            if bin or estimate or nuisance or systOnly:
                return self.__filterDict( self.uncertainties[key], bin=bin, estimate=estimate, nuisance=nuisance, systOnly=systOnly )
            else:
                return self.uncertainties[key]
        uncertainties = {}
        allUnc        = self.getNuisancesList( systOnly=systOnly )
        allEst        = self.getProcessesPerBin()
        for b in allEst.keys():
            uncertainties[b] = {}
            for est in allEst[b]:
                uncertainties[b][est] = {}
                for unc in allUnc:
                    uncertainties[b][est][unc] = self.__getUncertaintiesFromCard( estimate=est, nuisance=unc, bin=b, postFit=postFit )
        self.uncertainties[key] = uncertainties

        if bin or estimate or nuisance or systOnly:
            return self.__filterDict( self.uncertainties[key], bin=bin, estimate=estimate, nuisance=nuisance, systOnly=systOnly )
        else:
            return self.uncertainties[key]

    def getObservation( self, bin=None ):
        # return safed observations if available
        if self.observations:
            if bin and bin in self.observations.keys():
                return self.observations[bin]
            else:
                return self.observations

        res          = {}
        binList      = self.getBinList( unique=True )
        with open( self.cardFile ) as f:
            for line in f:
                if len(line.split())==0: continue
                if line.split()[0] == "observation":
                    for i_bin, _bin in enumerate(binList):
                        try:    res[_bin] = float(line.split()[1:][i_bin])
                        except: res[_bin] = 0.
        self.observations = res

        if bin not in self.observations.keys():
            self.observations[bin] = 0

        if bin: return self.observations[bin]
        else:   return self.observations

    def getEstimates( self, postFit=False, bin=None, estimate=None ):
        key    = "postFit" if postFit else "preFit"
        if self.estimates[key]:
            if bin or estimate:
                return self.__filterDict( self.estimates[key], bin=bin, estimate=estimate )
            else:
                return self.estimates[key]

        regionHistos = self.getRegionHistos( postFit=postFit, plotBins=None, plotChannel=None, sorted=False )
        processes    = set(self.getProcessList())
        yields       = {}
        tmp          = {}
        for est, h in regionHistos.iteritems():
            if est not in processes: continue
            tmp[est] = {}
            for i in range(h.GetNbinsX()):
                y = h.GetBinContent(i+1)
                e = h.GetBinError(i+1) # Attention, this is the full error, not only MC statistics! Fixme
                tmp[est]["Bin%i"%i] = u_float( y, e )
                yields["Bin%i"%i]    = {}

        # stupid restructuring to make it compatible w/ other functions
        for b in yields.keys():
            for est in tmp.keys():
                yields[b][est] = tmp[est][b]

        self.estimates[key] = yields

        if bin or estimate:
            return self.__filterDict( self.estimates[key], bin=bin, estimate=estimate )
        else:
            return self.estimates[key]

    def getNuisanceHistos( self, postFit=False, plotBins=None, plotChannel=None, nuisance=None ):
        nuisanceYields = self.__getNuisanceYields( nuisance, postFit=postFit )
        # create histogram
        hists = self.getRegionHistos( postFit=postFit, plotBins=None, plotChannel=None, sorted=False )
        nuisanceHistUp   = hists[hists.keys()[0]].Clone()
        nuisanceHistDown = hists[hists.keys()[0]].Clone()
        for b, nDict in nuisanceYields.iteritems():
            i = int(b.split("Bin")[1])
            nuisanceHistUp.SetBinContent(   i+1, nDict["up"] )
            nuisanceHistDown.SetBinContent( i+1, nDict["down"] )
        nuisanceHistUp.style        = styles.lineStyle( ROOT.kSpring-1, width=3 )
        nuisanceHistDown.style      = styles.lineStyle( ROOT.kOrange+7, width=3 )
        nuisanceHistUp.legendText   = nuisance + " (+1#sigma)"
        nuisanceHistDown.legendText = nuisance + " (-1#sigma)"
        return { nuisance:{"up":nuisanceHistUp, "down":nuisanceHistDown} }

    def getRegionHistos( self, postFit=False, plotBins=None, plotChannel=None, sorted=False, nuisance=None ):

        if not self.rootFile:
            raise ValueError( "Root file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

        key    = "postFit" if postFit else "preFit"
        subkey = self.__getSubKey( plotBins=plotBins, plotChannel=plotChannel )

        if sorted and subkey in self.sortedRegionHistos[key].keys() and self.sortedRegionHistos[key][subkey]:
            return self.sortedRegionHistos[key][subkey]
        elif not sorted and subkey in self.regionHistos[key].keys() and self.regionHistos[key][subkey]:
            return self.regionHistos[key][subkey]

        if postFit:
            dirName = "shapes_fit_b" if self.bkgOnly else "shapes_fit_s"
        else:
            dirName = "shapes_prefit"

        fit      = self.__getFitObject( key=dirName )
        channel  = copy.copy(fit.Get("Bin0"))
        histList = [ x.GetName() for x in channel.GetListOfKeys() ]

        hists    = {}
        for hist in histList:
            if hist == "total_covar": continue
            hists[hist] = copy.copy(channel.Get(hist))

        if nuisance:
            hists.update( self.getNuisanceHistos( postFit=postFit, plotBins=plotBins, plotChannel=plotChannel, nuisance=nuisance ) )

        # Data Histo
        hists["data"].style        = styles.errorStyle( ROOT.kBlack )
        hists["data"].legendOption = "p"

        if sorted:
            self.sortedRegionHistos[key][subkey] = hists
        else:
            self.regionHistos[key][subkey] = hists

        return hists


    def getImpactPlot( self, expected=False, printPNG=False, cores=1 ):

        cardName      = self.cardFile.split("/")[-1].split(".")[0]
        shapeName     = self.shapeFile.split("/")[-1]
        shapeRootName = self.shapeRootFile.split("/")[-1]
        rootCardName  = self.rootCardFile.split("/")[-1]

        # assuming you have combine in the same release!!!
        combineReleaseLocation = os.path.join( os.environ["CMSSW_BASE"], "src" )
        combineDirname = os.path.join( combineReleaseLocation, str(self.year), cardName )
        if not os.path.isdir(combineDirname): os.makedirs(combineDirname)

        newShapeFilePath     = os.path.join( combineDirname, shapeName )
        newShapeRootFilePath = os.path.join( combineDirname, shapeRootName )
        shutil.copyfile( self.shapeFile,     newShapeFilePath )
        shutil.copyfile( self.shapeRootFile, newShapeRootFilePath )

        # use scram if combineReleaseLocation is a different release than current working directory
        # echo is just a placeholder
        if os.environ["CMSSW_BASE"] in combineReleaseLocation:
            scram = "echo ''"
        else:
            scram = "eval `scramv1 runtime -sh`"

        if self.bkgOnly:
            prepWorkspace = "text2workspace.py %s --X-allow-no-signal -m 125"%shapeName
            robustFit     = "combineTool.py -M Impacts -d %s -m 125 --doInitialFit --robustFit 1 --rMin -0.01 --rMax 0.0"%rootCardName
            impactFits    = "combineTool.py -M Impacts -d %s -m 125 --robustFit 1 --doFits --parallel %i --rMin -0.01 --rMax 0.0"%( rootCardName, cores )
        else:
            prepWorkspace = "text2workspace.py %s -m 125"%shapeName
            robustFit     = "combineTool.py -M Impacts -d %s -m 125 --doInitialFit --robustFit 1 --rMin -10 --rMax 10"%rootCardName
            impactFits    = "combineTool.py -M Impacts -d %s -m 125 --robustFit 1 --doFits --parallel %s --rMin -10 --rMax 10"%( rootCardName, cores )

        extractImpact   = "combineTool.py -M Impacts -d %s -m 125 -o impacts.json"%rootCardName
        plotImpacts     = "plotImpacts.py -i impacts.json -o impacts"
        combineCommand  = ";".join( [ "cd %s"%combineDirname, scram, prepWorkspace, robustFit, impactFits, extractImpact, plotImpacts ] )

        os.system(combineCommand)

        plotName = "impacts"
        if self.bkgOnly: plotName += "_bkgOnly"
        if expected:     plotName += "_expected"

        shutil.copyfile( combineDirname+"/impacts.pdf", "%s/%s.pdf"%(self.plotDirectory, plotName) )
        if printPNG:
            os.system("convert %s/%s.pdf %s/%s.png"%( self.plotDirectory, plotName, self.plotDirectory, plotName) )
            copyIndexPHP( self.plotDirectory )

        shutil.rmtree( combineDirname )


    #def getNuisanceHisto( self, postFit=False, plotBins=None, plotChannel=None, sorted=False ):

    def getCorrelationHisto( self, systOnly=None ):

        if not self.rootFile:
            raise ValueError( "Root file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

        if self.correlationHisto:
            if systOnly:
                nuisSyst = self.getNuisancesList( systOnly=True )
                nuisAll  = self.getNuisancesList( systOnly=False )
                hist = self.correlationHisto.Clone()
                hist.GetXaxis().SetRangeUser(0,len(nuisSyst))
                hist.GetYaxis().SetRangeUser(len(nuisAll)-len(nuisSyst),len(nuisAll))
                hist.LabelsOption("v","X")
                return hist
            return self.correlationHisto

        fit = self.__getFitObject( key="fit_b" if self.bkgOnly else "fit_s" )
        self.correlationHisto = fit.correlationHist()
        self.correlationHisto.LabelsOption("v","X")

        if systOnly:
            nuisSyst = self.getNuisancesList( systOnly=True )
            nuisAll  = self.getNuisancesList( systOnly=False )
            hist = self.correlationHisto.Clone()
            hist.GetXaxis().SetRangeUser(0,len(nuisSyst))
            hist.GetYaxis().SetRangeUser(len(nuisAll)-len(nuisSyst),len(nuisAll))
            hist.LabelsOption("v","X")
            return hist
        return self.correlationHisto

    def getCovarianceHisto( self, postFit=False ):
        # get the TH2D covariance matrix plot

        if not self.rootFile:
            raise ValueError( "Root file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

        key = "postFit" if postFit else "preFit"
        if self.covarianceHistos[key]:
            return self.covarianceHistos[key]

        if postFit:
            dirName = "shapes_fit_b" if self.bkgOnly else "shapes_fit_s"
        else:
            dirName = "shapes_prefit"

        fit = self.__getFitObject( key=dirName )
        self.covarianceHistos[key] = copy.copy( fit.Get("overall_total_covar") )

        return self.covarianceHistos[key]


if __name__ == "__main__":

    from TTGammaEFT.Tools.user import plot_directory

    cardFile = "/afs/hephy.at/data/llechner01/TTGammaEFT/cache/analysis/2016/limits/cardFiles/defaultSetup/observed/DY2_VG2_misDY2_misIDPOI.txt"
    add = [ item for item in cardFile.split("_") if item in ["addDYSF", "addMisIDSF", "misIDPOI", "incl"] ]
    add.sort()
    dirName  = "_".join( [ item for item in cardFile.split("/")[-1].split("_") if item not in ["addDYSF", "addMisIDSF", "misIDPOI", "incl"] ] )
    fit      = "_".join( ["postFit"] + add )
    plotDir  = os.path.join(plot_directory, "fit", str(2016), fit, dirName)
    Results = CombineResults( cardFile, plotDir, 2016, bkgOnly=False )
    print Results.getCorrelationHisto(systOnly=True).GetNbinsX()
