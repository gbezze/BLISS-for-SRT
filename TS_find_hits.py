'''
TURBO SETI FIND HITS SCRIPT

Before running this script activate the conda environment: 'conda activate bliss-giovanni'
to execute in a detached way run this from terminal: nohup python3 -u TS_find_hits.py > turboseti.log 2>&1 &
'''
import os
import numpy as np
from turbo_seti.find_doppler.find_doppler import FindDoppler

data_dir = f'/datax/users/obs/gbezze/H5_data_TIC/'
data_files= os.listdir(data_dir)
data_files = [file for file in data_files if file.endswith('.h5')]
print(str(len(data_files)) + ' h5 files present in' + data_dir)

SNR_threshold = 10
drift_rate_range = 2 #[Hz/s]

output_dir = f'/datax/users/obs/gbezze/TS_output/'
if not os.path.exists(output_dir): os.makedirs(output_dir)

for i in range(len(data_files)):
    data_file_path = data_dir + data_files[i]
    last_computed_dat_path=output_dir+data_files[min(i,len(data_files))-1].replace('h5','dat')
    print('Turboseti: finding doppler of file '+str(i)+': '+str(data_files[i]))
    try:
        TS_hits=FindDoppler(data_file_path, max_drift=drift_rate_range, min_drift=0, snr=10, out_dir=output_dir)
        TS_hits.search()
    except:
        print('Cursed file encountered:'+data_file_path)

#NOTE:
#This is extremely slow, there is a way to run it in the GPU but it didn't work for me and it wasn't important to do it fast for my project.
#If you want to try running it on the GPU it it shouldn't be too difficult