from synthetics_generator_class import Synthetics_generator

inputs={'n_sources':100,'latmin':39.0, 'latmax':39.1, 'lonmin':118.2, 'lonmax':118.3, 'depmin':1000, 'depmax':10000, 
'tormin':"2019-01-01", 'tormax':"2019-01-07", 'magmin':-1.0, 'magmax':2.0}

inv_filename = "JD*.xml"
data_dir='/home/francesco/Jidong'
gfstore_dir='/home/francesco/hengill/GF_Stores'
gf_store='jidong'

time_window = 15.
buffer=5
resampling_freq=50
highcut_freq=2
event_type='event'
source_type='dc'
data_id='events_test'
parallel=False

catname='jidong_cat.txt'
dataset=Synthetics_generator(data_dir, inv_filename, gfstore_dir, gf_store, data_id)
dataset.generate_catalogue(inputs, catname, event_type)
dataset.generate_waveforms(dataset.events, time_window, buffer, resampling_freq, highcut_freq, source_type, parallel)
