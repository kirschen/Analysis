#!/bin/bash

voms-proxy-init -voms cms --valid 192:00 --vomslife 192:0 -out /afs/hephy.at/user/${USER:0:1}/$USER/private/private/.proxy
