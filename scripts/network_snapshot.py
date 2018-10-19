import traci
import sumolib
import xml.etree.ElementTree as ET
import json
import time
from collections import defaultdict
import os.path

class SumoSim():
    
    SUMOBIN = 'sumo'
    def __init__(self, disrupted, lmbd, start_time, end_time, filename, rank):
        self.vehroutes_path = "../output/temp_routes/vehroutes{}.xml".format(rank)
        self.SUMOCMD = [self.SUMOBIN, "-c", "../scenario/dua.static.sumocfg",
                        "--time-to-teleport", "300", "--vehroute-output", self.vehroutes_path,
                        "--vehroute-output.exit-times", "true", "--ignore-route-errors", "-v",
                        "false", "-W", "true", "--additional-files", """../scenario/vtypes.add.xml,
                        ../scenario/busstops.add.xml, 
                        ../scenario/lust.poly.xml, ../scenario/tll.static.xml, ../scenario/additional/additional{}.xml""".format(rank), 
                        ]
        print("*********************************************************")
        print("Simulation Details: \n Disrupted link: {} \n Lambda: {} \n Start - End time: {} - {}".format(disrupted, lmbd, start_time, end_time))
        print("Initializing")
        self.network = sumolib.net.readNet('../scenario/lust.net.xml')
        self.filename = filename
        self.disrupted = disrupted
        self.start_time = start_time
        self.end_time = end_time
        if end_time == 0:
            self.nominal = True
        else:
            self.nominal = False

        self.lmbd = lmbd
        #if lmbd < float('inf'):
        #    self.convert_network(lmbd=self.lmbd)

        print("Setting up additional file")
        add_file = "../scenario/additional/additional{}.xml".format(rank)
        f = open(add_file, 'w')
        f.write("""
        <additional>
            <edgeData id="1" file="../../output/edgeData{0}.xml" begin="0" end="28800" excludeEmpty="true"/>
            <edgeData id="2" file="../../output/edgeData{0}.xml" begin="28800" end="57600" excludeEmpty="true"/>
            <edgeData id="3" file="../../output/edgeData{0}.xml" begin="57600" end="86400" excludeEmpty="true"/>
        </additional>
        """.format(rank))
        f.close()

        print("Setting up simulation")
        #self.setup_sim()
        #print("Total number of trips: {}".format(len(self.new_demand_route)))


    def run(self):
        print("Running Simulation")
        self.sim_start = time.time()
        self.run_sim()
        self.sim_end = time.time()
        print("Writing to file")
        self.write_to_file()

    def run_sim(self):
        traci.start(self.SUMOCMD)
        self.step = 0

        while traci.simulation.getMinExpectedNumber() > 0:
            self.disrupt_links()
            traci.simulationStep()
            self.step += 1
            
        traci.close()

    def disrupt_links(self):
        if self.nominal ==False and (self.start_time == self.step):
            #If nominal is true to not disrupt link
            lanes = self.network.getEdge(self.disrupted).getLanes()
            for lane in lanes:
                laneID = lane.getID()
                traci.lane.setDisallowed(laneID, ['passenger'])
        if self.nominal ==False and self.step == self.end_time:
            lanes = self.network.getEdge(self.disrupted).getLanes()
            for lane in lanes:
                laneID = lane.getID()
                traci.lane.setDisallowed(laneID, [])

    def write_to_file(self):
        data = {}
        tree = ET.parse(self.vehroutes_path)
        root = tree.getroot()
        for vehicle in root:
            if vehicle[0].tag == 'route':
                edges = vehicle[0].attrib['edges']
                exitTimes = vehicle[0].attrib['exitTimes']
            elif vehicle[0].tag == 'routeDistribution':
                edges = vehicle[0][-1].attrib['edges']
                exitTimes = vehicle[0][-1].attrib['exitTimes']
            data[vehicle.attrib['id']] = {"traveltime": float(vehicle.attrib['arrival']) - float(vehicle.attrib['depart']),
                                          "edges": edges,
                                          "exitTimes": exitTimes}

        data['sim_time'] = self.sim_end - self.sim_start
        
        with open(self.filename, 'w') as outfile:
            json.dump(data, outfile)

if __name__=="__main__":
    edge = u'--30256#0'
    lmbd = float('inf')
    start_time = 0
    end_time = 28800
    filename = 'test.json'
    rank = 0
    ss = SumoSim(edge, lmbd, start_time, end_time, filename, rank)
    ss.run()