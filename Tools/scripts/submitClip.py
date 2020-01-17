#!/usr/bin/python

""" 
    Usage:
    submitClip.py --OPTIONS "FILE"  :  Will submit a batch job for each command line in FILE.
    If the commandline ends with #SPLIT2, where 2 can be any number, an array job will be executed with (2) jobs.
    Each jobs gets the additional command options --nJobs 2 --job 0 and --nJobs 2 --job 1
    
    submitClip.py --OPTIONS "COMMAND"  :  Will submit a batch job for the command.

    Log files by default are stored at /mnt/hephy/cms/USER/batch_output/
"""
# Standard imports
import os, time, re, sys
import shlex, uuid
import shutil

# Defaults
home          = os.getenv("HOME")
user          = os.getenv("USER")
user_initial  = user[0]
cwd           = os.getcwd()
hostname      = os.getenv("HOSTNAME")
proxyCert     = os.getenv("X509_USER_PROXY")
submit_time   = time.strftime("%Y%m%d_%H%M%S", time.localtime())
inSingularity = os.path.exists("/.singularity.d/")
batch_output  = "/mnt/hephy/cms/%s/batch_output"%(user)
batch_tmp   = "/mnt/hephy/cms/%s/batch_input"%(user)

if not "clip" in hostname:
    raise Exception( "Running submitClip.py outside of clip is not supported!" )

if inSingularity:
    raise Exception( "Running submitClip.py inside of Singularity is not supported!" )

logChoices       = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET', 'SYNC']
queueChoices     = ["short", "medium", "long"] # long: 14 days, medium: 2 days, short: 8h
partitionChoices = ["c", "m", "g"] # c: regular node, m: high memory node, g: GPU node
# Parser
from optparse import OptionParser

parser = OptionParser()
parser.add_option('--logLevel',           dest="logLevel",           default="INFO",     choices=logChoices,       help="Log level for logging" )
parser.add_option('--status',             dest="status",                                 action='store_true',      help="Runs just squeue")
parser.add_option("--jobInfo",            dest="jobInfo",            default=None,       type=int,                 help="Print info to jobId" )
parser.add_option("--removeLogs",         dest="removeLogs",                             action='store_true',      help="Remove all log-files!" )
parser.add_option("--title",              dest="title",              default="batch",                              help="Job Title on batch" )
parser.add_option("--output",             dest="output",             default=batch_output,                         help="Logfile directory. Default is /mnt/hephy/cms/%s/batch_output/")
parser.add_option("--tmpDirectory",       dest="tmpDirectory",       default=batch_tmp,                            help="tmpfile directory. Default is /mnt/hephy/cms/%s/batch_input/")
parser.add_option('--dpm',                dest="dpm",                                    action='store_true',      help="Use dpm?")
parser.add_option('--dryrun',             dest="dryrun",                                 action='store_true',      help='Create submission files without submit?', )
parser.add_option("--queue",              dest="queue",              default="short",    choices=queueChoices,     help="Queue for batch job, default is short")
parser.add_option("--partition",          dest="partition",          default=None,       choices=partitionChoices, help="Partition for batch job, default is c")
parser.add_option("--nNodes" ,            dest="nNodes",             default=None,       type=int,                 help="Number of nodes requested" )
parser.add_option("--nTasks" ,            dest="nTasks",             default=None,       type=int,                 help="Number of times the job will be executed (each with same settings)" )
parser.add_option("--nCPUs"  ,            dest="nCPUs",              default=None,       type=int,                 help="Number of CPUs per task" )
parser.add_option("--nGPUs"  ,            dest="nGPUs",              default=None,       type=int,                 help="Number of GPUs (if --partition g) per task" )
parser.add_option("--memory",             dest="memory",             default=None,       type=int,                 help="Request memory in GB. Default is 4GB/core")
parser.add_option("--walltime",           dest="walltime",           default=None,       type=str,                 help="Walltime in format DD-HH:MM:SS")
parser.add_option("--cmssw",              dest="cmssw",              default="10_2_18",  type=str,                 help="Load CMSSW version from singularity container in the format XX_XX_XX. Default is 10_2_18. Set it to None to run without CMSSW!")

(options,args) = parser.parse_args()

# Logger
import logger
logger = logger.get_logger( options.logLevel, logFile=None )

def getProxy():
    # If X509_USER_PROXY is set, use existing proxy.
#    from proxy import renew_proxy
#    proxy = renew_proxy( None )
#    logger.info( "Using proxy certificate %s", proxy )
    logger.info( "Renewal of proxy certificate is currently not supported. You can use the certificate, but make sure it is still valid and the path is set in the environmental variable X509_USER_PROXY!" )
    proxy_cmd = "export X509_USER_PROXY=%s"%proxyCert if proxyCert else ""
    return proxy_cmd

def getCommands( line ):
    commands = []
    split    = 1

    try:
        m     = re.search(r"SPLIT[0-9][0-9]*", line)
        split = int(m.group(0).replace('SPLIT',''))
    except:
    	pass

    line = line.split('#')[0]
    if line:
        if split > 1:
            commands.append( (line + " --nJobs %i --job $SLURM_ARRAY_TASK_ID"%split, split) )
        else:
            commands.append( (line, split) )

    return commands

def make_batch_job( file, script, command, proxy_cmd, nJobs=1 ):
    # Submission script
    submitCommands  = []

    submitCommands += ["#!/usr/bin/bash"]
    submitCommands += [""]
    submitCommands += ["#SBATCH -J %s"%options.title]
    submitCommands += ["#SBATCH -D %s"%cwd]
    if nJobs > 1:
        submitCommands += ["#SBATCH -o %s/clipBatch.%%J.%%A-%%a.out"%(options.output)]
        submitCommands += ["#SBATCH -e %s/clipBatch.%%J.%%A-%%a.err"%(options.output)]
    else:
        submitCommands += ["#SBATCH -o %s/batch.%%J.out"%(options.output)]
        submitCommands += ["#SBATCH -e %s/batch.%%J.err"%(options.output)]
    submitCommands += [""]
    if options.nNodes:
        submitCommands += ["#SBATCH --nodes=%i"%options.nNodes]
    if options.nTasks:
        submitCommands += ["#SBATCH --ntasks=%i"%options.nTasks]
    if options.nCPUs:
        submitCommands += ["#SBATCH --cpus-per-task=%i"%options.nCPUs]
    if options.memory:
        submitCommands += ["#SBATCH --mem-per-cpu=%iG"%options.memory]
    if options.walltime:
        submitCommands += ["#SBATCH --time=%s"%options.walltime]
    if options.nGPUs:
        submitCommands += ["#SBATCH --gres=gpu:%i"%options.nGPUs]
    if options.partition:
        submitCommands += ["#SBATCH --partition %s"%options.partition]
    if nJobs > 1:
        submitCommands += ["#SBATCH --array=0-%i"%(nJobs-1)]
    submitCommands += [""]

    if options.cmssw:
        submitCommands += ["echo Loading CMSSW version %s from singularity container /mnt/hephy/cms/test/cmssw_CMSSW_%s.sif"%(options.cmssw, options.cmssw)]
        submitCommands += ["module load singularity/3.4.1"]
        submitCommands += ["singularity exec /mnt/hephy/cms/test/cmssw_CMSSW_%s.sif sh %s"%(options.cmssw, script)]

    else:
        submitCommands += ["sh " + script]

    submitCommands += ["rm %s"%script]
    submitCommands += ["echo Removed execution file: %s"%script]

    with open( file, "w" ) as f:
        for cmd in submitCommands:
            f.write(cmd+"\n")
    
    # Execution script
    scriptCommands  = []
    scriptCommands += ["#!/usr/bin/bash"]
    scriptCommands += [""]

    if options.cmssw:
        scriptCommands += ["eval $(/opt/cms/common/scram runtime -sh)"]

        if proxy_cmd:
            scriptCommands += [proxy_cmd]
            scriptCommands += ["echo"]
            scriptCommands += ["echo Checking Proxy Certificate:"]
            scriptCommands += ["echo"]
            scriptCommands += ["voms-proxy-info -all"]

    scriptCommands += ["echo"]
    if options.nTasks:
        scriptCommands += ["echo Executing user command for each of the %i tasks"%options.nTasks]
        scriptCommands += ["echo srun -l %s"%command]
        scriptCommands += ["echo"]
        scriptCommands += ["srun -l %s"%command]

    else:
        scriptCommands += ["echo Executing user command:"]
        scriptCommands += ["echo %s"%command]
        scriptCommands += ["echo"]
        scriptCommands += [command]

    scriptCommands += ["echo"]

    if proxy_cmd and options.cmssw:
        scriptCommands += ["echo Checking Proxy Certificate:"]
        scriptCommands += ["echo"]
        scriptCommands += ["voms-proxy-info -all"]

    scriptCommands += ["echo"]
    scriptCommands += ["echo Done executing command:"]
    scriptCommands += ["echo %s"%command]

    with open( script, "w" ) as f:
        for cmd in scriptCommands:
            f.write(cmd+"\n")
    

if __name__ == '__main__':

    if options.status:
        os.system("squeue")
        sys.exit(0)

    if options.jobInfo:
        os.system("jobinfo %i"%options.jobInfo)
        sys.exit(0)

    # create logfile output dir
    if options.removeLogs:
        logger.info( "Removing log files in path %s"%options.output )
        if os.path.exists( options.output ):
            shutil.rmtree( options.output )
            os.makedirs( options.output )
        sys.exit(0)

    if not len(args) == 1:
        raise Exception("Only one argument accepted! Instead this was given: %s"%args)

    if options.cmssw == "None":
        options.cmssw = None

    if options.cmssw and not os.path.exists("/mnt/hephy/cms/test/cmssw_CMSSW_%s.sif"%options.cmssw):
        raise Exception("Singularity container for CMSSW version %s not found: /mnt/hephy/cms/test/cmssw_CMSSW_%s.sif"%(options.cmssw,options.cmssw))

    # create logfile output dir
    if not os.path.isdir( options.output ):
        os.makedirs( options.output )

    # If X509_USER_PROXY is set, use existing proxy.
    proxy_cmd = getProxy() if options.dpm else ""

    # load file with commands
    if os.path.isfile(args[0]):
        commands = []
        with open(args[0]) as f:
            for line in f.xreadlines():
                commands.extend( getCommands( line.rstrip("\n") ) )

    # or just the one command
    elif isinstance( args[0], str ):
        commands = getCommands( args[0] )

    for command in commands:
        hash_string    = hash( "_".join( map( str, [time.time(), command, uuid.uuid4()] ) ) )
        job_file       = "%s/batch_%s.sub"%(options.tmpDirectory,hash_string)
        script_file    = "%s/script_%s.sh"%(options.tmpDirectory,hash_string)
        submit_command = "sbatch %s"%(job_file)

        if not os.path.isdir( options.tmpDirectory ):
            os.makedirs( options.tmpDirectory )

        make_batch_job( job_file, script_file, command[0], proxy_cmd, nJobs=command[1] )

        logger.info( "Created submission file: %s"%job_file )
        logger.info( "Created execution file: %s"%script_file )

        if not options.dryrun:
            os.system( submit_command )
            os.remove( job_file )
            logger.info( "Removed submission file: %s"%job_file )
            logger.info( "Log file written to %s"%options.output )

