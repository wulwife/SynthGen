import os

from obspy.core import UTCDateTime

from pyrocko.gf import MTSource, DCSource, LocalEngine, Target
from pyrocko.trace import Trace
from pyrocko import io

import numpy as num


class Synthetic_waveforms:

    def __init__(self, data_dir, inv_folder, inv_filename, gf_store_dir, gf_store, data_id):
        self.inv_dir = os.path.join(data_dir,inv_folder)
        self._read_inv(inv_filename)
        self._read_gf(gf_store_dir,gf_store)
        self.waveform_dir = os.path.join(data_dir, self.gf_store+'_'+data_id)
        if not os.path.isdir(self.waveform_dir):
            os.mkdir(self.waveform_dir)

    def _read_gf(self,gf_store_dir,gf_store):
        self.gf_store_path = os.path.join(gf_store_dir,gf_store)
        self.gf_store_dir=gf_store_dir
        self.gf_store=gf_store
        if not os.path.exists(self.gf_store_path):
            from pyrocko.gf import ws
            import shutil
            ws.download_gf_store(site='kinherd', store_id=self.gf_store)
            shutil.move(gf_store,self.gf_store_path)

    def _read_inv(self, inv_filename):
        from obspy import read_inventory
        self.inventory_path = os.path.join(self.inv_dir, inv_filename)
        self.inventory = read_inventory(self.inventory_path)


    def __waveform_gen(self, tor, time_window, source, event_dir, noise):
        engine = LocalEngine(store_superdirs=[self.gf_store_dir+'/'])
        for net in self.inventory:
            for sta in net:
                for cha in sta:
                    try:
                        target = Target(quantity='velocity',tmin = tor, tmax = tor + time_window,lat=float(sta.latitude),lon=float(sta.longitude),store_id=self.gf_store,codes=(net.code, sta.code, cha.location_code, cha.code ))
                        response = engine.process(source, target)
                        synthetic_trace = response.pyrocko_traces()
                        channel_id = os.path.join(event_dir, ".".join([str(net.code),str(sta.code),str(cha.location_code),str(cha.code)]))
                        if noise:
                            noise_waveform=noise[str(net.code)+'_'+str(sta.code)+'_'+str(cha.code)]
                            event_waveform=synthetic_trace[0].ydata
                            synthetic_trace[0].ydata=self.__add_noise(event_waveform, noise_waveform)
                        io.save(synthetic_trace, channel_id + ".mseed")
                    except:
                        print(str(sta) +' skipped!')

    def __add_noise(self, event_waveform, noise_waveform):
        n_synth=num.size(event_waveform)
        n_noise=num.size(noise_waveform)
        if n_synth > n_noise:
            event_waveform[:n_noise]= event_waveform[:n_noise] + noise_waveform
        elif n_synth < n_noise:
            event_waveform = event_waveform + noise_waveform[:n_synth]
        else:
            event_waveform = event_waveform + noise_waveform
        return event_waveform
    
    def __uniform_mt_dist(self, moment_norm):
        # parametrization of uniformely distributed moment tensor of norm 1
        x=num.random.rand(5)
        mnn = moment_norm*num.sqrt(x[0]* num.sqrt(x[1]))*num.cos(2*num.pi*x[2])              
        mee = moment_norm*num.sqrt(x[0]* num.sqrt(x[1]))*num.sin(2*num.pi*x[2])
        mdd = moment_norm*num.sqrt((1-x[0])* num.sqrt(x[1]))*num.cos(2*num.pi*x[3])
        mne = moment_norm*(1/num.sqrt(2))*num.sqrt((1-x[0])* num.sqrt(x[1]))*num.sin(2*num.pi*x[3])
        mnd = moment_norm*(1/num.sqrt(2))*num.sqrt(1-num.sqrt(x[1]))*num.cos(2*num.pi*x[4])
        med = moment_norm*(1/num.sqrt(2))*num.sqrt(1-num.sqrt(x[1]))*num.sin(2*num.pi*x[4])
        return mnn, mee, mdd, mne, mnd, med
    
    def __uniform_dc_dist(self):
        sk = 360*num.random.rand()
        dp = 90*num.random.rand()
        rk = -180 + 360*num.random.rand()
        return sk, dp, rk

    def __dc_source(self, lat, lon, dep, tor, mag):
        sk,dp,rk=self.__uniform_dc_dist()
        source=DCSource(lat=lat,lon=lon,depth=dep,strike=sk, dip=dp, rake=rk, magnitude=mag, time=tor)
        return source
    
    def __mt_source(self, lat, lon, dep, tor, moment_norm):
        mnn, mee, mdd, mne, mnd, med=self.__uniform_mt_dist(moment_norm)
        source = MTSource(mnn=mnn,mee=mee,mdd=mdd,mne=mne,mnd=mnd,med=med,lat=lat,lon=lon,depth=dep,time=tor)
        return source

    def __gen_source(self, event, source_type):
        tor, lat, lon, dep, mag=event
        if  source_type=='dc':
            source=self.__dc_source(lat, lon, dep, tor, mag)
        elif source_type=='mt':
            moment_norm=self.__mag2mo(mag)
            source=self.__mt_source(lat, lon, dep, tor, moment_norm)
        elif source_type=='noise':
            moment_norm=0
            source=self.__mt_source(lat, lon, dep, tor, moment_norm)
        else:
            print('source type must be dc or mt')
        return source
            
    def __mag2mo(self,Mw):
        dycm2Nm=10**-7
        M0=(10**(1.5*(Mw+10.7)))*dycm2Nm
        return M0

    def __mo2mag(self,M0):
        Nm2dycm=10**7
        Mw=(2/3)*(num.log10(M0*Nm2dycm))-10.7
        return Mw

    def generate_waveforms(self, otime, lat, lon, dep, mag, time_window, source_type, noise=[]):
        id=UTCDateTime(otime)
        tor=id.timestamp
        evid = ((str(id).split(".")[0]).replace(':','')).replace('-','')
        event=[tor, lat, lon, dep, mag]
        source=self.__gen_source(event, source_type)
        event_dir = os.path.join(self.waveform_dir, evid)
        if not os.path.isdir(event_dir):
            os.mkdir(event_dir)
        self.__waveform_gen(tor, time_window, source, event_dir, noise)



if __name__ == "__main__":

    #inv_filename = "COSEISMIQ_networks_inventory.xml"
    #data_dir='/home/francesco/hengill'
    #gfstore_dir='/home/francesco/hengill/GF_Stores'
    #gf_store='iceland'
    data_dir='/home/francesco/Jidong'
    inv_filename = 'JD*xml'
    gfstore_dir='/home/francesco/Jidong/GF_Stores'
    gf_store='jidong'
    inv_folder='response_files'

    otime='20190101T061102'
    lat=39.1
    lon=118.2
    dep=2000
    mag=2
    time_window = 15.
    highcut_freq=2
    source_type='dc'
    data_id='event_single'

    waveforms=Synthetic_waveforms(data_dir, inv_folder, inv_filename, gfstore_dir, gf_store, data_id)
    waveforms.generate_waveforms(otime, lat, lon, dep, mag, time_window, source_type)