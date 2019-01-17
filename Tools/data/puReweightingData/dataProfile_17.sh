#!/bin/sh

PILEUP_LATEST=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/pileup_latest.txt
JSON=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/ReReco/Cert_294927-306462_13TeV_EOY2017ReReco_Collisions17_JSON.txt
LUMI=41860

if [ ! -f "$PILEUP_LATEST" ]; then
   echo "File $PILEUP_LATEST does not exist on this site, copying from lxplus"
   scp $USER@lxplus.cern.ch:$PILEUP_LATEST pileup_latest.txt
   PILEUP_LATEST=pileup_latest.txt
fi


echo "Calculating PU 2017 XSecVDown"
pileupCalc.py -i $JSON --inputLumiJSON $PILEUP_LATEST --calcMode true --minBiasXsec 62280 --maxPileupBin 100 --numPileupBins 100 PU_2017_${LUMI}_XSecVDown.root
echo "Calculating PU 2017 XSecDown"
pileupCalc.py -i $JSON --inputLumiJSON $PILEUP_LATEST --calcMode true --minBiasXsec 66986 --maxPileupBin 100 --numPileupBins 100 PU_2017_${LUMI}_XSecDown.root
echo "Calculating PU 2017 XSecCentral"
pileupCalc.py -i $JSON --inputLumiJSON $PILEUP_LATEST --calcMode true --minBiasXsec 69200 --maxPileupBin 100 --numPileupBins 100 PU_2017_${LUMI}_XSecCentral.root
echo "Calculating PU 2017 XSecUp"
pileupCalc.py -i $JSON --inputLumiJSON $PILEUP_LATEST --calcMode true --minBiasXsec 71414 --maxPileupBin 100 --numPileupBins 100 PU_2017_${LUMI}_XSecUp.root
echo "Calculating PU 2017 XSecVUp"
pileupCalc.py -i $JSON --inputLumiJSON $PILEUP_LATEST --calcMode true --minBiasXsec 76120 --maxPileupBin 100 --numPileupBins 100 PU_2017_${LUMI}_XSecVUp.root
