#!/usr/bin/env bash

schedd=$(condor_status -schedd | grep "bigbird" | cut -d ' ' -f 1)

for addr in $schedd;
do
    export _condor_CREDD_HOST=$addr && export _condor_SCHEDD_HOST=$addr
    condor_q
    echo ""
    echo ""
done;

