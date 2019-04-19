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
logChoices   = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET']
# Parser
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--output",             dest="output",             default="/afs/cern.ch/work/%s/%s/condor_output/"%(user_initial, user), help="path for batch output ")
parser.add_option("--execFile",           dest="execFile",           default="submit_to_lxplus.sh",            help="queue name for condor jobs")
parser.add_option("--queue",              dest="queue",              default="nextweek", choices=queueChoices, help="queue name for condor jobs")
parser.add_option("--discSpace",          dest="discSpace",          default=None,       type=int,             help="Request disc space in MB")
parser.add_option("--memory",             dest="memory",             default=None,       type=int,             help="Request memory in MB")
parser.add_option('--dpm',                dest="dpm",                                    action='store_true',  help="Use dpm?")
parser.add_option('--slc6',               dest="slc6",                                   action='store_true',  help="Use slc6?")
parser.add_option('--resubmitFailedJobs', dest="resubmitFailedJobs",                     action='store_true',  help="Resubmit Job when exitcode != 0" )
parser.add_option('--maxRetries',         dest="maxRetries",         default=10,         type=int,             help="Resubmit Job x times. Default is 10" )
parser.add_option('--dryrun',             dest="dryrun",                                 action='store_true',  help='Run only on a small subset of the data?', )
parser.add_option('--logLevel',           dest="logLevel",           default="INFO",     choices=logChoices,   help="Log level for logging" )

(options,args) = parser.parse_args()

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

    options.output = os.path.join( options.output, submit_time )

    # Hephy Token
    prepareTokens()

    if not len(args) == 1:
        raise Exception("Only one argument accepted! Instead this was given: %s"%args)

    # If X509_USER_PROXY is set, use existing proxy.
    if options.dpm:
        if hostname.startswith("lxplus"):
            from Analysis.Tools.user import cern_proxy_certificate
            proxy_location = cern_proxy_certificate
        else:
            proxy_location = None

        from RootTools.core.helpers import renew_proxy
        proxy = renew_proxy( proxy_location )

#        logger.info( "Using proxy certificate %s", proxy )
        os.system("export X509_USER_PROXY=%s"%proxy)

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
            os.makedirs(options.output)

        # general condor commands
        rundir = cwd.split(cmssw+"/")[1]
        condorCommands  = []
        condorCommands += ["universe              = vanilla"]
        condorCommands += ["executable            = %s"%options.execFile]
        condorCommands += ['+JobFlavour           = "%s"'%options.queue]
        condorCommands += ['environment           = "IWD=%s"' %cwd]
        if options.discSpace:
            condorCommands += ["request_disk          = %i"%(options.discSpace*1000)] # disc space in kB (MB*1000)
        if options.memory:
            condorCommands += ["request_memory        = %i"%(options.memory)] # memory in MB
        if options.resubmitFailedJobs:
            # Make sure your .sh file ends with the failing job!
            # If e.g. there is an "echo ..." after the failing job, the .sh file returns an error code 0, as "echo" was successful
            condorCommands += ["on_exit_remove        = ExitCode =?= 0"]
            condorCommands += ["max_retries           = %i" %options.maxRetries]            
        if options.dpm:
            condorCommands += ["x509userproxy         = $ENV(X509_USER_PROXY)"]
            condorCommands += ["use_x509userproxy     = true"]
        if options.slc6:
            condorCommands += ['requirements          = (OpSysAndVer =?= "SLCern6")'] # force slc6 machine

        for i, command in enumerate(commands):
            # condor commands for each job
            filename = command.replace(".py","").replace("  ","_").replace(" ","_").replace("--","")
            # NumJobStarts for creating an extra log file if the job restarts
            condorCommands += ["output                = %s"%os.path.join(options.output, filename+".out")]
            condorCommands += ["error                 = %s"%os.path.join(options.output, filename+".err")]
            condorCommands += ["log                   = %s"%os.path.join(options.output, filename+".log")]
            condorCommands += ["arguments             = %s %s"%(rundir, command) ]
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
