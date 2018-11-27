from mpi4py import MPI
import h5py
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()


f = h5py.File('test_data.h5', 'a', driver='mpio', comm=comm)
grps = []
grps.append(f.get('/lux_scenario/0_28800')) 
grps.append(f.get('/lux_scenario/28800_57600')) 

current_grp = grps[rank]

a = np.array([('x', 5, 6), ('y', 1, 2)], dtype=[('vehicle', 'S50'), ('start_time', 'i'), ('end_time', 'i')])
data = current_grp.create_dataset("test", data=a)