import ROOT

default_factory_settings = [ "!V", "!Silent", "Color", "DrawProgressBar", "Transformations=I;D;P;G,D", "AnalysisType=Classification" ]

default_methods = {
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

