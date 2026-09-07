#!/bin/bash

#awk -v block="$(./generate_block.py -snap minX minY minZ -scales 1 1 1 Surfaces/fins.stl)" \
#    '/VERTICES/{print block; next} 1' system/blockMeshDict.config > \
#    system/blockMesh
#
#if ! blockMesh > log.blockMesh; then
#    echo ERROR
#    echo blockMesh failed
#else
#    echo blockMesh done.
#fi
#

awk -v block="$(./generate_block.py "$@")" \
    '/VERTICES/{print block; next} 1' system/blockMeshDict.config > \
    system/blockMeshDict

if ! blockMesh > log.blockMesh; then
    echo ERROR
    echo blockMesh failed
else
    echo blockMesh done.
fi
