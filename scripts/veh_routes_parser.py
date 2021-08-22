import xml.etree.ElementTree as ET

f = ET.parse('../scenario/DUARoutes/local.0.rou.xml')
root = f.getroot()

vehroutes = {}


for vehicle in root:
    id = vehicle.attrib['id']
    veh_type = vehicle.attrib['type']
    
