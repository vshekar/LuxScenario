import h5py
import numpy as np
import pandas as pd

f = h5py.File('test_data.h5', 'w')
f.create_group('/lux_scenario/0_28800')
f.create_group('/lux_scenario/28800_57600')
grp = f.create_group('/lux_scenario/57600_28800')

a = np.array([('x', 5, 6), ('y', 1, 2)], dtype=[('vehicle', 'S50'), ('start_time', 'i'), ('end_time', 'i')])
#df = pd.DataFrame({'vehicle' : ['x', 'y'],
#                   'start_time' : [1, 2],
#                   'end_time' : [4, 5]})
data = grp.create_dataset("test", data=a)
#data = grp.get('test')
#np.append(data, ('z', 45, 3), axis=0)
print(data[0][0])
data[0] = ('asdf', 100, 100)
print(data[0])
f.close()
