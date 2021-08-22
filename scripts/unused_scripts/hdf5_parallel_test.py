from mpi4py import MPI
import h5py
import numpy as np
import sys
import pandas as pd

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

if rank == 2:
    total_messages = 0
    f = h5py.File('test_data.h5', 'a')
    grps = []
    grps.append(f.get('/lux_scenario/0_28800')) 
    grps.append(f.get('/lux_scenario/28800_57600')) 
    complete = []
    while len(complete) < 2:
        status = MPI.Status()
        data = None
        req = comm.irecv()
        data = req.wait(status=status)
        tag = status.Get_tag()
        rnk = status.Get_source()
        print(data)
        print(rnk)
        print(tag)
        sys.stdout.flush()
        if tag == 2:
            complete.append(data)
        elif tag == 1:
            data = grps[rnk].create_dataset(str(rnk), data=data)
        
    f.close()
else:
    #a = np.array([('x', 5, 6), ('y', 1, 2)], dtype=[('vehicle', 'S50'), ('start_time', 'i'), ('end_time', 'i')])
    data = {'name':['x', 'y'], 'start':[5, 1], 'end':[6,2]}
    a = pd.DataFrame(data=data)

    req1 = comm.isend(a.values(), dest=2, tag=1)
    req2 = comm.isend(True, dest=2, tag=2)
    

