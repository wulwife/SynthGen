import os
from collections import Counter
from synthetic_catalogue_class import Synthetic_catalogue
from synthetic_waveforms_class import Synthetic_waveforms

class Synthetics_generator:

    def __init__(self, data_dir, inv_filename, gf_store_dir, gf_store, data_id):
        self.data_dir=data_dir
        self.gf_store_dir=gf_store_dir
        self.gf_store=gf_store
        self.inv_filename=inv_filename
        self.data_id=data_id

    def generate_catalogue(self, inputs, catname, event_type='random', seed=None):
        catalogue=Synthetic_catalogue(self.data_dir, inputs, input_type='dict')
        events=catalogue.gen_catalogue(catname, event_type, True, seed)
        self.events=events

    def generate_waveforms(self, events, time_window, buffer, resampling_freq, highcut_freq, source_type='dc', parallel=False):
        waveforms=Synthetic_waveforms(self.data_dir, self.inv_filename, self.gf_store_dir, self.gf_store, self.data_id)
        if parallel:
            waveforms.generate_waveforms_parallel(events, time_window, buffer, resampling_freq, highcut_freq, source_type)
        else:
            waveforms.generate_waveforms(events, time_window, buffer, resampling_freq, highcut_freq, source_type)
        self.clean_dataset(waveforms.waveform_dir)

    def clean_datatet(self, root_dir):
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
    inputs={'n_sources':100,'latmin':63.9, 'latmax':64.2, 'lonmin':-21.7, 'lonmax':-20.9, 'depmin':1000, 'depmax':15000, 
    'tormin':"2019-01-01", 'tormax':"2019-01-07", 'magmin':0.0, 'magmax':2.0}

    inv_filename = "COSEISMIQ_networks_inventory.xml"
    data_dir='/home/francesco/hengill'
    gfstore_dir='/home/francesco/hengill/GF_Stores'
    gf_store='iceland'

    time_window = 15.
    buffer=5
    resampling_freq=50
    highcut_freq=2
    event_type='noise'
    source_type='dc'
    data_id='noise_parallel'
    parallel=True

    inv_filename = "COSEISMIQ_networks_inventory.xml"
    data_dir='/home/francesco/hengill'
    catname='iceland.txt'
    dataset=Synthetics_generator(data_dir, inv_filename, gfstore_dir, gf_store, data_id)
    dataset.generate_catalogue(inputs, catname, event_type)
    dataset.generate_waveforms(dataset.events, time_window, buffer, resampling_freq, highcut_freq, source_type, parallel)


