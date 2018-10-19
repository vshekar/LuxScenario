from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey

Base = declarative_base()

class Edges(Base):
    __tablename__ = 'edges'
    id = Column(Integer, primary_key=True)
    edge_name = Column(String)

class Trips(Base):
    __tablename__ = 'trips'

    id = Column(Integer, primary_key=True)
    vehicle = Column(String)
    leg = Column(Integer)
    edge = Column(Integer, ForeignKey("edges.id"), nullable=False)
    time = Column(Integer)

class TravelTimes(Base):
    __tablename__ = 'travel_times'
    id = Column(Integer, primary_key=True)
    trip = Column(Integer, ForeignKey("trips.id"), nullable=False)
    travel_time = Column(Integer)