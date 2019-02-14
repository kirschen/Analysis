''' Some definitions.
    To avoid changes of the file being pushed to github, e.g. when you define a different dbDir, use:
    git update-index --skip-worktree config.py
'''
import os

if os.environ['USER'] in ['llechner']:
    plot_directory                      = "/afs/hephy.at/user/l/llechner/www/TTGammaEFT/"
    cache_directory                     = "/afs/hephy.at/data/llechner01/TTGammaEFT/cache/"
else:
    ## This definition might not work for everybody. Update with whatever you like.
    plot_directory                      = "/afs/hephy.at/user/%s/%s/www/Analysis/"%(os.environ['USER'][0],os.environ['USER'])
    cache_directory                     = "/afs/hephy.at/data/%s01/Analysis/"%os.environ['USER']

if not os.path.isdir(cache_directory): os.makedirs(cache_directory)
