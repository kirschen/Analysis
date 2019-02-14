''' Some definitions.
    To avoid changes of the file being pushed to github, e.g. when you define a different dbDir, use:
    git update-index --skip-worktree config.py
'''
import os

plot_directory                      = "/afs/hephy.at/user/%s/%s/www/Analysis/"%(os.environ['USER'][0],os.environ['USER'])
cache_directory                     = "/afs/hephy.at/data/%s01/Analysis/"%os.environ['USER']

if not os.path.isdir(cache_directory): os.makedirs(cache_directory)
