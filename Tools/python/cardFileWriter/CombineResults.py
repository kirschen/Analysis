# Still to do
# signal on top of histlist for signalregions
# cardfile manipulations
# cleanup

""" 
Extracting pre- and post-fit information.
Parts stolen from:
https://github.com/HephySusySW/Workspace/blob/94X-master/DegenerateStopAnalysis/python/tools/sysTools.py
and
https://github.com/HephySusySW/Workspace/blob/94X-master/DegenerateStopAnalysis/python/tools/degTools.py

Uses information of the *.txt, *.shapeCard.txt, shapeCard_FD.root files
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

import CombineHarvester.CombineTools.ch as ch

# Logging
import logging
logger = logging.getLogger(__name__)


class CombineResults:

    def __init__( self, cardFile, plotDirectory, year, bkgOnly=False, isSearch=False ):

        if not isinstance( cardFile, str ):
            raise ValueError( "CardFile input needs to be a string with the path to the cardFile" )
        if not cardFile.endswith(".txt") or "shapeCard" in cardFile or not os.path.exists( cardFile ):
            raise ValueError( "Please provide the path to the *.txt cardfile! Got: %s"%cardFile )

        self.year          = year
        self.bkgOnly       = bkgOnly
        self.isSearch      = isSearch # for searches, the bkgOnly impact plots are with mu=0, for measurements mu=1
        self.cardFile      = cardFile

        self.shapeFile      = cardFile.replace(".txt","_shapeCard.txt" )
        if not os.path.exists( self.shapeFile ):
            logger.warning( "Shape card not found: %s"%self.shapeFile )
            logger.warning( "Continuing with limited options!" )
            self.shapeFile = None

        self.rootFile      = cardFile.replace(".txt","_shapeCard_FD.root" )
        if not os.path.exists( self.rootFile ):
            logger.warning( "Root file of fit result not found: %s"%self.rootFile )
            logger.warning( "Continuing with limited options!" )
            self.rootFile = None

        # only used for impact plot
        self.shapeRootFile = cardFile.replace(".txt","_shape.root" )
        if not os.path.exists( self.shapeRootFile ):
            logger.warning( "Root file of fit result not found: %s"%self.shapeRootFile )
            logger.warning( "Continuing with limited options!" )
            self.shapeRootFile = None

        # only used for impact plot
        self.rootCardFile = cardFile.replace(".txt","_shapeCard.root" )
        if not os.path.exists( self.rootCardFile ):
            logger.warning( "Root card file of fit result not found: %s"%self.rootCardFile )
            logger.warning( "Continuing with limited options!" )
            self.rootCardFile = None

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
        self.nuisances           = None
        self.correlationHisto    = None
        self.rateParameter       = {"preFit":None, "postFit":None}
        self.estimates           = {"preFit":None, "postFit":None}
        self.uncertainties       = {"preFit":None, "postFit":None}
        self.pulls               = {"preFit":None, "postFit":None}
        self.covarianceHistos    = {"preFit":None, "postFit":None}
        self.regionHistos        = {"preFit":{"all":None}, "postFit":{"all":None}}
        self.regionFile          = {"preFit":{"all":None}, "postFit":{"all":None}}
        self.modHistos           = None

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

        fits   = ["fit_b", "fit_s", "norm_prefit", "norm_fit_s", "norm_fit_b", "nuisances_prefit", "nuisances_prefit_res", "shapes_prefit", "shapes_fit_b", "shapes_fit_s", "overall_total_covar", "process_covar", "process_corr"]
        result = {}
        for fit in fits:
            result[fit] = copy.copy( self.tRootFile.Get(fit) )
        self.fitResults = result

        if key: return self.fitResults[key]
        else:   return self.fitResults

    def __rewriteRebinnedFile( self, rootFile, copyDataFrom=None ):
        """ rewrite the rootfile from rebinning in the style of the combine output
        """
        tRootFile = ROOT.TFile( rootFile, "READ")

        fits   = ["Bin0_prefit", "Bin0_postfit", "Bin0_cov", "Bin0_cor"]
        result = {}
        for fit in fits:
            dir = copy.copy( tRootFile.Get(fit) )
            if "fit" in fit:
                histList    = [ x.GetName() for x in dir.GetListOfKeys() ]
                result[fit] = {}
                for hist in histList:
                    result[fit][hist] = copy.copy(dir.Get(hist))
            else:
                result[fit] = copy.copy(dir)

        tRootFile.Close()
        del tRootFile

        # copy initial results root file
        if copyDataFrom: # this is dangerous, maybe initial fit results are also taken into account! #FIXME
            shutil.copyfile( copyDataFrom, rootFile ) # copy labels etc. create a consistant set of cards

        tRootFile = ROOT.TFile( rootFile, "UPDATE" if copyDataFrom else "RECREATE")
        tRootFile.cd()

        fits = {"shapes_prefit":result["Bin0_prefit"], "shapes_fit_b":result["Bin0_postfit"], "shapes_fit_s":result["Bin0_postfit"]}
        for dir, obj in fits.iteritems():
            if not copyDataFrom: tRootFile.mkdir(dir+"/")
            tRootFile.cd(dir+"/")
            if not "prefit" in dir:
                result["Bin0_cov"].SetName("process_covar")
                result["Bin0_cov"].Write()
                result["Bin0_cor"].SetName("process_corr")
                result["Bin0_cor"].Write()
            if not copyDataFrom: tRootFile.mkdir(dir+"/Bin0/")
            tRootFile.cd(dir+"/Bin0/")
            for name, hist in obj.iteritems():
                if   name == "TotalSig"   in name: hist.SetName("total_signal")
                elif name == "TotalBkg"   in name: hist.SetName("total_background")
                elif name == "TotalProcs" in name: hist.SetName("total")
                elif name == "data_obs"   in name: hist.SetName("data")
                hist.Write()
            tRootFile.cd()

        tRootFile.Close()
        del tRootFile

    def __filter( self, filterDict, var=None ):
        if not isinstance( filterDict, dict ) or not var: return filterDict
        return { key:val for key, val in filterDict.items() if key==var}
            
    def __filterDict( self, filterDict, bin=None, estimate=None, nuisance=None, systOnly=False ):
        # remove estimate sub dictionaries
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

    def __reduceHistogram( self, fromHisto, plotBins ):
        # remove single bins from a histogram
        newH = ROOT.TH1F( str(uuid.uuid4()), str(uuid.uuid4()), len(plotBins), 0, len(plotBins))
        j = 0
        for i in range( fromHisto.GetNbinsX() ):
            if i not in plotBins: continue
            newH.SetBinContent( j+1, fromHisto.GetBinContent(i+1) )
            newH.SetBinError(   j+1, fromHisto.GetBinError(i+1)   )
            j += 1
        self.__copyHistoSettings( fromHist=fromHisto, toHist=newH, plotBins=plotBins )
        return newH

    def __copyHistoSettings( self, fromHist, toHist, plotBins=None ):
        # copy all our settings of a histogram when cloning it
        for var in [attr for attr in dir(fromHist) if not callable(getattr(fromHist, attr)) and not attr.startswith("__")]:
            try: setattr( toHist, var, getattr( h, var ) )
            except: pass
        try:    toHist.style = fromHist.style
        except: pass
        try:    toHist.legendOption = fromHist.legendOption
        except: pass
        try:    toHist.legendText = fromHist.legendText
        except: pass

        j = 0
        for i in range( fromHist.GetNbinsX() ):
            # make that more dynamic FIXME
            if plotBins and i not in plotBins: continue
            toHist.GetXaxis().SetBinLabel( j+1, fromHist.GetXaxis().GetBinLabel( i+1 ) )
            j += 1

        toHist.LabelsOption("v","X")

    def __getUncertaintiesFromCard( self, estimate, nuisance, bin, postFit=False ):
        binList   = self.getBinList( unique=False )
        estimates = self.getProcessList( unique=False )
        pull      = self.getPulls( nuisance=nuisance, postFit=postFit )
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
        
        return pull.val * unc if postFit else unc

    def __getRateParameterFromCard( self ):
        binList   = self.getBinList( unique=False )
        estimates = self.getProcessList( unique=False )
        unc       = 0
        rateParams = []
        with open( self.cardFile ) as f:
            for line in f:
                if "extArg" in line:      rateParams.append(line.split()[0])
                elif "rateParam" in line: rateParams.append(line.split()[-1])
        
        return list( set( rateParams ) )

    def __getSubKey( self, plotBins=None ):
        # that was a bit more complicated before, now it's kinda useless
        subkey = "all"
        if plotBins: subkey = "_".join(map(str,plotBins))
        return subkey

    def getNuisanceYields( self, nuisance, postFit=False, addSignal=(not self.isSearch) ):
        return { b:self.__getNuisanceBinYield( nuisance=nuisance, bin=b, postFit=postFit, addSignal=addSignal ) for b in self.getBinList( unique=True ) }

    def __getNuisanceBinYield( self, nuisance, bin, postFit=False, addSignal=True ):
        yields    = self.getEstimates( postFit=postFit, directory=None )
        processes = self.getProcessesPerBin( bin=bin )[bin]
        unc       = self.getUncertainties(   bin=bin, postFit=postFit, systOnly=False )[bin]

        del yields["total"]
        for key, y in yields.iteritems():
            if bin in y.keys():
                yields = y[bin]
                break

        #if nuisance not in unc["total_signal"].keys():
        #    raise ValueError("Nuisance not in cardfile: %s. Use one of [%s]"%(nuisance, ", ".join(unc["total_signal"].keys())))

        y, yup, ydown = 0, 0, 0
        for p in processes:
            if p.count('signal') and not addSignal: continue
            yproc  = yields[p].val if p in yields.keys() else 0 # yield is 0 when it is not in the results? or throw an error? FIXME
            uproc  = unc[p][nuisance]
            y     += yproc
            yup   += yproc*(1+uproc)
            ydown += yproc*(1-uproc)
        return {"up":yup, "down":ydown, "relUp":yup/y if y else 0, "relDown":ydown/y if y else 0, "yield":y}

    def getBinList( self, unique=True ):
        # get either the bin names for each process according to the cardfile ( Bin0 Bin0 Bin0 ... Bin1 Bin1 ...)
        # or only the unique ones (Bin0 Bin1 ...)
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

    def getBinLabels( self, labelFormater=None ):
        # labelFormater applies a function to the labels to format is accordingly

        # return safed binList if available
        if self.binLabels:
            if labelFormater:
                binLabels = map( labelFormater, self.binLabels )
                return binLabels
            else:
                return self.binLabels

        binLabels = []
        with open( self.cardFile ) as f:
            for line in f:
                if line.startswith("# Bin"):
                    binLabels.append(line.split(": ")[1].split("\n")[0])
                elif line.startswith("#Muted"):
                    binLabels.append(line.split(": ")[2].split("\n")[0])

        self.binLabels = binLabels

        if labelFormater:
            return map( labelFormater, binLabels )

        return self.binLabels

    def getNuisancesList( self, systOnly=False ):
        # get a list of nuisances in the cardfile

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

    def getProcessList( self, unique=True ):
        # get either the process names for each bin according to the cardfile ( MC1 MC2 MC3 ... MC1 MC2 ...)
        # or only the unique ones (MC1 MC2 ...)
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
        # get a dictionary with a list of processes for each bin

        # return safed binList if available
        if self.processes:
            if bin: return {bin:self.processes[bin]}
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
        if bin: return {bin:self.processes[bin]}
        return self.processes

    def getPulls( self, nuisance=None, postFit=False ):

        if not self.rootFile:
            raise ValueError( "Root file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

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


    def getRateParameter( self, rateParameter=None, postFit=False ):
        # return safed rate parameter if available
        key = "postFit" if postFit else "preFit"
        if self.rateParameter[key]:
            if rateParameter: return self.rateParameter[key][rateParameter]
            else:             return self.rateParameter[key]

        rateParamList = self.__getRateParameterFromCard()
        pulls         = self.getPulls( postFit=postFit )
        rateParams    = { par:pulls[par] for par in rateParamList if par in pulls.keys() }

        self.rateParameter[key] = rateParams
        if rateParameter: return self.rateParameter[key][rateParameter]
        else:             return self.rateParameter[key]


    def getUncertainties( self, bin=None, estimate=None, nuisance=None, postFit=False, systOnly=False ):
        # return safed uncertainties if available
        key = "postFit" if postFit else "preFit"
        if self.uncertainties[key]:
            if bin or estimate or nuisance or systOnly:
                return self.__filterDict( self.uncertainties[key], bin=bin, estimate=estimate, nuisance=nuisance, systOnly=systOnly )
            else:
                return self.uncertainties[key]

        allUnc        = self.getNuisancesList( systOnly=systOnly )
        allEst        = self.getProcessList( unique=False )
        rateParams    = self.getRateParameter()
        pulls         = self.getPulls( postFit=postFit )
        binList       = self.getBinList( unique=False )
        uncertainties = {}

        with open( self.cardFile ) as f:
            for line in f:
                if not line.split(): continue
                unc = line.split()[0] 
                if unc not in allUnc: continue
                if unc in rateParams.keys(): continue # remove rate parameters as they would be 0 anyway
                for i_bin, _bin in enumerate(binList):
                    est = allEst[i_bin]
                    if not _bin in uncertainties.keys(): uncertainties[_bin] = {}
                    if not est in uncertainties[_bin].keys(): uncertainties[_bin][est] = {}
                    try:
                        uncertainties[_bin][est][unc] = float(line.split()[2:][i_bin])-1
                        if postFit: uncertainties[_bin][est][unc] *= pulls[unc].sigma
                    except:
                        uncertainties[_bin][est][unc] = 0

        self.uncertainties[key] = uncertainties

        if bin or estimate or nuisance or systOnly:
            return self.__filterDict( self.uncertainties[key], bin=bin, estimate=estimate, nuisance=nuisance, systOnly=systOnly )
        else:
            return self.uncertainties[key]

    def getObservation( self, bin=None, directory="total" ):
        return {dir:{ b:b_dict["data"] for b, b_dict in o.iteritems() } for dir, o in self.getEstimates( postFit=False, bin=bin, estimate="data", directory=directory ).iteritems()}

    def getEstimates( self, bin=None, estimate=None, directory="total", postFit=False ):
        key    = "postFit" if postFit else "preFit"
        if self.estimates[key]:
            ests = self.estimates[key]
            all = { d:self.__filterDict( dic, bin=bin, estimate=estimate ) if bin else dic for d, dic in ests.iteritems() } 
            if directory: return {directory:all[directory]}                
            else: return all

        binList      = self.getBinList( unique=False )
        regionHistos = self.getRegionHistos( postFit=postFit, plotBins=None, directory=None )
        processes    = self.getProcessesPerBin( bin=None )
        yields       = {}
        for dir, histoDict in regionHistos.iteritems():
            tmp          = {}
            yields[dir]  = {}
            for est, h in histoDict.iteritems():
#                if est not in processes and est != "data" and not "total" in est: continue
                tmp[est] = {}
                for i in range(h.GetNbinsX()):
                    y = h.GetBinContent(i+1)
                    e = h.GetBinError(i+1) # Attention, this is the full error, not only MC statistics! Fixme
                    key = dir + "_Bin%i"%i if dir != "total" else binList[i]
                    tmp[est][key] = u_float( y, e )
                    yields[dir][key]    = {}

            # stupid restructuring to make it compatible w/ other functions
            for b in yields[dir].keys():
                for est in tmp.keys():
                    yields[dir][b][est] = tmp[est][b]

        self.estimates[key] = yields

        all = { d:self.__filterDict( dic, bin=bin, estimate=estimate ) if bin else dic for d, dic in yields.iteritems() } 
        if directory: return {directory:all[directory]}                
        else: return all

    def getNuisanceHistos( self, postFit=False, plotBins=None, nuisances=None, directory="total" ):

        histDict       = self.getRegionHistos( postFit=postFit, plotBins=None, directory=directory )
        nuisanceHistos = {}

        for dir, hist in histDict.iteritems():
            nuisanceHistUp      = hist["total_signal"].Clone()
            nuisanceHistDown    = hist["total_signal"].Clone()
            nuisanceHistos[dir] = {}
            for i_n, nuisance in enumerate(nuisances):
                nuisanceYields  = self.getNuisanceYields( nuisance, postFit=postFit )

                for i in range(nuisanceHistUp.GetNbinsX()):
                    nDict = nuisanceYields.values()[i]
                    nuisanceHistUp.SetBinContent(   i+1, nDict["up"] )
                    nuisanceHistDown.SetBinContent( i+1, nDict["down"] )
    
                nuisanceHistos[dir][nuisance]                    = { "up":nuisanceHistUp.Clone(), "down":nuisanceHistDown.Clone() }
                nuisanceHistos[dir][nuisance]["up"].style        = styles.lineStyle( ROOT.kSpring-1-i_n, width=3 ) #change to dynamic style
                nuisanceHistos[dir][nuisance]["down"].style      = styles.lineStyle( ROOT.kOrange+7+i_n, width=3 )
                nuisanceHistos[dir][nuisance]["up"].legendText   = nuisance + " (+1#sigma)"
                nuisanceHistos[dir][nuisance]["down"].legendText = nuisance + " (-1#sigma)"

        return nuisanceHistos

    def createRebinnedResults( self, rebinningCardFile ):
        # re-bin combine result according to https://cms-analysis.github.io/CombineHarvester/post-fit-shapes-ws.html
        # the results of self.CombineResults (pulls,...) will be applied to the new cardfile provided to this function (rebinningCardFile)
        # it creates all cards necessary for another CombineResults object containing all result objects (covMatrix, corrMatrix, pre/post-fit results)
        # the results can be used in another CombineResults object to get the plots

        if not self.rootFile:
            raise ValueError( "Root file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

        fitResult             = "fit_b" if self.bkgOnly else "fit_s"

        rebinningShapeFile    = rebinningCardFile.replace( ".txt", "_shapeCard.txt" )
        rebinningRootCardFile = rebinningCardFile.replace( ".txt", "_shapeCard.root" )
        rebinningRootFile     = rebinningCardFile.replace( ".txt", "_shapeCard_FD.root" )

        modCardFile           = rebinningCardFile.replace( ".txt", "_rebinned.txt" )       # copy inital txt input
        modShapeFile          = modCardFile.replace(       ".txt", "_shapeCard.txt" )      # copy initial shape input
        modRootFile           = modCardFile.replace(       ".txt", "_shapeCard_FD.root" )  # create with this method

        shutil.copyfile( rebinningCardFile,  modCardFile  ) # copy pre-fit txtCardFile to create a consistant set of cards
        shutil.copyfile( rebinningShapeFile, modShapeFile ) # copy pre-fit shapeCardFile to create a consistant set of cards

        rebinningCMD = "PostFitShapesFromWorkspace -w %s -o %s -d %s -f %s:%s --postfit --sampling --covariance"%(rebinningRootCardFile, modRootFile, modShapeFile, self.rootFile, fitResult)
        os.system(rebinningCMD)

        # rewrite content in a similar way to the combine fit results
        self.__rewriteRebinnedFile( modRootFile, copyDataFrom=rebinningRootFile )

        return modCardFile

    def getRegionHistos( self, postFit=False, plotBins=None, nuisances=None, bkgSubstracted=False, labelFormater=None, directory="total" ):

        if not self.rootFile:
            raise ValueError( "Root file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

        key    = "postFit" if postFit else "preFit"
        subkey = self.__getSubKey( plotBins=plotBins )

        if subkey in self.regionHistos[key].keys() and self.regionHistos[key][subkey]:
            hists = self.regionHistos[key][subkey]
            if directory: return {directory:hists[directory]}                
            else: return hists

        if   postFit and not self.bkgOnly: dirName = "shapes_fit_s"
        elif postFit and     self.bkgOnly: dirName = "shapes_fit_b"
        else:                              dirName = "shapes_prefit"

        fit      = self.__getFitObject( key=dirName )
        # loop over all directories, necessary for combined fits
        channels = { x.GetName():copy.copy( fit.Get( x.GetName() ) ) for x in fit.GetListOfKeys() if isinstance( fit.Get(x.GetName()), ROOT.TDirectoryFile ) }
        histDict = { dirName: [ x.GetName() for x in channel.GetListOfKeys() if x.GetName() != "data" ] + [ "data" ] for dirName, channel in channels.iteritems() }
        channels.update( { "total": fit } )
        histDict.update( { "total": [ x.GetName() for x in fit.GetListOfKeys() if x.GetName() not in channels.keys()] } )
        hists    = {}
        for dir, histList in histDict.iteritems():
            hists[dir]    = {}
            histList.sort()
            histList = filter( lambda hist: "total_covar" not in hist and "process_" not in hist, histList )
            for hist in histList:

                hists[dir][hist] = copy.copy(channels[dir].Get(hist))

                # change TGraph type to TH1F type for data
                if "data" in hist:# and not "_rebinned" in self.cardFile:
                    dataHist = hists[dir][histList[0]].Clone()
                    dataHist.Reset()
                    dataHist.SetName("data")

                    if type( hists[dir][hist] ) == ROOT.TGraphAsymmErrors:
                        for i in range(dataHist.GetNbinsX()):
                            dataHist.SetBinContent(i+1, hists[dir][hist].Eval(i+0.5))
                            dataHist.SetBinError(i+1, math.sqrt(hists[dir][hist].Eval(i+0.5)))
                        hists[dir]["data"] = dataHist
                    else:
                        hists[dir]["data"] = hists[dir][hist]


                    if hist != "data": del hists[dir][hist]

                    # Data Histo
                    hists[dir]["data"].style        = styles.errorStyle( ROOT.kBlack )
                    hists[dir]["data"].legendText   = "data"
                    hists[dir]["data"].legendOption = "p"

            if nuisances and not bkgSubstracted: # currently no single-nuisance plots with bkg substracted histograms #FIXME
                if isinstance( nuisances, str ): nuisances = [nuisances]
                hists[dir].update( self.getNuisanceHistos( postFit=postFit, plotBins=None, nuisances=nuisances ) )

            labels = self.getBinLabels( labelFormater=labelFormater )
            if labels:
                for h_key, h in hists[dir].iteritems():
                    if nuisances and h_key in nuisances:
                        for i in range(h["up"].GetNbinsX()):
                            h["up"].GetXaxis().SetBinLabel( i+1, labels[i] )
                            h["down"].GetXaxis().SetBinLabel( i+1, labels[i] )
                        h["up"].LabelsOption("v","X") #"vu" for 45 degree labels
                        h["down"].LabelsOption("v","X") #"vu" for 45 degree labels
                    else:
                        for i in range(h.GetNbinsX()):
                            h.GetXaxis().SetBinLabel( i+1, labels[i] )
                        h.LabelsOption("v","X") #"vu" for 45 degree labels

            # remove single bins from region plots
            if plotBins:
                for i_h, (h_key,h) in enumerate(hists[dir].iteritems()):
                    if nuisances and h_key in nuisances:
                        hists[dir][h_key]["up"]   = self.__reduceHistogram( fromHisto=h["up"],   plotBins=plotBins )
                        hists[dir][h_key]["down"] = self.__reduceHistogram( fromHisto=h["down"], plotBins=plotBins )
                    else:
                        hists[dir][h_key] = self.__reduceHistogram( fromHisto=h, plotBins=plotBins )

        self.regionHistos[key][subkey] = hists

        # substract backgrounds from data histo, remove bkg (except signal)
        # remove histograms after storing it in self.regionHistos (I know, waste of resources in loops before)
        if bkgSubstracted:
            for dir, histList in histDict.iteritems():
                hists[dir] = {"data":hists[dir]["data"], "signal":hists[dir]["total_signal"], "total":hists[dir]["total" if "total" in hists[dir].keys() else "total_overall"], "total_background":hists[dir]["total_background"], "total_signal":hists[dir]["total_signal"]}

                hists[dir]["data"].Add( hists[dir]["total_background"], -1 )
                # set negative bins to 0
                for i in range(hists[dir]["data"].GetNbinsX()):
                    if hists[dir]["data"].GetBinContent(i+1) < 0: hists[dir]["data"].SetBinContent(i+1, 0)

                hists[dir]["data_syst"] = hists[dir]["data"].Clone()
                hists[dir]["data_stat"] = hists[dir]["data"].Clone()

                for i in range(hists[dir]["data"].GetNbinsX()):
                    stat = hists[dir]["data"].GetBinError(i+1)
                    syst = hists[dir]["total_background"].GetBinError(i+1) / hists[dir]["total_background"].GetBinContent(i+1) * hists[dir]["data"].GetBinContent(i+1)
                    hists[dir]["data_syst"].SetBinError(i+1, syst)
                    hists[dir]["data_stat"].SetBinError(i+1, stat)
                    hists[dir]["data"].SetBinError(i+1, math.sqrt(stat**2+syst**2))

                hists[dir]["total_background"].Scale(0)

        if subkey in self.regionHistos[key].keys() and self.regionHistos[key][subkey]:
            if directory: return {directory:hists[directory]}                
            else: return hists

    def getRegionHistoList( self, regionHistos, processes=None, noData=False, sorted=False, bkgSubstracted=False ):
        # get the list of histograms and the ratio list for plotting a region plot

        if bkgSubstracted: return [ [regionHistos["signal"]], [regionHistos["data"]], [regionHistos["data_syst"]] ], [(0,1),(1,1),(2,1)]

        for p in processes:
            if not p in regionHistos.keys():
                # some histograms are 0, still should be in the legend
                logger.info("Histogram for %s not found! Creating one and setting it to 0! Continuing..."%p)
                regionHistos[p] = regionHistos["signal"].Clone()
                self.__copyHistoSettings( fromHist=regionHistos["signal"], toHist=regionHistos[p], plotBins=None )
                regionHistos[p].Scale(0.)
                regionHistos[p].SetName(p)
                del regionHistos[p].legendText
                regionHistos[p].notInLegend = True
    

        nuisances    = self.getNuisancesList( systOnly=False )
        binProcesses = self.getProcessesPerBin()
        ratioHistos  = []
        i_n          = 0

        if sorted:
            histoList = [[]]
            for i in range( regionHistos["signal"].GetNbinsX() ):
                proc_list = []

                for p in binProcesses["Bin%i"%i]:

                    if p in regionHistos.keys():
                        # set only one bin != 0
                        tmp = regionHistos[p].Clone( p + "_Bin%i_%s"%(i, str(uuid.uuid4())) )
                        tmp.Scale(0.)
                        tmp.SetBinContent( i+1, regionHistos[p].GetBinContent(i+1) )
                        self.__copyHistoSettings( fromHist=regionHistos[p], toHist=tmp, plotBins=None )
                    else:
                        tmp = regionHistos["signal"].Clone( p + "_Bin%i_%s"%(i, str(uuid.uuid4())) )
                        tmp.Scale(0.)
                        logger.info( "Adding default histogram for process %s in bin %i"%(p, i) )
                    if i != 0:
                        # remove all but the first histogram bin from the legend
                        try: del tmp.legendText
                        except: pass

                    proc_list.append(tmp)

                # sort each bin
                proc_list.sort( key=lambda h: -h.Integral() )
                histoList[0] += copy.copy(proc_list)
        else:
            histoList = [ [p_h for p, p_h in regionHistos.iteritems() if p in binProcesses ] ]
            histoList[0].sort( key=lambda h: -regionHistos[p].Integral() )

        # add data histos
        if not noData:
            histoList   += [ [regionHistos["data"]] ]
            ratioHistos += [ (1,0) ]
            i_n         += 1

        # add nuisance histos at last
        for n in nuisances:
            if n in regionHistos.keys() and isinstance( regionHistos[n], dict ):
                histoList   += [ [regionHistos[n]["up"]], [regionHistos[n]["down"]] ]
                ratioHistos += [ ((i_n)*2,0),((i_n)*2+1,0) ]
                i_n         += 1


        for i in range( regionHistos["signal"].GetNbinsX() ):
            for h_list in histoList:
                for h in h_list:
                    # make that more dynamic FIXME
                    h.GetXaxis().SetBinLabel( i+1, regionHistos["signal"].GetXaxis().GetBinLabel( i+1 ) )
                    h.LabelsOption("v","X") #"vu" for 45 degree labels


        return histoList, ratioHistos
        

    def setPlotDirectory( self, plotDirectory ):
        self.plotDirectory = plotDirectory

    def getImpactPlot( self, expected=False, printPNG=False, cores=1 ):

        cardName      = self.cardFile.split("/")[-1].split(".")[0]
        shapeName     = self.shapeFile.split("/")[-1]
        shapeRootName = self.shapeRootFile.split("/")[-1]
        rootCardName  = self.rootCardFile.split("/")[-1]

        # assuming you have combine in the same release!!! #FIXME
        combineReleaseLocation = os.path.join( os.environ["CMSSW_BASE"], "src" )
        combineDirname = os.path.join( combineReleaseLocation, str(self.year), cardName )
        if not os.path.isdir(combineDirname): os.makedirs(combineDirname)

        newShapeFilePath     = os.path.join( combineDirname, shapeName )
        newShapeRootFilePath = os.path.join( combineDirname, shapeRootName )
        shutil.copyfile( self.shapeFile,     newShapeFilePath )
        shutil.copyfile( self.shapeRootFile, newShapeRootFilePath )

        # use scram if combineReleaseLocation is a different release than current working directory
        # echo is just a placeholder
        if os.environ["CMSSW_BASE"] in combineReleaseLocation: scram = "echo ''"
        else:                                                  scram = "eval `scramv1 runtime -sh`"

        if self.bkgOnly:
            prepWorkspace = "text2workspace.py %s --X-allow-no-signal -m 125"%shapeName
            if self.isSearch:
                robustFit  = "combineTool.py -M Impacts -d %s -m 125 --doInitialFit --robustFit 1 --rMin -0.001 --rMax 0.001"%rootCardName
                impactFits = "combineTool.py -M Impacts -d %s -m 125 --robustFit 1 --doFits --parallel %i --rMin -0.001 --rMax 0.001"%( rootCardName, cores )
            else:
                robustFit  = "combineTool.py -M Impacts -d %s -m 125 --doInitialFit --robustFit 1 --rMin 0.999 --rMax 1.001"%rootCardName
                impactFits = "combineTool.py -M Impacts -d %s -m 125 --robustFit 1 --doFits --parallel %i --rMin 0.999 --rMax 1.001"%( rootCardName, cores )
        else:
            prepWorkspace = "text2workspace.py %s -m 125"%shapeName
            robustFit     = "combineTool.py -M Impacts -d %s -m 125 --doInitialFit --robustFit 1 --rMin -10 --rMax 10"%rootCardName
            impactFits    = "combineTool.py -M Impacts -d %s -m 125 --robustFit 1 --doFits --parallel %s --rMin -10 --rMax 10"%( rootCardName, cores )

        extractImpact  = "combineTool.py -M Impacts -d %s -m 125 -o impacts.json"%rootCardName
        plotImpacts    = "plotImpacts.py -i impacts.json -o impacts"
        combineCommand = ";".join( [ "cd %s"%combineDirname, scram, prepWorkspace, robustFit, impactFits, extractImpact, plotImpacts ] )

        os.system(combineCommand)

        plotName = "impacts"
        if self.bkgOnly: plotName += "_bkgOnly"
        if expected:     plotName += "_expected"

        shutil.copyfile( combineDirname+"/impacts.pdf", "%s/%s.pdf"%(self.plotDirectory, plotName) )
        if printPNG: # useful to get a visible plot in the www directory, for nothing else
            os.system("convert -trim %s/%s.pdf -density 150 -verbose -quality 100 -flatten -sharpen 0x1.0 -geometry 1600x1600 %s/%s.png"%( self.plotDirectory, plotName, self.plotDirectory, plotName) )
            copyIndexPHP( self.plotDirectory )

        logger.info("Impact plot created at %s/%s.pdf"%(self.plotDirectory, plotName) )
        shutil.rmtree( combineDirname )

    def getCorrelationHisto( self, systOnly=False ):

        if not self.rootFile:
            raise ValueError( "Root file of fit result not found! Running in limited mode, thus cannot get the object needed!" )

        if self.correlationHisto:
            if systOnly:
                nuisSyst = self.getNuisancesList( systOnly=True )
                nuisAll  = self.getNuisancesList( systOnly=False )
                hist     = self.correlationHisto.Clone(str(uuid.uuid4()))
                hist.GetXaxis().SetRangeUser(0,len(nuisSyst))
                hist.GetYaxis().SetRangeUser(len(nuisAll)-len(nuisSyst),len(nuisAll))
                hist.LabelsOption("v","X")
                return hist
            return self.correlationHisto

        fit      = self.__getFitObject( key="fit_b" if self.bkgOnly else "fit_s" )
        corrhist = copy.copy(fit.correlationHist())

        # bit of formating
        corrhist.GetZaxis().SetRangeUser(-1,1)
        corrhist.LabelsOption("v","X")

        self.correlationHisto = corrhist

        if systOnly:
            nuisSyst = self.getNuisancesList( systOnly=True )
            nuisAll  = self.getNuisancesList( systOnly=False )
            hist     = corrhist.Clone(str(uuid.uuid4()))
            hist.GetXaxis().SetRangeUser(0,len(nuisSyst))
            hist.GetYaxis().SetRangeUser(len(nuisAll)-len(nuisSyst)+1,len(nuisAll)+1)
            return hist
        return self.correlationHisto

    def getCovarianceHisto( self, labelFormater=None, postFit=False ):
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

        # normalize
        self.covarianceHistos[key].Scale(1./self.covarianceHistos[key].GetMaximum())

        # set labels
        self.covarianceHistos[key].LabelsOption("v","X")
        labels = self.getBinLabels( labelFormater=labelFormater )
        for i in range(self.covarianceHistos[key].GetNbinsY()):
            self.covarianceHistos[key].GetYaxis().SetBinLabel( i+1, labels[i] )
            self.covarianceHistos[key].GetXaxis().SetBinLabel( i+1, labels[i] )

        return self.covarianceHistos[key]

