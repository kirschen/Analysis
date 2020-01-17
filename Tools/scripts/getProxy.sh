#!/bin/bash

if [[ $HOSTNAME == *"clip"* ]]; then
    voms-proxy-init --valid 192:00 --vomslife 192:0 -out $HOME/private/.proxy
else
    voms-proxy-init -voms cms --valid 192:00 --vomslife 192:0 -out $HOME/private/.proxy
fi
