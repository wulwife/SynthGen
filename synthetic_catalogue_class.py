import os
from obspy.core import UTCDateTime
import numpy as num

class Synthetic_catalogue:

    def __init__(self, data_dir, inputs, input_type='file'):
        ''' inputs can be a python dictionay, an ascii or a pkl file '''
        self.data_dir=data_dir
        if input_type=='file':
            self._read_inputfile(data_dir, inputs)
        elif input_type=='dict':
            self.inputs=inputs
        else:
            print('inputs not passed!!!')
            self.inputs=None

    def _read_inputfile(self, input_file):
        ''' inputs is a file text with the following keys n_sources,latmin, latmax
        lonmin, lonmax, depmin, depmax, tormin, tormax, magmin, magmax'''
        if input_file[-3:]=='pkl':
            import pickle
            with open(self.data_dir+'/'+input_file,'rb') as f:
                inputs = pickle.load(f)
        else:
            with open(self.data_dir+'/'+input_file,'r') as f:
                f.readline() #skip the first line
                inputs={}
                for line in f:
                    toks=line.split()
                    inputs[toks[0]]=eval(toks[1])
        self.inputs=inputs

    def _write_catalogue(self, filename):
        with open(self.data_dir+'/'+filename,'w') as f:
            f.write('OriginTime Latitude(deg) Longitude(deg) Depth(km) Magnitude \n')
            for event_id in sorted(self.events.keys()):
                tor, lat, lon, dep, mag, evtype=self.events[event_id]
                evline=' %6.4f %7.4f %4.2f %3.2f %s\n' %(lat,lon,dep/1000,mag, evtype)
                f.write(event_id+evline)

    def __gen_events(self, source_type):
        id, tor = self.__gen_evtime()
        lat, lon, dep =self.__gen_evcoords()
        mag=self.__gen_evmag()
        if source_type=='random':
            evtype=self.__gen_evtype()
        else:
            evtype=source_type
        return id, tor, lat, lon, dep, mag, evtype

    def __gen_evtime(self):
        tormin=UTCDateTime(self.inputs['tormin'])
        tormax=UTCDateTime(self.inputs['tormax'])
        id = (tormin + (tormax-tormin)*num.random.rand())
        tor=id.timestamp
        return id, tor

    def __gen_evcoords(self):
        lat = self.inputs['latmin'] + (self.inputs['latmax']-self.inputs['latmin'])*num.random.rand()
        lon = self.inputs['lonmin'] + (self.inputs['lonmax']-self.inputs['lonmin'])*num.random.rand()
        dep = self.inputs['depmin'] + (self.inputs['depmax']-self.inputs['depmin'])*num.random.rand()
        return lat, lon, dep
    
    def __gen_evmag(self):
        mag = self.inputs['magmin'] + (self.inputs['magmax']-self.inputs['magmin'])*num.random.rand()
        return mag
    
    def __gen_evtype(self):
        types=['noise', 'event']
        evtype = num.random.choice(types)
        return evtype
    
    def gen_catalogue(self, catname, source_type='random', return_object='False', seed=None):
        ''' source type must be : "random", "event" '''
        n_sources=self.inputs['n_sources']
        events={}

        for i in range(n_sources):
            id, tor, lat, lon, dep, mag, evtype=self.__gen_events(source_type)
            event_id = ((str(id).split(".")[0]).replace(':','')).replace('-','')
            events[event_id]=[tor, lat, lon, dep, mag, evtype]
        self.events=events
        self._write_catalogue(catname)

        if seed is not None:
            num.random.seed(seed)

        if return_object:
            return events

if __name__ == "__main__":
    inputs={'n_sources':100,'latmin':63.9, 'latmax':64.2, 'lonmin':-21.7, 'lonmax':-20.9, 'depmin':1000, 'depmax':15000, 
            'tormin':"2019-01-01", 'tormax':"2019-01-07", 'magmin':0.0, 'magmax':2.0}
    
    inv_filename = "COSEISMIQ_networks_inventory.xml"
    data_dir='/home/francesco/hengill'
    catname='iceland.txt'
    dataset=Synthetic_catalogue(data_dir, inputs, input_type='dict')
    dataset.gen_catalogue(catname, source_type='random', seed=11)

