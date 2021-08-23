from __future__ import print_function
import traci
import sumolib
import xml.etree.ElementTree as ET
import json
import time
from collections import defaultdict
import os.path
import os
from data_wrapper import Data, Graph
from mpi4py import MPI
import sys
from sumolib.miscutils import getFreeSocketPort
import traceback
from pathlib import Path

SIM_DATA = 1
PROCESS_COMPLETE = 2
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

class SumoSim():
    base_path = Path('/project/umd_lance_fiondella')
    output_path = base_path / 'sumo_output'
    config_path = base_path / 'config'
    network_path = Path('/home/vs57d/LuxScenario/scenario/lust.net.xml')
    
    SUMOBIN = 'sumo'
    def __init__(self, disrupted, lmbd, start_time, end_time, filename, rank, net_graph, writer_rank):
        self.writer = writer_rank
        #self.vehroutes_path = "/project/umd_lance_fiondella/sumo_output/temp_routes/vehroutes_{}.xml".format(rank)
        self.vehroutes_path = str(self.output_path / 'temp_routes' / 'vehroutes_{}.xml'.format(rank))
        self.SUMOCMD = [self.SUMOBIN, "-c", str(self.config_path / "dua.actuated_{}.sumocfg".format(rank)),
                        "--time-to-teleport", "1200", "--vehroute-output", self.vehroutes_path,
                        "--vehroute-output.exit-times", "true", "--ignore-route-errors", "-v",
                        "false", "-W", "true", "--no-step-log",
                        "--additional-files",
                        """{1}/vtypes.add_{0}.xml, {1}/busstops.add_{0}.xml, {1}/lust.poly_{0}.xml, {1}/tll.static_{0}.xml, {1}/additional_{0}.xml""".format(rank, str(self.config_path)),
                        ]
        print('RUNNING COMMAND: {0}'.format(self.SUMOCMD), file=sys.stderr, flush=True)
        #print("*********************************************************")
        #print("Simulation Details: \n Disrupted link: {} \n Lambda: {} \n Start - End time: {} - {}".format(disrupted, lmbd, start_time, end_time))
        #print("Initializing")
        #self.network = sumolib.net.readNet('../scenario/lust.net.xml')
        self.network = sumolib.net.readNet(str(self.network_path))
        self.net_graph = net_graph
        self.filename = filename

        self.edges = self.network.getEdges()
        self.edgeIDs = [edge.getID() for edge in self.edges]

        self.disrupted = disrupted
        self.start_time = start_time
        self.end_time = end_time
        if end_time == 0:
            self.nominal = True
        else:
            self.nominal = False

        self.lmbd = lmbd
        self.rank = rank
        
        #print("Setting up additional file")
        self.get_subnetwork()
        self.setup_additional_file()

        #print("Setting up simulation")
        self.setup_sim()
        #print("Total number of trips: {}".format(len(self.new_demand_route)))

    def setup_additional_file(self):
        #add_file = "../scenario/additional/additional_{}.xml".format(self.rank)
        add_file = "{1}/additional_{0}.xml".format(rank, str(self.config_path))
        f = open(add_file, 'w')
        f.write("""
        <additional>
            <edgeData id="1" file="/project/umd_lance_fiondella/sumo_output/edgeData_{0}_{1}_{2}_{3}.xml" begin="0" end="28800" excludeEmpty="true"/>
            <edgeData id="2" file="/project/umd_lance_fiondella/sumo_output/edgeData_{0}_{1}_{2}_{3}.xml" begin="28800" end="57600" excludeEmpty="true"/>
            <edgeData id="3" file="/project/umd_lance_fiondella/sumo_output/edgeData_{0}_{1}_{2}_{3}.xml" begin="57600" end="108000" excludeEmpty="true"/>
        </additional>
        """.format(self.disrupted, self.lmbd, self.start_time, self.end_time))
        f.close()

        tree = ET.parse(add_file)
        xmlRoot = tree.getroot()
        rerouter = ET.Element("rerouter")
        interval = ET.Element("interval")
        closing_reroute = ET.Element("closingReroute")

        closing_reroute.set('id', str(self.disrupted))
        closing_reroute.set('disallow', 'passenger')
        interval.set('begin', str(self.start_time))
        interval.set('end', str(self.end_time))
        rerouter.set('id', '1')
        
        disruptedEdge = self.network.getEdge(self.disrupted)
        #sources = [edge.getID() for edge in list(disruptedEdge.getIncoming().keys())]
        #dests = [edge.getID() for edge in list(disruptedEdge.getOutgoing().keys())]
        with open('min_subnet.json', 'r') as f:
            min_lambda = json.load(f)

        if disruptedEdge.getID() in min_lambda:
            reroute_edges = self.net_graph.getSubnet(disruptedEdge, min_lambda[disruptedEdge.getID()])
        else:
            print('Edge {0} not found in min_lambda'.format(disruptedEdge.getID()), flush=True)
            to_node = disruptedEdge.getToNode()
            from_node = disruptedEdge.getFromNode()
            dests = [edge.getID() for edge in list(to_node.getIncoming())] + \
                            [edge.getID() for edge in list(to_node.getOutgoing())]
            sources = [edge.getID() for edge in list(from_node.getIncoming())] + \
                            [edge.getID() for edge in list(from_node.getOutgoing())]
            reroute_edges = sources + dests

        rerouter.set('edges', ' '.join(reroute_edges))
        #rerouter.set('edges', '1_1')
        interval.append(closing_reroute)
        rerouter.append(interval)
        xmlRoot.append(rerouter)

        tree.write(add_file)


    def run(self):
        #print("Running Simulation")
        self.sim_start = time.time()
        self.run_sim()
        self.sim_end = time.time()
        #print("Writing to file")
        self.write_to_file()
        traci.close()

    def run_sim(self):
        #print('RUNNING COMMAND: {0}'.format(self.SUMOCMD))
        
        while True:
            try:
                PORT = sumolib.miscutils.getFreeSocketPort()
                traci.start(self.SUMOCMD, port=PORT)
                break
            except Exception as e:
                _,__,tb = sys.exc_info()
                traceback.print_tb(tb)
                #print("Unable to start traci, retrying: {}".format(traceback.print_tb(tb)), file=sys.stderr)
                #sys.stderr.write("Unable to start traci, retrying: {}".format(e))
        self.close_edges()
        self.setup_trips()
        
        self.step = 0

        #while traci.simulation.getMinExpectedNumber() > 0:
        #Simulate for 30 hours
        while self.step < 108000:
            self.disrupt_links()
            traci.simulationStep()
            self.step += 1
            if self.step  in [self.end_time+30, self.start_time+30, 30, 28830, 57630, 86430]:
                for edge in self.subnetwork_edges:
                    for veh in traci.edge.getLastStepVehicleIDs(edge):
                        traci.vehicle.rerouteTraveltime(veh)
            
        traci.close()

    def disrupt_links(self):
        if self.nominal ==False and (self.start_time == self.step):
            #If nominal is true to not disrupt link
            lanes = self.network.getEdge(self.disrupted).getLanes()
            for lane in lanes:
                laneID = lane.getID()
                traci.lane.setDisallowed(laneID, ['passenger', 'bus'])
        if self.nominal ==False and self.step == self.end_time:
            lanes = self.network.getEdge(self.disrupted).getLanes()
            for lane in lanes:
                laneID = lane.getID()
                traci.lane.setDisallowed(laneID, [])

    def write_to_file(self):
        #data = {}
        
        #print("Process {} starting write to file".format(rank), file=sys.stderr)
        sys.stderr.write("Process {} starting write to file".format(rank))
        data = []
        with open(self.vehroutes_path, 'r') as source:
            tree = ET.parse(source)
        root = tree.getroot()
        for vehicle in root:
            data.append((vehicle.attrib['id'], int(float(vehicle.attrib['arrival'])), int(float(vehicle.attrib['depart']))))
        
        
        df = Data(self.lmbd, self.start_time, self.end_time, self.disrupted)

        
        data.append(('sim_time', int(float(self.sim_start)), int(float(self.sim_end))))
        df.set_dataframe(data)
        #print("Process {} sending data".format(rank), file=sys.stderr)
        sys.stderr.write("Process {} sending data".format(rank))
        print("Process {} sending data. Dataframe shape: {}"
              .format(rank, df.get_dataframe().shape))
        req1 = comm.send(df, dest=self.writer, tag=SIM_DATA)
        
        
        print("Process {} starting closed file, now deleting".format(rank), file=sys.stderr, flush=True)
        os.remove(self.vehroutes_path)
        os.remove('/project/umd_lance_fiondella/sumo_output/edgeData_{0}_{1}_{2}_{3}.xml'.format(self.disrupted, self.lmbd, self.start_time, self.end_time))

        print("Process {} deleted file, exiting".format(rank), file=sys.stderr, flush=True)

    def setup_sim(self):
        with open('vehroutes.json', 'r') as f:
            jsondata = json.load(f)

        vehicles_considered = []
        for vehicle in jsondata:
            if len(set(jsondata[vehicle]['edges']) & set(self.subnetwork_edges)) > 0:
                vehicles_considered.append(vehicle)

        self.new_demand_route = {}
        self.new_demand_depart = {}
        self.new_demand_depart_lane = {}
        self.new_demand_depart_pos = {}
        self.new_demand_depart_speed = {}
        self.new_demand_depart_vehicles = defaultdict(list)    
        self.new_demand_vehicle_type = {}
        
        for vehicle in vehicles_considered:
            self.new_demand_vehicle_type[vehicle] = jsondata[vehicle]['type']
            start = False
            for i, edge in enumerate(jsondata[vehicle]['edges']):
                if edge in self.subnetwork_edges and not start:
                    self.new_demand_route[vehicle] = [edge]
                    if i < len(jsondata[vehicle]['exitTimes']):
                        exitTimes = i
                    else:
                        exitTimes = -1
        

                    self.new_demand_depart[vehicle] = int(float(jsondata[vehicle]['exitTimes'][exitTimes]))
                    self.new_demand_depart_vehicles[int(float(jsondata[vehicle]['exitTimes'][exitTimes]))].append(vehicle)
                    start = True
                    #if i == 0:
                    #    self.new_demand_depart_lane[vehicle] = jsondata[vehicle]['departLane']
                    #    self.new_demand_depart_pos[vehicle] = jsondata[vehicle]['departPos']
                    #    self.new_demand_depart_speed[vehicle] = jsondata[vehicle]['departSpeed']
                    #else:
                    self.new_demand_depart_lane[vehicle] = 0
                    self.new_demand_depart_pos[vehicle] = 0.0
                    self.new_demand_depart_speed[vehicle] = 0.0
                elif (edge in self.subnetwork_edges and start) and i < len(jsondata[vehicle]['edges']):
                    self.new_demand_route[vehicle].append(edge)
                elif (edge not in self.subnetwork_edges and start):
                    break
    

    def close_edges(self):
       # Close appropriate edges in network for subnetwork
       for edgeID in self.edgeIDs:
           if edgeID not in set(self.subnetwork_edges):
               lanes = self.network.getEdge(edgeID).getLanes()
               for lane in lanes:
                   laneID = lane.getID()
                   traci.lane.setDisallowed(laneID, ['passenger', 'bus'])

    def setup_trips(self):
       for vehicle in self.new_demand_route:
           """
           if len(self.new_demand_route[vehicle]) > 1 and self.disrupted in self.new_demand_route[vehicle]:
               if self.disrupted != self.new_demand_route[vehicle][0] and self.disrupted != self.new_demand_route[vehicle][-1]:
                   traci.route.add(vehicle+'_route', [self.new_demand_route[vehicle][0], self.new_demand_route[vehicle][-1]])
               else:
                   if self.new_demand_route[vehicle][0] == self.disrupted:
                       traci.route.add(vehicle + '_route',
                                       [self.new_demand_route[vehicle][1], self.new_demand_route[vehicle][-1]])
                   else:
                       traci.route.add(vehicle + '_route',
                                       [self.new_demand_route[vehicle][0], self.new_demand_route[vehicle][-2]])
           elif self.new_demand_route[vehicle][0] == self.disrupted:
               disruptedEdge = self.network.getEdge(self.disrupted)
               try:
                   source = list(disruptedEdge.getIncoming().keys())[0].getID()
                   dest = list(disruptedEdge.getOutgoing().keys())[0].getID()
                   traci.route.add(vehicle + '_route', [source, dest])
               except:
                   continue 
           else:
               traci.route.add(vehicle + '_route', self.new_demand_route[vehicle])
           """
           
           if self.new_demand_route[vehicle][0] == self.disrupted:
                if self.start_time <= self.new_demand_depart[vehicle] and self.new_demand_depart[vehicle] <= self.end_time:
                    self.new_demand_depart[vehicle] = self.end_time+1
            
           traci.route.add(vehicle + '_route', self.new_demand_route[vehicle])

           try:
               traci.vehicle.add(vehicle, vehicle+'_route', depart= str(self.new_demand_depart[vehicle]),
                                 typeID=str(self.new_demand_vehicle_type[vehicle]))
           except traci.exceptions.TraCIException as e:
               print(e.getCommand())
               print(e.getType())
               print("Vehicle : " + vehicle)
               print( "Depart : {}".format(self.new_demand_depart[vehicle]))
               print("Pos : {}".format(self.new_demand_depart_pos[vehicle]))
               print(" Route : {}".format(self.new_demand_route[vehicle]))
               print("Traci Route : {}".format(traci.route.getEdges(vehicle + "_route")))



    def get_subnetwork(self):
        self.subnetwork_edges = self.net_graph.getSubnet(self.network.getEdge(self.disrupted), self.lmbd)


if __name__=="__main__":
    edge = u'--30256#0'
    lmbd = 100 
    start_time = 0
    end_time = 28800
    filename = 'test.json'
    rank = 0
    g = Graph()
    net = sumolib.net.readNet('../scenario/lust.net.xml')
    for e in net.getEdges():
        g.addEdge(e.getFromNode().getID(), e.getToNode().getID(), e.getID())
    ss = SumoSim(edge, lmbd, start_time, end_time, filename, rank, g)
    ss.run()
