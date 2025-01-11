import os

from obspy.core import UTCDateTime

from pyrocko.gf import MTSource, DCSource, LocalEngine, Target
from pyrocko.trace import Trace
from pyrocko import io

import numpy as num


class Synthetic_waveforms:

    def __init__(self, data_dir, inv_filename, gf_store_dir, gf_store, data_id):
        self._read_inv(data_dir,inv_filename)
        self._read_gf(gf_store_dir,gf_store)
        self.waveform_dir = os.path.join(self.data_dir, self.gf_store+'_'+data_id)
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

    def _read_inv(self,data_dir,inv_filename):
        from obspy import read_inventory
        self.data_dir=data_dir
        self.inventory_path = os.path.join(data_dir, inv_filename)
        self.inventory = read_inventory(self.inventory_path)

    def __waveform_gen(self, tor, time_window, source, noise, event_dir):
        engine = LocalEngine(store_superdirs=[self.gf_store_dir+'/'])
        for net in self.inventory:
            for sta in net:
                for cha in sta:
                    if str(net.code)+'_'+str(sta.code)+'_'+str(cha.code) in noise.keys():
                        target = Target(quantity='velocity',tmin = tor, tmax = tor + time_window,lat=float(sta.latitude),lon=float(sta.longitude),store_id=self.gf_store,codes=(net.code, sta.code, cha.location_code, cha.code ))
                        response = engine.process(source, target)
                        synthetic_trace = response.pyrocko_traces()
                        event_waveform=synthetic_trace[0].ydata
                        noise_waveform=noise[str(net.code)+'_'+str(sta.code)+'_'+str(cha.code)]
                        channel_id = os.path.join(event_dir, ".".join([str(net.code),str(sta.code),str(cha.location_code),str(cha.code)]))
                        synthetic_trace[0].ydata=self.__add_noise(event_waveform, noise_waveform)
                        io.save(synthetic_trace, channel_id + ".mseed")

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

    def __get_sensitivity(self, events):
        tinv=sorted(events.keys())[-1]
        tini=UTCDateTime(tinv)
        sensitivity={}
        avg_sens=[]
        for net in self.inventory:
            for sta in net:
                for cha in sta:
                    invcode=str(net.code)+'.'+str(sta.code)+'.'+str(cha.location_code)+'.'+str(cha.code)
                    try:
                        resp=self.inventory.get_response(invcode, tini)
                        sens=resp.instrument_sensitivity.value
                        sensitivity[invcode]=sens
                        avg_sens.append(sens)
                    except:
                        pass
        self.sensitivity=sensitivity
        self.avg_sens=num.mean(num.array(avg_sens))
    
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
        tor, lat, lon, dep, mag, evtype=event
        if  evtype=='event' and source_type=='dc':
            source=self.__dc_source(lat, lon, dep, tor, mag)
        elif evtype=='event' and source_type=='mt':
            moment_norm=self.__mag2mo(mag)
            source=self.__mt_source(lat, lon, dep, tor, moment_norm)
        elif evtype=='noise':
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
    
    def __extract_real_noise(self, evid, time_window, buffer, resampling_freq, highcut_freq, sds_root='/media/francesco/LaCie/COSEISMIQ'):
        from obspy.clients.filesystem.sds import Client
        client=Client(sds_root, sds_type='D', format='MSEED', fileborder_seconds=30, fileborder_samples=5000)
        real_noise={}
        tini=UTCDateTime(evid)
        st = client.get_waveforms("[2O][CN]", "*", "*", "[BHE]H[ENZ]", tini-buffer, tini+time_window+buffer, sds_type='D')
        st.detrend('demean')
        st.merge(method=0,fill_value=0)
        st.resample(resampling_freq, no_filter=True)
        st.filter('highpass',freq=highcut_freq)
        st.trim(tini,tini+time_window)
        for tr in st:
            trid= tr.stats.network+'_'+tr.stats.station+'_'+tr.stats.channel
            invcode=tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.location+'.'+tr.stats.channel
            if invcode in self.sensitivity.keys():
                real_noise[trid]=tr.data/self.sensitivity[invcode]
            else:
                real_noise[trid]=tr.data/self.avg_sens
        return real_noise

    def _model_noise(self, evid, time_window, buffer, resampling_freq, highcut_freq):
        noise={}
        real_noise=self.__extract_real_noise(evid, time_window, buffer, resampling_freq, highcut_freq)
        for trid in real_noise.keys():
            trace=real_noise[trid]
            try:
                ftrace=num.fft.rfft(trace)
                phases=-num.pi + 2*num.pi*num.random.rand(num.size(ftrace))
                ftrace=num.abs(ftrace)*num.exp(-1j*phases)
                model_noise=num.fft.irfft(ftrace)
            except:
                model_noise=num.zeros(num.size(trace))
            noise[trid]=model_noise
        return noise

    def generate_waveforms(self, events, time_window, buffer, resampling_freq, highcut_freq, source_type='dc'):
        self.__get_sensitivity(events)
        for evid in events.keys():
            event_dir = os.path.join(self.waveform_dir, evid)
            if not os.path.isdir(event_dir):
                os.mkdir(event_dir)
            tor=events[evid][0]
            source=self.__gen_source(events[evid], source_type)
            noise=self._model_noise(evid, time_window, buffer, resampling_freq, highcut_freq)
            self.__waveform_gen(tor, time_window, source, noise, event_dir)

    def generate_single_event(self, otime, lat, lon, dep, mag, evtype, time_window, buffer, resampling_freq, highcut_freq, source_type):
        id=UTCDateTime(otime)
        tor=id.timestamp
        evid = ((str(id).split(".")[0]).replace(':','')).replace('-','')
        events={evid : [tor, lat, lon, dep, mag, evtype]}
        source=self.__gen_source(events[evid], source_type)
        self.__get_sensitivity(events)
        noise=self._model_noise(evid, time_window, buffer, resampling_freq, highcut_freq)
        event_dir = os.path.join(self.waveform_dir, evid)
        if not os.path.isdir(event_dir):
            os.mkdir(event_dir)
        self.__waveform_gen(tor, time_window, source, noise, event_dir)

    def _process_event(self, args):
        evid, event, time_window, buffer, resampling_freq, highcut_freq, source_type = args
        event_dir = os.path.join(self.waveform_dir, evid)
        if not os.path.isdir(event_dir):
            os.mkdir(event_dir)
        tor = event[0]
        source = self.__gen_source(event, source_type)
        noise = self._model_noise(evid, time_window, buffer, resampling_freq, highcut_freq)
        self.__waveform_gen(tor, time_window, source, noise, event_dir)

    def generate_waveforms_parallel(self, events, time_window, buffer, resampling_freq, highcut_freq, source_type='dc'):
        from multiprocessing import Pool
        self.__get_sensitivity(events)
        
        # Prepare arguments for parallel processing
        args = [
            (evid, events[evid], time_window, buffer, resampling_freq, highcut_freq, source_type)
            for evid in events.keys()
        ]
        
        # Use multiprocessing Pool for parallelism
        with Pool(processes=os.cpu_count()) as pool:
            pool.map(self._process_event, args)



if __name__ == "__main__":

    inv_filename = "COSEISMIQ_networks_inventory.xml"
    data_dir='/home/francesco/hengill'
    gfstore_dir='/home/francesco/hengill/GF_Stores'
    gf_store='iceland'


    otime='20190101T061102'
    lat=64.1
    lon=-21.3
    dep=5000
    mag=2
    time_window = 15.
    buffer=5
    resampling_freq=50
    highcut_freq=2
    event_type='noise'
    source_type='dc'
    data_id='noise_single'

    inv_filename = "COSEISMIQ_networks_inventory.xml"
    data_dir='/home/francesco/hengill'
    catname='iceland.txt'
    waveforms=Synthetic_waveforms(data_dir, inv_filename, gfstore_dir, gf_store, data_id)
    waveforms.generate_single_event(otime, lat, lon, dep, mag, event_type, time_window, buffer, resampling_freq, highcut_freq, source_type)