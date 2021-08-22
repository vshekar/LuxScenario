from mpi4py import MPI
from network_snapshot import SumoSim
import sumolib
import time
import os

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

network = sumolib.net.readNet('../scenario/lust.net.xml')
edges = network.getEdges()
edgeIDs = [edge.getID() for edge in edges if edge.getLaneNumber()>2]
time_intervals = [(0, 28800), (28800, 57600), (57600, 86400)]
total_processors = 100
lmbd_list = [float('inf')]

chunks = [edgeIDs[i::total_processors] for i in range(total_processors)]

current_chunk = chunks[rank]

for edge in current_chunk:
    for start_time, end_time in time_intervals:
        for lmbd in lmbd_list:
            filename = '../output/lmbd_{}/traveltime_{}_{}_{}_{}.json'.format(lmbd, edge, start_time, end_time, lmbd)
            f = open('comp_sim.txt', 'r')
            completed_sims = f.read().split()
            f.close()
            
        ss = SumoSim(edge, lmbd, start_time, end_time, filename, rank)
        if not os.path.isfile(filename) and filename.split('/')[-1] not in completed_sims:
            #os.makedirs(filename)
            #ss.run()
            print(" ")
        f = open(filename, 'w')
        f.close()
        ss.run()
