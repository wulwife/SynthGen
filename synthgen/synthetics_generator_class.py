import os
from collections import Counter
from synthgen.synthetic_catalogue_class import Synthetic_catalogue
from synthgen.synthetic_waveforms_class import Synthetic_waveforms
from synthgen.synthetic_noise_class import Synthetic_noise


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

    def generate_waveforms(self, time_window, source_type='dc'):
        waveforms=Synthetic_waveforms(data_dir, self.inv_folder, self.inv_filename, self.gf_store_dir, self.gf_store, self.data_id)
        for otime in self.events.keys():
            _, lat, lon, dep, mag=self.events[otime]
            waveforms.generate_waveforms(otime, lat, lon, dep, mag, time_window, source_type, self.noise[otime])
        self.clean_dataset(waveforms.waveform_dir)

    def clean_dataset(self, root_dir):
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
    inputs={'n_sources':10,'latmin':39.1, 'latmax':39.2, 'lonmin':118.1, 'lonmax':118.2, 'depmin':1000, 'depmax':5000, 
    'tormin':"2024-10-20", 'tormax':"2024-10-30", 'magmin':2.0, 'magmax':3.0}

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
    data_id='event_single'
    
    starttime='20241020T000000'
    endtime='20241130T000000'

    resampling_freq=50

    network='JD'

    dataset = Synthetics_generator(data_dir, inv_folder, inv_filename, gfstore_dir, gf_store, data_id, noise_id, sds_root)
    dataset.generate_catalogue(inputs, catname)
    dataset.generate_noise(starttime, endtime, time_window, resampling_freq, highcut_freq)
    dataset.generate_waveforms(time_window, source_type)
