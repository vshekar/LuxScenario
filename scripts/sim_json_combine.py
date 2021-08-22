import json

f1 = open('completed_sims.json','r')
f2 = open('completed_sims_latest.json', 'r')

total_data = json.load(f1)
latest_data = json.load(f2)

for key in latest_data.keys():
  if key in total_data.keys():
    total_data[key] = list(set(total_data[key]).union(set(latest_data[key])))
  else:
    total_data[key] = latest_data[key]

json.dump(total_data,open('completed_sims_total.json','w'))

