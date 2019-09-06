#!/usr/bin/env python

# standard imports
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
import os
import uuid

theano_compile_dir = '/tmp/%s'%str(uuid.uuid4())
if not os.path.exists( theano_compile_dir ):
    os.makedirs( theano_compile_dir )
os.environ['THEANO_FLAGS'] = 'base_compiledir=%s'%theano_compile_dir 

# RootTools
from RootTools.core.standard import *
from Analysis.Tools.helpers  import nonEmptyFile
### nanoAOD postprocessor
from importlib import import_module
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor   import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel       import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop       import Module
    
## modules for nanoAOD postprocessor
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetUncertainties   import jetmetUncertaintiesProducer
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetRecalib            import jetRecalib
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.METSigProducer        import METSigProducer 
from PhysicsTools.NanoAODTools.postprocessing.modules.private.METminProducer    import METminProducer
from PhysicsTools.NanoAODTools.postprocessing.modules.private.ISRcounter        import ISRcounter

# Logger
import logging
logger = logging.getLogger(__name__)

def extractEra(sampleName):
    return sampleName[sampleName.find("Run"):sampleName.find("Run")+len('Run2000A')]

class MetSignificance:

    def __init__( self, sample, year, output_directory, fastSim=False ):

        if year not in [ 2016, 2017, 2018 ]:
            raise Exception("MetSignificance for year %i not known"%year)

        logger.info("Preparing nanoAOD postprocessing")
        logger.info("Will put files into directory %s", output_directory)

        self.year             = year
        self.output_directory = output_directory
        self.isData           = sample.isData
        self.fastSim          = fastSim
        self.name             = sample.name
        self.postfix          = "_for_%s"%self.name
        self.files            = [ f for f in sample.files if nonEmptyFile(f) ]
        self.outfiles         = None

        if year == 2016:
            metSigParamsMC      = [1.617529475909303, 1.617529475909303, 1.4505983036866312, 1.4505983036866312, 1.411498565372343, 1.411498565372343, 1.4087559908291813, 1.4087559908291813, 1.3633674107893856, 1.3633674107893856, 0.0019861227075085516, 0.6539410816436597]
            metSigParamsData    = [1.843242937068234, 1.843242937068234, 1.64107911184195,   1.64107911184195,   1.567040591823117, 1.567040591823117, 1.5077143780804294, 1.5077143780804294, 1.614014783345394,  1.614014783345394, -0.0005986196920895609, 0.6071479349467596]
            JER                 = "Summer16_25nsV1_MC" if not self.isData else "Summer16_25nsV1_DATA"
            JERera              = "Summer16_25nsV1"
            if self.isData:
                if self.name.count("Run2016B") or self.name.count("Run2016C") or self.name.count("Run2016D"):
                    JEC         = "Summer16_07Aug2017BCD_V11_DATA"
                elif self.name.count("Run2016E") or self.name.count("Run2016F"):
                    JEC         = "Summer16_07Aug2017EF_V11_DATA"
                elif self.name.count("Run2016G") or self.name.count("Run2016H"):
                    JEC         = "Summer16_07Aug2017GH_V11_DATA"
                else:
                    raise NotImplementedError ("Don't know what JECs to use for sample %s"%self.name)
            elif self.fastSim:
                JEC             = "Spring16_25nsFastSimV1_MC"
            else:
                JEC             = "Summer16_07Aug2017_V11_MC"

        elif year == 2017:
            metSigParamsMC      = [1.9648214119268503, 1.5343086462230238, 1.9167197601498538, 1.5145044341064964, 1.8069380221985405, 1.3217263662622654, 1.5506294867561126, 1.272977540964842, 1.50742322311234,   1.6542883449796797, -0.0017865650107230548,  0.6593106706741719]
            metSigParamsData    = [2.228118299837604,  1.2420725475347338, 2.227630982417529,  1.256752205787215,  2.0215250734187853, 1.1557507029911258, 1.7350536144535336, 1.1587692458345757, 1.9385081854607988, 1.8726188460472792, -2.6697894266706265e-05, 0.646984812801919]
            JER                 = "Fall17_V3_MC" if not self.isData else "Fall17_V3_DATA"
            JERera              = "Fall17_V3"
            if self.isData:
                if self.name.count('Run2017B'):
                    JEC         = "Fall17_17Nov2017B_V32_DATA"
                elif self.name.count('Run2017C'):
                    JEC         = "Fall17_17Nov2017C_V32_DATA"
                elif self.name.count('Run2017D'):
                    JEC         = "Fall17_17Nov2017DE_V32_DATA"
                elif self.name.count('Run2017E'):
                    JEC         = "Fall17_17Nov2017DE_V32_DATA"
                elif self.name.count('Run2017F'):
                    JEC         = "Fall17_17Nov2017F_V32_DATA"
                else:
                    raise NotImplementedError ("Don't know what JECs to use for sample %s"%self.name)
            elif self.fastSim:
                JEC             = "Fall17_FastsimV1_MC"
            else:
                JEC             = "Fall17_17Nov2017_V32_MC"

        elif year == 2018:
            metSigParamsMC      = [1.8430848616315363, 1.8430848616315363, 1.8572853766660877, 1.8572853766660877, 1.613083160233781,  1.613083160233781,  1.3966398718198898, 1.3966398718198898, 1.4831008506492056, 1.4831008506492056, 0.0011310724285762122, 0.6929410058142578]
            metSigParamsData    = [1.6231076732985186, 1.6231076732985186, 1.615595174619551,  1.615595174619551,  1.4731794897915416, 1.4731794897915416, 1.5183631493937553, 1.5183631493937553, 2.145670387603659,  2.145670387603659, -0.0001524158603362826, 0.7510574688006575]
            JER                 = "Autumn18_V1_MC" if not self.isData else "Autumn18_V1_DATA"
            JERera              = "Autumn18_V1"
            if self.isData:
                if self.name.count("Run2018"):
                    era         = extractEra(self.name)[-1]
                    JEC         = "Autumn18_Run%s_V8_DATA"%era
                else:
                    raise NotImplementedError ("Don't know what JECs to use for sample %s"%self.name)
            elif self.fastSim:
                JEC             = "Autumn18_FastSimV1_MC"
            else:
                JEC             = "Autumn18_V8_MC"

        # set the params for MET Significance calculation
        self.metSigParams = metSigParamsMC if not self.isData else metSigParamsData

        logger.info("Using JERs: %s", JER)
        logger.info("Using JECs: %s", JEC)

        # define modules. JEC reapplication only works with MC right now, so just don't do it.
        self.modules = []
    
        if not self.isData:
            self.modules.append( ISRcounter() )
            # always correct the "standard" MET (needed e.g. for METMinProducer). JECs won't be applied twice.
            #self.modules.append( jetmetUncertaintiesProducer(str(self.year), JEC, [ "Total" ], jer=JERera, jetType = "AK4PFchs", redoJEC=True, METBranchName='MET') )
            self.modules.append( jetmetUncertaintiesProducer(str(self.year), JEC, [ "Total" ], jetType = "AK4PFchs", redoJEC=True, doJERSmearing=False, METBranchName='MET') )
            if self.year == 2017:
                # in 2017, also recorrect the MET calculated with the v2 recipe
                #self.modules.append( jetmetUncertaintiesProducer(str(self.year), JEC, [ "Total" ], jer=JERera, jetType = "AK4PFchs", redoJEC=True, METBranchName='METFixEE2017') )
                self.modules.append( jetmetUncertaintiesProducer(str(self.year), JEC, [ "Total" ], jetType = "AK4PFchs", redoJEC=True, doJERSmearing=False, METBranchName='METFixEE2017') )
        else:
            self.modules.append( jetRecalib(JEC,JEC) )
            if year == 2017:
                self.modules.append( jetRecalib(JEC, JEC, METBranchName='METFixEE2017') )
            logger.info("JECs will be reapplied.")

        if year == 2016:
            self.modules.append( METSigProducer(JER, self.metSigParams, METCollection="MET", useRecorr=True, calcVariations=(not self.isData), jetThreshold=15.) )
        elif year == 2017:
            self.modules.append( METSigProducer(JER, self.metSigParams, METCollection="METFixEE2017", useRecorr=True, calcVariations=(not self.isData), jetThreshold=15., vetoEtaRegion=(2.65,3.14)) )
            self.modules.append( METminProducer(isData=self.isData, calcVariations=(not self.isData)) )
        elif year == 2018:
            self.modules.append( METSigProducer(JER, self.metSigParams, METCollection="MET", useRecorr=True, calcVariations=(not self.isData), jetThreshold=25.) )

    def __call__( self, cut ):
        newFileList = []
        logger.info("Starting nanoAOD postprocessing")
        for f in self.files:
            # need a hash to avoid data loss
            file_hash = str(hash(f))
            p = PostProcessor( self.output_directory, [f], cut=cut, modules=self.modules, postfix="%s_%s"%(self.postfix, file_hash))
            p.run()
            newFileList += [self.output_directory + '/' + f.split('/')[-1].replace('.root', '%s_%s.root'%(self.postfix, file_hash))]
        logger.info("Done. Replacing input files for further processing.")
        self.outfiles = newFileList

    def getNewSampleFilenames( self ):
        # return sample.files
        return self.outfiles



