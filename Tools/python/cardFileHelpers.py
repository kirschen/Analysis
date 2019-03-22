import math
import os, copy, shutil, uuid

from Analysis.Tools.CardFileWriter  import CardFileWriter
from Analysis.Tools.u_float import u_float

import logging
logger = logging.getLogger(__name__)


def getPull(nuisanceFile, name):
    with open(nuisanceFile) as f:
      for line in f:
        if name != line.split()[0]: continue
        return float(line.split(',')[0].split()[-1])
    return 0 # Sometimes a bin is not found in the nuisance file because its yield is 0

def getConstrain(nuisanceFile, name):
    with open(nuisanceFile) as f:
      for line in f:
        if name != line.split()[0]: continue
        return float(line.split(',')[1].split()[0].replace('*','').replace('!',''))
    return 0 # Sometimes a bin is not found in the nuisance file because its yield is 0

def getFittedUncertainty(nuisanceFile, name):
    with open(nuisanceFile) as f:
      for line in f:
        if name != line.split()[0]: continue
        return float(line.split(',')[1].split()[0].replace('!','').replace('*',''))
    return 0 # Sometimes a bin is not found in the nuisance file because its yield is 0


def getPostFitUncFromCard(cardFile, estimateName, uncName, binName):
    nuisanceFile = cardFile.replace('.txt','_nuisances_full.txt')
    return getFittedUncertainty(nuisanceFile, estimateName)*getPreFitUncFromCard(cardFile, estimateName, uncName, binName)

def getPreFitUncFromCard(cardFile, estimateName, uncName, binName):
    with open(cardFile) as f:
      binList = False
      estimateList = False
      for line in f:
        if len(line.split())==0: continue
        if line.split()[0] == "bin":
          if not binList: binList = True
          else:           binList = line.split()[1:]
        if line.split()[0] == "process":
          if not estimateList: estimateList = line.split()[1:]
        if line.split()[0] != uncName: continue
        for i in range(len(binList)):
          if binList[i] == binName and estimateList[i]==estimateName:
            try:    return float(line.split()[2:][i])-1
            except: 
              return 0. # muted bin has -, cannot be converted to float
      return 0.
      #raise Warning('No uncertainty ' + uncName + ' for ' + estimateName + ' ' + binName)

def getTotalPostFitUncertainty(cardFile, binName):
    with open(cardFile) as f:
      binList = False
      estimateList = False
      ind = []
      uncertainties = False
      uncDict = {}
      totalUnc = {}
      for line in f:
        if len(line.split())==0: continue
        if line.split()[0] == "bin":
          if not binList: binList = True
          else:
            binList = line.split()[1:]
            for i,b in enumerate(binList):
                if b == binName:
                    ind.append(i) 
          print ind
        if line.split()[0] == "process":
          if not estimateList:
            estimateList = line.split()[1:]
            estimateList = estimateList[ind[1]:ind[-1]+1]
        if line.split()[0] == "rate":
          estimates = line.split()[1:]
          estimates = [float(a) for a in estimates[ind[1]:ind[-1]+1]]
        if line.split()[0] == 'PU': uncertainties = True
        if uncertainties:
            uncDict[line.split()[0]] = [ 0 if a =='-' else float(a)-1 for a in line.split()[2:][ind[1]:ind[-1]+1] ]
    print estimateList
    print estimates
    nuisanceFile = cardFile.replace('.txt','_nuisances_full.txt')
    for unc in uncDict.keys():
        totalUnc[unc] = 0
        for i in range(len(estimates)):
            #totalUnc[unc] += uncDict[unc][i] * estimates[i] * ( 1 + getPull(nuisanceFile,unc)*uncDict[unc][i] ) #* getConstrain(nuisanceFile, unc)
            totalUnc[unc] += uncDict[unc][i] * estimates[i] * math.exp( getPull(nuisanceFile,unc)*uncDict[unc][i] )
            #totalUnc[unc] += (uncDict[unc][i] * estimates[i] * math.exp( getPull(nuisanceFile,unc)*uncDict[unc][i] ))**2
        if totalUnc[unc] > 0: print unc, totalUnc[unc]
        #totalUnc[unc] = math.sqrt(totalUnc[unc])
    total = 0
    for unc in totalUnc.keys():
        total += totalUnc[unc]**2
    estimatesPostFit = []
    for e in estimateList:
        res = getEstimateFromCard(cardFile, e, binName)
        res = applyAllNuisances(cardFile, e, res, binName)
        estimatesPostFit.append(res.val)
    estimatePostFit = sum(estimatesPostFit)
    return u_float(estimatePostFit,math.sqrt(total))
    #return uncDict, totalUnc
          #else: 

def getEstimateFromCard(cardFile, estimateName, binName, postfix=''):
    res = u_float(0)
    uncName = 'Stat_' + binName + '_' + estimateName+postfix
    with open(cardFile) as f:
      binList = False
      estimateList = False
      for line in f:
        if len(line.split())==0: continue
        if line.split()[0] == "bin":
          if not binList: binList = True
          else:           binList = line.split()[1:]
        if line.split()[0] == "process":
          if not estimateList: estimateList = line.split()[1:]
        if line.split()[0] == "rate":
            for i in range(len(binList)):
              if binList[i] == binName and estimateList[i]==estimateName:
                try: res.val = float(line.split()[1:][i])
                except: res.val = 0
                #return float(line.split()[1:][i])
        if line.split()[0] != uncName: continue
        for i in range(len(binList)):
          if binList[i] == binName and estimateList[i]==estimateName:
            try:    res.sigma = (float(line.split()[2:][i])-1)*res.val
            except: res.sigma = 0.
    return res

def getObservationFromCard(cardFile, binName):
    res = u_float(0)
    with open(cardFile) as f:
      binList = False
      estimateList = False
      for line in f:
        if len(line.split())==0: continue
        if line.split()[0] == "bin":
            binList = line.split()[1:]
        if line.split()[0] == "observation":
            for i in range(len(binList)):
              if binList[i] == binName:# and estimateList[i]==estimateName:
                try: res.val = float(line.split()[1:][i])
                except: res.val = 0
    return res

def applyNuisance(cardFile, estimate, res, binName):
    if not estimate.name in ['DY','multiBoson','TTZ']: return res
    uncName      = estimate.name if estimate.name != "TTZ" else 'ttZ'
    nuisanceFile = cardFile.replace('.txt','_nuisances_full.txt')
    scaledRes    = res*(1+getPreFitUncFromCard(cardFile, estimate.name, uncName, binName)*getPull(nuisanceFile, uncName))
    scaledRes2   = scaledRes*(1+res.sigma/res.val*getPull(nuisanceFile, 'Stat_' + binName + '_' + estimate.name)) if scaledRes.val > 0 else scaledRes
    return scaledRes2

def applyAllNuisances(cardFile, estimate, res, binName, nuisances):
    if not estimate in ['signal', 'WZ', 'TTX', 'TTW', 'TZQ', 'rare', 'nonprompt', 'ZZ','ZG']: return res
    if estimate == "WZ":
        uncName = estimate+'_xsec'
    elif estimate == "ZZ":
        uncName = estimate+'_xsec'
    elif estimate == "TZQ":
        uncName = "tZq"
    elif estimate == "TTX":
        uncName = "ttX"
    else:
        uncName      = estimate
    # use r=1 fits for now
    nuisanceFile = cardFile.replace('.txt','_nuisances_r1_full.txt')
    if estimate == "signal" or estimate == "TTW":
        scaledRes = res
    else:
        scaledRes    = res*(1+getPreFitUncFromCard(cardFile, estimate, uncName, binName)*getPull(nuisanceFile, uncName))
    scaledRes2   = scaledRes*(1+getPreFitUncFromCard(cardFile, estimate, 'Stat_' + binName + '_' + estimate, binName))**getPull(nuisanceFile, 'Stat_' + binName + '_' + estimate) if scaledRes.val > 0 else scaledRes
    allNuisances = nuisances#["unclEn","JER","leptonSF","PU","Lumi","PDF","SFb","topPt","JEC","trigger","SFl"]
    for n in allNuisances:
        scaledRes2 = scaledRes2*(1+getPreFitUncFromCard(cardFile, estimate, n, binName))**getPull(nuisanceFile, n) if scaledRes.val > 0 else scaledRes
        if scaledRes.val > 0: logger.info("Found uncertainty %s", n)
    return scaledRes2

def getRegionCuts(cardFile):
    binNames = getAllBinNames(cardFile)
    regionCuts = {}
    with open(cardFile) as f:
        for line in f:
            if not line.startswith("# "): continue
            for bin in binNames:
                if not bin in line: continue
                regionCuts[bin] = line.split(" ")[-1].split("\n")[0]
                break
    return regionCuts

def getAllBinNames(cardFile):
    with open(cardFile) as f:
        for line in f:
            if len(line.split())==0: continue
            if line.split()[0] == "bin":
                binList = line.split()[1:]
                return binList

def getAllProcesses(cardFile):
    with open(cardFile) as f:
        for line in f:
            if len(line.split())==0: continue
            if line.split()[0] == "process":
                processList = []
                # complex syntax needed to get the right order, set() mixes it up
                for proc in line.split()[1:]:
                    if not processList or proc != processList[0]:
                        processList.append(proc)
                    elif proc == processList[0]:
                        break
                return processList

def scaleCardFile(cardFile, outFile=None, scale=1., scaledProcesses=None, copyUncertainties=True):

    if not outFile:                  outFile  = "out_" + cardFile
    if not cardFile.startswith("/"): cardFile = os.path.join( os.getcwd(), cardFile )
    if not outFile.startswith("/"):  outFile  = os.path.join( os.getcwd(), outFile )

    if cardFile == outFile:
        # overwriting
        tmpFile = "/tmp/" + str(uuid.uuid4())
        shutil.copyfile( cardFile, tmpFile )
        cardFile = tmpFile
        
    regions     = getAllBinNames(cardFile)
    processes   = getAllProcesses(cardFile)

    if isinstance( scale, dict ):
        if set(scale.keys()) - set(regions):
            raise Exception("Regions in scale dict not known!")
        for region in list(set(regions) - set(scale.keys())):
            # add missing scales
            scale[region] = 1.
    else:
        scale = { region:scale for region in regions }                

    print scale

    if scaledProcesses is None:
        scaledProcesses = processes
    else:
        notContained = list(set(scaledProcesses) - set(processes))
        if notContained:
            raise Exception("Processes from scaledProcesses not in cardFile: %s"%", ".join(notContained))

    bgProcesses = copy.copy(processes)
    bgProcesses.remove("signal")

    c = CardFileWriter()

    for region in regions:

        totYield = 0
        for proc in processes:
            rate = getEstimateFromCard(cardFile, proc, region).val
            if proc in scaledProcesses: rate *= scale[region]
            c.specifyExpectation( region, proc, round( rate, 5 ) )
            totYield += rate

        c.addBin( region, bgProcesses, region)
        c.specifyObservation( region, int(round(totYield)) )

    c.writeToFile( outFile )
    del c

    # read uncertainty lines and simply append it to the new cardfile
    if copyUncertainties:

        flag = False
        with open(cardFile, "r") as f:
            with open(outFile, "a") as of:
                for line in f:
                    if flag: of.write(line)
                    elif line.startswith("rate"): flag = True
