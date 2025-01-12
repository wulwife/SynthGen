from synthetics_generator_class import Synthetics_generator

inputs={'n_sources':2500,'latmin':63.9, 'latmax':64.2, 'lonmin':-21.7, 'lonmax':-20.9, 'depmin':1000, 'depmax':15000, 
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
data_id='noise'
parallel=False

inv_filename = "COSEISMIQ_networks_inventory.xml"
data_dir='/home/francesco/hengill'
catname='iceland.txt'
dataset=Synthetics_generator(data_dir, inv_filename, gfstore_dir, gf_store, data_id)
dataset.generate_catalogue(inputs, catname, event_type)
dataset.generate_waveforms(dataset.events, time_window, buffer, resampling_freq, highcut_freq, source_type, parallel)
