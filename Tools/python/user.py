'''
Some definitions.
'''
import os
if os.environ['USER'] in ['llechner']:
    plot_directory  = "/afs/hephy.at/user/l/llechner/www/TTGammaEFT/"
    cache_directory = "/afs/hephy.at/data/llechner01/TTGammaEFT/cache/"
elif os.environ['USER'] in ['dspitzba', 'dspitzbart']:
    plot_directory  = "/afs/hephy.at/user/d/dspitzbart/www/stopsDileptonLegacy/"
    cache_directory = "/afs/hephy.at/data/dspitzbart01/cache/"
else:
    plot_directory  = "/afs/hephy.at/user/%s/%s/www/Analysis/"%(os.environ['USER'][0],os.environ['USER'])
    cache_directory = "/afs/hephy.at/data/%s01/Analysis/"%os.environ['USER']

if not os.path.isdir(cache_directory): os.makedirs(cache_directory)
