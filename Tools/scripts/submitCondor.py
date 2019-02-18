#!/usr/bin/env python
"""
Usage:
submitCondor.py --query CONDORQUEUENAME --execFile submit_on_lxplus.sh file_with_commands
Will submit a condor job for each command line in the file_with_commands.
Each condor job is passed through the execFile (e.g. submit_on_lxplus.sh) to setup the environment.
Log files by default are stored at /afs/hephy.at/work/
"""
# Standard imports
import os, time, re

from Analysis.Tools.runUtils import prepareTokens, getSystem

# Defaults
user         = os.getenv("USER")
user_initial = os.getenv("USER")[0]
cwd          = os.getcwd()
cmssw        = os.getenv("CMSSW_BASE")
hostname     = os.getenv("HOSTNAME")
submit_time  = time.strftime("%Y%m%d_%H%M%S", time.localtime())

if not hostname.startswith("lxplus"):
    raise Exception( "Running submitCondor.py outside of lxplus is not supported yet!" )

queueChoices = [ "espresso", "microcentury", "longlunch", "workday", "tomorrow", "testmatch", "nextweek" ]
# Parser
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--output",   dest="output",   default="/afs/hephy.at/work/%s/%s/condor_output/"%(user_initial, user), help="path for batch output ")
parser.add_option("--execFile", dest="execFile", default="submit_to_lxplus.sh",            help="queue name for condor jobs")
parser.add_option("--queue",    dest="queue",    default="nextweek", choices=queueChoices, help="queue name for condor jobs")
parser.add_option('--dryrun',   dest="dryrun",                       action='store_true',  help='Run only on a small subset of the data?', )
parser.add_option('--logLevel', dest="logLevel",                     choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'], default='INFO', help="Log level for logging" )

(options,args) = parser.parse_args()

# Hephy Token
prepareTokens()

def getCommands( line ):
    commands = []
    split = None
    try:
        m=re.search(r"SPLIT[0-9][0-9]*", line)
        split=int(m.group(0).replace('SPLIT',''))
    except:
	pass
    line = line.split('#')[0]
    if line:
        if split:
            for i in range(split):
                commands.append(line+" --nJobs %i --job %i"%( split, i ))
        else:
            commands.append(line)
    return commands


if __name__ == '__main__':

    if not len(args) == 1:
        raise Exception("Only one argument accepted! Instead this was given: %s"%args)

    # load file with commands
    if os.path.isfile(args[0]):
        commands = []
        with open(args[0]) as f:
            for line in f.xreadlines():
                commands.extend( getCommands( line.rstrip("\n") ) )

    # or just the one command
    elif type(args[0]) == type(""):
        commands = getCommands( args[0] )

    if commands:

        # create logfile output dir
        if not os.path.isdir(options.output):
            os.mkdir(options.output)

        # general condor commands
	rundir = cwd.strip(cmssw)
        condorCommands  = []
        condorCommands += ["universe              = vanilla"]
        condorCommands += ["executable            = %s"%options.execFile]

        for i, command in enumerate(commands):
 
            # condor commands for each job
            filename = submit_time + "_" + command.replace(".py","").replace("  ","_").replace(" ","_").replace("--","")
            condorCommands += ["output                = %s"%os.path.join(options.output, filename+".output")]
            condorCommands += ["log                   = %s"%os.path.join(options.output, filename+".log")]
            condorCommands += ["error                 = %s"%os.path.join(options.output, filename+".err")]
            condorCommands += ["arguments             = %s %s"%(rundir, command) ]
            condorCommands += ['+JobFlavour           = "%s"'%options.queue]
            condorCommands += ["x509userproxy         = $ENV(X509_USER_PROXY)"]
            condorCommands += ["use_x509userproxy     = true"]
            condorCommands += ["queue 1"]

# write a submit script
exFile = "condor.sub"
with open(exFile, "w") as f:
    for line in condorCommands:
        f.write(line + '\n')

# submit
if not options.dryrun:
    os.system("condor_submit %s"%exFile)
    os.remove(exFile)
