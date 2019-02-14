# MetFilter Analysis Recommendations according to https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETOptionalFiltersRun2

def getFilterCut( year, isData=False, ignoreJSON=False ):
    if year == 2016:
        filters             = [ "Flag_goodVertices" ]                         # primary vertex filter
        filters            += [ "Flag_globalSuperTightHalo2016Filter" ]       # beam halo filter
        filters            += [ "Flag_HBHENoiseFilter" ]                      # HBHE noise filter
        filters            += [ "Flag_HBHENoiseIsoFilter" ]                   # HBHEiso noise filter
        filters            += [ "Flag_EcalDeadCellTriggerPrimitiveFilter" ]   # ECAL TP filter
        filters            += [ "Flag_BadPFMuonFilter" ]                      # Bad PF Muon Filter
        filters            += [ "Flag_BadChargedCandidateFilter" ]            # Bad Charged Hadron Filter
        if isData:
            filters        += [ "Flag_eeBadScFilter" ]                        # ee badSC noise filter (data only)

    elif year == 2017:
        filters             = [ "Flag_goodVertices" ]                         # primary vertex filter
        filters            += [ "Flag_globalSuperTightHalo2016Filter" ]       # beam halo filter
        filters            += [ "Flag_HBHENoiseFilter" ]                      # HBHE noise filter
        filters            += [ "Flag_HBHENoiseIsoFilter" ]                   # HBHEiso noise filter
        filters            += [ "Flag_EcalDeadCellTriggerPrimitiveFilter" ]   # ECAL TP filter
        filters            += [ "Flag_BadPFMuonFilter" ]                      # Bad PF Muon Filter
        filters            += [ "Flag_BadChargedCandidateFilter" ]            # Bad Charged Hadron Filter
#        filters            += [ "Flag_ecalBadCalibReducedMINIAODFilter" ]     # ECAL bad calibration filter update (needs to be re-run on miniAOD)
        filters            += [ "Flag_ecalBadCalibFilter" ]                   # current replacement for Flag_ecalBadCalibReducedMINIAODFilter
        if isData:
            filters        += [ "Flag_eeBadScFilter" ]                        # ee badSC noise filter (data only)

    elif year == 2018:
        filters             = [ "Flag_goodVertices" ]                         # primary vertex filter
        filters            += [ "Flag_globalSuperTightHalo2016Filter" ]       # beam halo filter
        filters            += [ "Flag_HBHENoiseFilter" ]                      # HBHE noise filter
        filters            += [ "Flag_HBHENoiseIsoFilter" ]                   # HBHEiso noise filter
        filters            += [ "Flag_EcalDeadCellTriggerPrimitiveFilter" ]   # ECAL TP filter
        filters            += [ "Flag_BadPFMuonFilter" ]                      # Bad PF Muon Filter
        filters            += [ "Flag_BadChargedCandidateFilter" ]            # Bad Charged Hadron Filter
#        filters            += [ "Flag_ecalBadCalibReducedMINIAODFilter" ]     # ECAL bad calibration filter update (needs to be re-run on miniAOD)
        filters            += [ "Flag_ecalBadCalibFilter" ]                   # current replacement for Flag_ecalBadCalibReducedMINIAODFilter
        if isData:
            filters        += [ "Flag_eeBadScFilter" ]                        # ee badSC noise filter (data only)

    else:
        raise NotImplementedError( "No MET filter found for year %i" %year )

    if isData:
        filters            += [ "weight>0" ]
        if not ignoreJSON:
            filters        += [ "jsonPassed>0" ]

    return "&&".join(filters)

