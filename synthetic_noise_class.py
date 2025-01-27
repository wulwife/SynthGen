import os
import numpy as num
from obspy.core import read, UTCDateTime

class Synthetic_noise:

    def __init__(self, data_dir, inv_folder, inv_filename, noise_id, sds_root):
        self.sds_root=sds_root
        self.data_dir=data_dir
        self.inv_dir = os.path.join(data_dir,inv_folder)
        self._read_inv(inv_filename)
        self.noise_dir = os.path.join(data_dir,noise_id)
        if not os.path.isdir(self.noise_dir):
            os.mkdir(self.noise_dir)
        self.real_noise=None

    def _read_inv(self, inv_filename):
        from obspy import read_inventory
        self.inventory_path = os.path.join(self.inv_dir, inv_filename)
        self.inventory = read_inventory(self.inventory_path)
        self._get_sensitivity_full_network()

    def _get_sensitivity_full_network(self):
        sensitivity = {}
        avg_sens = []
        for net in self.inventory:
            for sta in net:
                for cha in sta:
                    invcode = f"{net.code}.{sta.code}.{cha.location_code}.{cha.code}"
                    try:
                        if cha.response and cha.response.instrument_sensitivity:
                            sens = cha.response.instrument_sensitivity.value
                            sensitivity[invcode] = sens
                            avg_sens.append(sens)
                        else:
                            print(f"No sensitivity information for {invcode}")
                    except Exception as e:
                        print(f"Error extracting sensitivity for {invcode}: {e}")
    
        self.sensitivity = sensitivity
        self.avg_sens = num.mean(avg_sens) if avg_sens else 1

    def __get_sensitivity(self, invcode):
        if invcode in self.sensitivity.keys():
            sensitivity=self.sensitivity[invcode]
        else:
            sensitivity= self.avg_sens
        return sensitivity

    def __extract_noise(self, tini_glob, tend_glob, noise_win, resampling_freq, highcut_freq, network):
        from obspy.clients.filesystem.sds import Client
        client=Client(self.sds_root, sds_type='D', format='MSEED', fileborder_seconds=30, fileborder_samples=5000)
        real_noise={}
        tiniglob=UTCDateTime(tini_glob)
        tendglob=UTCDateTime(tend_glob)
        st = client.get_waveforms(network, "*", "*", "[BHE]H[ENZ]", tiniglob, tendglob, sds_type='D') #da cambiare
        for tr in st:
            tini=tr.stats.starttime
            tr.trim(tini,tini+3*noise_win)
            tr.detrend('demean')
            tr.resample(resampling_freq, no_filter=True)
            tr.filter('highpass',freq=highcut_freq)
            tr.trim(tini+noise_win,tini+2*noise_win)
            trid= tr.stats.network+'_'+tr.stats.station+'_'+tr.stats.channel
            invcode=tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.location+'.'+tr.stats.channel
            real_noise[trid]=tr.data/self.__get_sensitivity(invcode)
            tr.stats.starttime=tiniglob
        self.noise_stream=st
        self.real_noise=real_noise
    
    def __model_noise(self):
        noise={}
        for trid in self.real_noise.keys():
            trace=self.real_noise[trid]
            try:
                ftrace=num.fft.rfft(trace)
                phases=-num.pi + 2*num.pi*num.random.rand(num.size(ftrace))
                ftrace=num.abs(ftrace)*num.exp(-1j*phases)
                model_noise=num.fft.irfft(ftrace)
            except:
                model_noise=num.zeros(num.size(trace))
            noise[trid]=model_noise
        return noise
    
    def __write_noise_waveform(self, noise, starttime):
        tini=UTCDateTime(starttime)
        if not os.path.isdir(self.noise_dir+'/'+starttime):
            os.mkdir(self.noise_dir+'/'+starttime)
        st=self.noise_stream
        for tr in st:
            tr.stats.starttime=tini
            trid= tr.stats.network+'_'+tr.stats.station+'_'+tr.stats.channel
            tr.data=noise[trid]
            tr.write(self.noise_dir+'/'+starttime+'/'+trid+'.mseed', format='MSEED')
    
    def gen_noise_waveforms(self, starttime, endtime, time_window, resampling_freq, highcut_freq, network):
        if not self.real_noise:
            self.__extract_noise(starttime, endtime, time_window, resampling_freq, highcut_freq, network)
        noise=self.__model_noise()
        self.__write_noise_waveform(noise, starttime)
        return noise

if __name__ == "__main__":

    data_dir='/home/francesco/Jidong'
    inv_filename = 'JD*xml'
    inv_folder='response_files'
    noise_id='noise_jidong'
    sds_root='/home/francesco/Jidong/DATI'
    
    starttime='20241020T000100'
    endtime='20241130T010000'

    time_window=60
    resampling_freq=50

    highcut_freq=1
    network='JD'

    jdnoise=Synthetic_noise(data_dir, inv_folder, inv_filename, noise_id, sds_root)
    jdnoise.gen_noise_waveforms(starttime, endtime, time_window, resampling_freq, highcut_freq, network)
    starttime='20241020T000500'
    jdnoise.gen_noise_waveforms(starttime, endtime, time_window, resampling_freq, highcut_freq, network)

