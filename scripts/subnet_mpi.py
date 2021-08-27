from mpi4py import MPI
import h5py
import sumolib
import time
from network_snapshot_subnet import SumoSim
from data_wrapper import Data, Graph
import os
#import sumolib
import numpy as np
import json
import traci
import shutil
import datetime
from pathlib import Path
from traci.exceptions import FatalTraCIError
import sys

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
current_hdf = 0
sim_complete = 0

network = sumolib.net.readNet('../scenario/lust.net.xml')
edges = network.getEdges()
with open('min_subnet.json', 'r') as f:
    edgeIDs = list(json.load(f).keys())
#edgeIDs = [edge.getID() for edge in edges if edge.getLaneNumber()>2]
time_intervals = [(0,10), (0, 28800), (28800, 57600), (57600, 86400)]
total_processors = 1001
TERMINATE = 0
SIM_DATA = 1
WAIT = 2
SIM_FAILED = 3
#PROCESS_COMPLETE
lmbd_list = json.load(open('lambdas.json', 'r'))
running_sims = {} 
remaining_sims = []


def start():
    print('Starting with {} processors'.format(total_processors), flush=True)
    if rank == total_processors-1:
        start_writer()
    else:
        start_sim()

def start_writer():
    """ Setup writer process """
    print('Setting up writer', flush=True)
    setup_hdf5()
    init_sims()
    
    while len(running_sims) > 0 or len(remaining_sims) > 0:
        print("Writer waiting for results. Running Sims: {} Remaining Sims: {}".format(len(running_sims), len(remaining_sims)), flush=True)
        #if no_space():
        #    send_file()
        #    print("No More Space!")
        #else:
        update_file()
        


def init_sims():
    global remaining_sims
    remaining_sims = get_remaining_sims()
    for i in range(total_processors-1):
       sim_data = remaining_sims.pop()
       req = comm.send(sim_data, dest=i, tag=SIM_DATA)
       running_sims[i] = sim_data
    #return remaining_sims, running_sims



def sim_data_location():
    return '/project/umd_lance_fiondella/sim_data_{}.h5'.format(current_hdf)

def update_file():
    print("Writer waiting for message", flush=True)
    status = MPI.Status()
    #data = bytearray(1<<27) 
    #req = comm.irecv()
    #data = req.wait(status=status)
    data = comm.recv(status = status)
    tag = status.Get_tag()
    rnk = status.Get_source()
     
    if tag == SIM_DATA or tag == SIM_FAILED:
        #data = grps[rnk].create_dataset(str(rnk), data=data)
        #npdata = data.dataframe
        f = h5py.File(sim_data_location(), 'a')
        print("{} : Writer got data from : {} \n For sim with interval {} to {} and edge {} disrupted. With dataframe of type: {} and shape: {}"
              .format(datetime.datetime.now(),
                      rnk, 
                      data.start_time, 
                      data.end_time, 
                      data.edge, 
                      type(data.get_dataframe()), data.get_dataframe().shape), flush=True)
        group_name = '/lux_scenario/{}_{}/{}'.format(data.start_time, data.end_time, data.edge)
        group = f.require_group(group_name)
        dataset_name = group_name + '/{}'.format(data.lmbd)
        #if '/lux_scenario/{}_{}/{}/{}'.format(data.start_time, data.end_time, data.edge, data.lmbd) not in f:
        if dataset_name not in f:
            group.create_dataset(str(data.lmbd), data=data.get_dataframe())
        f.close()

        # Update completed_sims.json
        with open('completed_sims.json','r') as f:
            completed = json.load(f)
        key = 'lux_scenario/{}/{}'.format(str(data.start_time)+'_'+str(data.end_time), data.edge)
        if key in completed:
            completed[key].append(data.lmbd)
        else:
            completed[key] = [data.lmbd]
        with open('completed_sims.json','w') as f:
            completed = json.dump(completed, f)

        del running_sims[rnk]
        if len(remaining_sims) > 0:
            sim_data = remaining_sims.pop()
            req = comm.send(sim_data, dest= rnk, tag=SIM_DATA)
            running_sims[rnk] = sim_data
        else:
            req = comm.send(None, dest = rnk, tag=TERMINATE)

        if tag == SIM_FAILED:
            with open('failed_sims.json','w+') as f:
                failed = json.load(f)
                failed.append(data)
                json.dump(failed, f)
                #completed = json.dump(completed, f)

        



def setup_hdf5():
    f = h5py.File(sim_data_location(), 'w')
    for eID in edgeIDs:
        f.create_group('/lux_scenario/0_28800/{}'.format(eID))
        f.create_group('/lux_scenario/28800_57600/{}'.format(eID))
        f.create_group('/lux_scenario/57600_86400/{}'.format(eID))
    f.close()

def get_remaining_sims():
    total_sims = {}
    with open('completed_sims.json','r') as f:
        completed = json.load(f)
    #Generating all simulations, Note: Simulating only 25% of total sims
    for edge in edgeIDs:
        for start, end in time_intervals:
            #for lmbd in range(1, lmbd_list[edge]):
            #total_sims['lux_scenario/{}/{}'.format(str(start)+'_'+str(end), edge)] = [i for i in range(1, lmbd_list[edge])]
            #total_sims['lux_scenario/{}/{}'.format(str(start)+'_'+str(end), edge)] = np.linspace(1, lmbd_list[edge], num=int(lmbd_list[edge]*0.25), dtype=np.int32, endpoint=False).tolist()
            total_sims['lux_scenario/{}/{}'.format(str(start)+'_'+str(end), edge)] = [i for i in np.linspace(1, 50, num=int(50*0.25), dtype=np.int32).tolist() if i <= lmbd_list[edge]]
    remaining_sims = []
    for sim in total_sims:
        if sim in completed.keys():
            rem = set(total_sims[sim]) - set(completed[sim])
            for lmbd in rem:
                remaining_sims.append((sim, lmbd))
        else:
            for lmbd in total_sims[sim]:
                remaining_sims.append((sim, lmbd))
    return remaining_sims


def start_sim():
    print('Starting Sim Rank = {0}'.format(rank), flush=True)
    tag = WAIT
    

    while tag != TERMINATE:
        status = MPI.Status()
        data = comm.recv(status = status)
        tag = status.Get_tag()
        if tag == SIM_DATA:
            #try:
            setup_and_run(data)
            #except FatalTraCIError:
            #    print
            #req1 = comm.send(data, dest=total_processors-1, tag=SIM_FAILED)
            tag = WAIT        
        elif tag == TERMINATE:
            print("Terminate tag received, exiting.")    
    #req2 = comm.send(True, dest=total_processors-1, tag=PROCESS_COMPLETE)


def setup_and_run(data):
    base_path = Path('/project/umd_lance_fiondella')
    output_path = base_path / 'sumo_output'
    config_path = base_path / 'config'
    scenario_path = '/home/vs57d/LuxScenario/scenario/'
    sim, lmbd = data
    net_graph = Graph()

    #completed = json.load(open('completed_sims.json'))
    for edge in network.getEdges():
        net_graph.addEdge(edge.getFromNode().getID(), edge.getToNode().getID(), edge.getID())

    #chunks = [edgeIDs[i::total_processors-1] for i in range(total_processors-1)]
    #chunks = [remaining_sims()[i::total_processors] for i in range(total_processors)]
    #current_chunk = chunks[rank]
    #for sim, lmbd in current_chunk:
    _, times, edge = sim.split('/')
    start_time, end_time = times.split('_')
    start_time, end_time = int(start_time), int(end_time)
    filename = ''
    cfg_file_path = config_path / 'dua.actuated_{}.sumocfg'
    if not cfg_file_path.exists():
        shutil.copy(scenario_path+'dua.actuated.sumocfg', str(config_path / 'dua.actuated_{}.sumocfg'.format(rank)))
        shutil.copy(scenario_path+'vtypes.add.xml', str(config_path / 'vtypes.add_{}.xml'.format(rank)))
        shutil.copy(scenario_path+'busstops.add.xml', str(config_path / 'busstops.add_{}.xml'.format(rank)))
        shutil.copy(scenario_path+'lust.poly.xml', str(config_path / 'lust.poly_{}.xml'.format(rank)))
        shutil.copy(scenario_path+'tll.static.xml', str(config_path / 'tll.static_{}.xml'.format(rank)))

    try:
        ss = SumoSim(edge, lmbd, start_time, end_time, filename, rank, net_graph, total_processors-1)
        ss.run()
    except Exception as e:
        print("Could not start simulation. Trying again. Exception: {}".format(e), flush=True)
        time.sleep(10)
        traci.close()
        ss = SumoSim(edge, lmbd, start_time, end_time, filename, rank, net_graph, total_processors-1)
        ss.run()

if __name__=="__main__":
    total_processors = int(sys.argv[1])
    start()
