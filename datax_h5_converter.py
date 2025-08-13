'''
SIMPLE FIL TO H5 CONVERTER for SRT data
1 - >> conda activate bliss-giovanni
2 - go to your user folder
3 - >> nohup python3 -u datax_h5_converter.py > converter.log 2>&1 &
4 - leave the program working, it will create an 'H5_datax' folder with the h5 files and a converter.log file for execution monitoring
'''

import os

#filterbank data directory
main_data_dir=f'/datax/'

# Create a list of all directories inside main_data_dir that start with '20' (all observation dates)
date_dir = [d for d in os.listdir(main_data_dir) if os.path.isdir(os.path.join(main_data_dir, d)) and d.startswith('20')]

for k in range(len(date_dir)):
    data_dir=main_data_dir + date_dir[k] + f'/GUPPI/'
    print('CONVERTER: Looking in folder '+str(k+1)+' out of '+str(len(date_dir)), flush=True)
    data_files= os.listdir(data_dir)
    print('CONVERTER: '+str(len(data_files)) + ' files found in ' + data_dir, flush=True)
    #h5 data directory (where the converted h5 files will be stored)
    data_dir_h5 = f'./H5_datax/'+date_dir[k]+f'/'
    if not os.path.exists(data_dir_h5):
        os.makedirs(data_dir_h5)

    j=0
    for i in range(len(data_files)):
        #take just the 0000 files (high spectral resolution)
        if data_files[i].endswith('0000.fil'):
            j+=1
            filepath_in = data_dir+data_files[i]
            convert_command='fil2h5 -o ' + data_dir_h5 +' '+filepath_in
            print('CONVERTER: Converting to h5 file '+str(j)+' ('+str(i+1)+' of '+str(len(data_files))+') of folder number '+str(k+1)+', named: '+str(data_files[i]), flush=True)
            data_files[i]=data_files[i].removesuffix('.fil')+'.h5'
            os.system(convert_command)

# Create a text file to log files that failed conversion
cursed_file_path = './cursed_files.txt'

with open(cursed_file_path, 'w') as cursed_file:
    cursed_file.write('Files that failed to convert:\n')

    # Open the converter.log file and parse it
    log_file_path = './converter.log'
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as log_file:
            lines = log_file.readlines()
            for line in lines:
                if 'Setting t_start = 0.000000' in line:
                    # Extract the file name from the previous line
                    prev_line = lines[lines.index(line) - 1]
                    if 'named:' in prev_line:
                        file_name = prev_line.split('named: ')[1].strip()
                        cursed_file.write(file_name + '\n')
    else:
        print('CONVERTER: Log file not found, unable to identify failed conversions.', flush=True)

base_dir=f'./H5_datax/'

#Move GC files
data_dir=f'./H5_data_GC/'
if not os.path.exists(data_dir): os.makedirs(data_dir)

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if 'BLGC' in file:
            src_path = os.path.join(root, file)
            dest_path = os.path.join(data_dir, file)
            os.rename(src_path, dest_path)

#Move TIC files
data_dir=f'./H5_data_TIC/'
if not os.path.exists(data_dir): os.makedirs(data_dir)

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if 'TIC' in file:
            src_path = os.path.join(root, file)
            dest_path = os.path.join(data_dir, file)
            os.rename(src_path, dest_path)

#Move K2-18b files
data_dir=f'./H5_data_K2-18b/'
if not os.path.exists(data_dir): os.makedirs(data_dir)

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if 'K2-18b' in file:
            src_path = os.path.join(root, file)
            dest_path = os.path.join(data_dir, file)
            os.rename(src_path, dest_path)

# CREATE YOUR OWN: change <TARGET TYPE> to your needs and uncomment

# #Move <TARGET TYPE> files
# data_dir=f'./H5_data_<TARGET TYPE>/'
# if not os.path.exists(data_dir): os.makedirs(data_dir)

# for root, dirs, files in os.walk(base_dir):
#     for file in files:
#         if '<TARGET TYPE>' in file:
#             src_path = os.path.join(root, file)
#             dest_path = os.path.join(data_dir, file)
#             os.rename(src_path, dest_path)

print('CONVERTER: All files converted and moved, goodnight✨')