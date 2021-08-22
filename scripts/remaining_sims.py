import json
import numpy as np
import sumolib

network = sumolib.net.readNet('../scenario/lust.net.xml')
edges = network.getEdges()
edgeIDs = [edge.getID() for edge in edges if edge.getLaneNumber()>2]
time_intervals = [(0, 28800), (28800, 57600), (57600, 86400)]
lmbd_list = json.load(open('lambdas.json', 'r'))

def remaining_sims():
    total_sims = {}
    total_sims_number = 0
    with open('completed_sims.json','r') as f:
        completed = json.load(f)
    #Generating all simulations, Note: Simulating only 25% of total sims
    for edge in edgeIDs:
        for start, end in time_intervals:
            #for lmbd in range(1, lmbd_list[edge]):
            #total_sims['lux_scenario/{}/{}'.format(str(start)+'_'+str(end), edge)] = [i for i in range(1, lmbd_list[edge])]
            total_sims['lux_scenario/{}/{}'.format(str(start)+'_'+str(end), edge)] = np.linspace(1, lmbd_list[edge], num=int(lmbd_list[edge]*0.25), dtype=np.int32, endpoint=False).tolist()
            total_sims_number += len(total_sims['lux_scenario/{}/{}'.format(str(start)+'_'+str(end), edge)])
    
    remaining_sims = []
    for sim in total_sims:
        if sim in completed.keys():
            rem = set(total_sims[sim]) - set(completed[sim])
            for lmbd in rem:
                remaining_sims.append((sim, lmbd))
        else:
            for lmbd in total_sims[sim]:
                remaining_sims.append((sim, lmbd))
    print('Total number of sims: {}'.format(total_sims_number))
    print('Completed sims: {}'.format(total_sims_number - len(remaining_sims)))
    return remaining_sims


print(len(remaining_sims()))
