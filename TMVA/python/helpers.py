import os, sys
import ROOT
import random

def getAnyObjFromFile( fname, hname ):

    rootGDirectory = ROOT.gDirectory.CurrentDirectory().GetName() + ':/'

    f     = ROOT.TFile.Open( fname ) if type( fname ) == type( "" ) else fname
    obj_t = f.FindObjectAny( hname )

    if not obj_t:
        raise Error( 'File ('+hname+') not found!' )

    ROOT.gDirectory.cd( rootGDirectory )
    obj = obj_t.CloneTree() if type( obj_t ) == type( ROOT.TTree() ) else obj_t.Clone()

    if type( fname ) == type( "" ):
        f.Close()

    return obj


def getEList( chain, cut, newname="eListTMP" ):
    chain.Draw(">>eListTMP_t", cut)
    elistTMP_t = ROOT.gROOT.Get("eListTMP_t")
    elistTMP = elistTMP_t.Clone(newname)
    del elistTMP_t
    return elistTMP

def fillTree( tree, chain, evlist, variables, maxEvents ):
    nmax = maxEvents if maxEvents>0 else len(evlist)
    for i, ev in enumerate(evlist[:nmax]):
        chain.GetEntry(ev)
        for v in variables:
            vn = getObsName(v[0])
            if obsType[vn] =="I":
                addObs[vn].value  = int(v[1](chain))
            if obsType[vn] =="F":
                addObs[vn].value  = v[1](chain)
        tree.Fill()

