import os

running = os.listdir('../output/lmbd_inf/')
with open('comp_sim.txt', 'r') as f:
  completed = f.read().split()

for run in running:
  if run in completed:
    print(run)
