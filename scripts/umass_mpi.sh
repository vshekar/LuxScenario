#!/bin/bash

#BSUB -J sumo_sim
#BSUB -n 1001
#BSUB -q long 
#BSUB -W 72:00
#BSUB -e %J.err
#BSUB -o %J.out
#BSUB -R rusage[mem=8192]


mpirun -n 1001 python3 subnet_mpi.py
