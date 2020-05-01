#!/bin/bash

python scripts/main.py -wf data/worflow-connection-subset-04-20.tsv -tu data/tool-popularity-20-03.tsv -om data/tool_recommendation_model.hdf5 -cd '2017-12-01' -pl 25 -ep 2 -oe 2 -me 2 -ts 0.2 -vs 0.2 -bs '32,256' -ut '32,256' -es '32,256' -dt '0.0,0.5' -sd '0.0,0.5' -rd '0.0,0.5' -lr '0.00001,0.1' -trs 10000 -cpus 4
