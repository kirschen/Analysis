#!/bin/bash

voms-proxy-init -voms cms --valid 192:00 --vomslife 192:0 -out $HOME/private/.proxy
