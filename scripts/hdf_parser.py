import h5py
import json

f = h5py.File('/project/umd_lance_fiondella/sim_data_init20.h5', 'r')
#if 'lux_scenario/0_28800/--30256#0/1' in f:
#    print("Found file")

 
#if 'lux_scenario/0_28800/--30256#0' in f:
#    print("Found Node")



#lmbds = []
prefix = 'lux_scenario/'
intervals = ['0_28800', '28800_57600', '57600_86400']
data = {}


for interval in intervals:
  for edge in f.get(prefix+interval).keys():
    lmbds = []
    for lmbd in f.get(prefix+interval+'/'+edge).keys():
      lmbds.append(int(lmbd))
    if len(lmbds) > 0:
      data[prefix+interval+'/'+edge] = lmbds      


#for edge in f.get('lux_scenario/0_28800').keys():
#  lmbds = []
#  for lmbd in f.get('lux_scenario/0_28800/'+edge).keys():
#    lmbds.append(int(lmbd))
#  if len(lmbds) > 0:
#    t1[edge] = lmbds

json.dump(data, open('completed_sims_latest.json', 'w'))

