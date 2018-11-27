#!/bin/bash

#BSUB -J sumo_sim
#BSUB -n 100
#BSUB -q long 
#BSUB -W 24:00
#BSUB -e %J.err
#BSUB -R rusage[mem=4096]

mpirun -n 100 python mpi_run.py
