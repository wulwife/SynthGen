import os
from collections import Counter
from synthetic_catalogue_class import Synthetic_catalogue
from synthetic_waveforms_class import Synthetic_waveforms
from synthetic_noise_class import Synthetic_noise

class Synthetics_generator:

    def __init__(self, data_dir, inv_folder, inv_filename, gf_store_dir, gf_store, data_id, noise_id, sds_root):
        self.data_dir=data_dir
        self.inv_folder=inv_folder
        self.inv_filename=inv_filename
        self.gf_store_dir=gf_store_dir
        self.gf_store=gf_store
        self.data_id=data_id
        self.noise_id=noise_id
        self.sds_root=sds_root

    def generate_catalogue(self, inputs, catname, seed=None):
        catalogue=Synthetic_catalogue(self.data_dir, inputs, input_type='dict')
        events=catalogue.gen_catalogue(catname, True, seed)
        self.events=events

    def generate_noise(self, starttime, endtime, time_window, resampling_freq, highcut_freq):
        noisew=Synthetic_noise(self.data_dir, self.inv_folder, self.inv_filename, self.noise_id, self.sds_root)
        noisew.extract_noise(starttime, endtime, time_window, resampling_freq, highcut_freq, network)
        noise={}
        for otime in self.events.keys():
            noise[otime]=noisew.gen_noise_waveforms(otime, True)
        self.noise=noise

    def generate_event_waveforms(self, time_window, source_type='dc'):
        waveforms=Synthetic_waveforms(data_dir, self.inv_folder, self.inv_filename, self.gf_store_dir, self.gf_store, self.data_id)
        for otime in self.events.keys():
            _, lat, lon, dep, mag=self.events[otime]
            waveforms.generate_waveforms(otime, lat, lon, dep, mag, time_window, source_type, self.noise[otime])
        self.__clean_dataset(waveforms.waveform_dir)

    def generate_continuous_waveforms(self, starttime, endtime, starttime_noise, endtime_noise, time_window, resampling_freq, highcut_freq, data_if):
        noisew=Synthetic_noise(self.data_dir, self.inv_folder, self.inv_filename, self.noise_id, self.sds_root)
        waveforms=Synthetic_waveforms(data_dir, self.inv_folder, self.inv_filename, self.gf_store_dir, self.gf_store, self.data_id)
        noisew.extract_noise(starttime, endtime, time_window, resampling_freq, highcut_freq, network)
        noisew.gen_cont_noise_waveforms(starttime_noise, endtime_noise)
        for otime in self.events.keys():
            _, lat, lon, dep, mag=self.events[otime]
            waveforms.generate_waveforms(otime, lat, lon, dep, mag, time_window, source_type='dc')
        self.__add_waveform_to_noise_stream(waveforms.traces,noisew.noise_stream,data_id)
        self.__clean_dataset(waveforms.waveform_dir)

    def __add_waveform_to_noise_stream_old(self,traces,noise_stream,data_id):
        from obspy import UTCDateTime
        import numpy as num
        event_dir = os.path.join(self.data_dir,data_id)
        if not os.path.isdir(event_dir):
            os.mkdir(event_dir)
        for evid in traces.keys():
            otime=UTCDateTime(evid)
            for trn in noise_stream:
                print(trn.stats.starttime)
                itn=int((num.abs(otime-trn.stats.starttime))/trn.stats.delta)
                code=trn.stats.network+'_'+trn.stats.station+'_'+trn.stats.channel
                if code in traces[evid].keys():
                    event_waveform=traces[evid][trn.stats.network+'_'+trn.stats.station+'_'+trn.stats.channel]
                    ns=num.size(event_waveform)
                    trn.data[itn:itn+ns]=trn.data[itn:itn+ns]+event_waveform
        noise_stream.write(event_dir+'/'+data_id+'.mseed', format='MSEED')
    
    def __add_waveform_to_noise_stream(self, traces, noise_stream, data_id):
        from obspy import UTCDateTime
        import numpy as num
        event_dir = os.path.join(self.data_dir, data_id)
        if not os.path.isdir(event_dir):
            os.mkdir(event_dir)

        for evid in traces.keys():
            otime = UTCDateTime(evid)
        
            for trn in noise_stream:
                # Calculate time index for the waveform insertion
                itn = int((num.abs(otime - trn.stats.starttime)) / trn.stats.delta)
    
                # Build the waveform code to match with the event data
                code = f"{trn.stats.network}_{trn.stats.station}_{trn.stats.channel}"
            
                if code in traces[evid].keys():
                    # Get the event waveform for the current trace
                    event_waveform = traces[evid][code]
                    ns = num.size(event_waveform)
                
                    # Check if the index and array length allow safe modification
                    if itn + ns <= len(trn.data):
                        trn.data[itn:itn + ns] += event_waveform
                    else:
                        print(f"Warning: The waveform exceeds available data length in trace {trn.id}")
            
        # Write the modified noise stream to a file
        noise_stream.write(os.path.join(event_dir, f"{data_id}.mseed"), format='MSEED')
    


    def __clean_dataset(self, root_dir):
        for foldername, _, filenames in os.walk(root_dir):
            station_counts = Counter()
            file_station_map = {}

            for filename in filenames:
                if filename.endswith(".mseed"):
                    station = filename.split('.')[1]
                    station_counts[station] += 1
                    file_station_map[filename] = station

            # Identify and remove files for stations with less than three occurrences
            for filename, station in file_station_map.items():
                if station_counts[station] < 3:
                    filepath = os.path.join(foldername, filename)
                    print(f"Removing: {filepath}")
                    os.remove(filepath)



if __name__ == "__main__":
    inputs={'n_sources':4,'latmin':39.1, 'latmax':39.2, 'lonmin':118.1, 'lonmax':118.2, 'depmin':1000, 'depmax':5000, 
    'tormin':"20241020T000000", 'tormax':"20241020T000200", 'magmin':1.0, 'magmax':2.0}

    inv_filename = "COSEISMIQ_networks_inventory.xml"
    data_dir='/home/francesco/hengill'
    gfstore_dir='/home/francesco/hengill/GF_Stores'
    gf_store='iceland'
    catname='iceland.txt'


    data_dir='/home/francesco/Jidong'
    inv_filename = 'JD*xml'
    gfstore_dir='/home/francesco/Jidong/GF_Stores'
    gf_store='jidong'
    inv_folder='response_files'
    noise_id='noise_jidong'
    sds_root='/home/francesco/Jidong/DATI'
    catname='jidong.txt'

    otime='20190101T061102'
    lat=39.1
    lon=118.2
    dep=2000
    mag=2
    time_window = 20.
    highcut_freq=2
    source_type='dc'
    data_id='continuous'
    
    starttime='20241020T000000'
    endtime='20241130T000000'
    starttime_noise="20241020T000000"
    endtime_noise="20241020T000240"

    resampling_freq=50

    network='JD'

    dataset=Synthetics_generator(data_dir, inv_folder, inv_filename, gfstore_dir, gf_store, data_id, noise_id, sds_root)
    dataset.generate_catalogue(inputs, catname)
    #dataset.generate_noise(starttime, endtime, time_window, resampling_freq, highcut_freq)
    #dataset.generate_event_waveforms(time_window, source_type)
    dataset.generate_continuous_waveforms(starttime, endtime, starttime_noise, endtime_noise, time_window, resampling_freq, highcut_freq, data_id)