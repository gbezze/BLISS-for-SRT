'''
BLISS PIPELINE for Tess Input Catalog SRT data

Make sure the H5 files are present in the data_dir folder (run datax_h5_converter.py if they are not).
Before running this script activate the conda environment: 'conda activate bliss-giovanni'
to execute in a detached way run this from terminal: nohup python3 -u BLISS_pipeline_tic.py > pipeline.log 2>&1 &
'''

import os
from turbo_seti.find_event.find_event_pipeline import find_event_pipeline
from turbo_seti.find_event.plot_event_pipeline import plot_event_pipeline
'''
 +--------------------------------------------------------+
 |        (1) set up paths and data file lists            |
 +--------------------------------------------------------+
'''

# base directory: must contain H5_data_TIC
base_dir = '/datax/users/obs/gbezze/'

# H5 data directory
data_dir = os.path.join(base_dir,f'H5_data_TIC/')

# where the DAT hits files will be stored
output_dir =  os.path.join(base_dir,f'TIC/BLISS_output/')

# where the CSV event files will be stored
events_dir=os.path.join(base_dir,f'TIC/events_output')

# where the images will be stored
image_dir =os.path.join(base_dir,f'TIC/event_plots')

data_files= os.listdir(data_dir)
data_files = [file for file in data_files if file.endswith('.h5')]
print(str(len(data_files)) + ' h5 files present in' + data_dir)

if not os.path.exists(output_dir): os.makedirs(output_dir)

'''
 +--------------------------------------------------------+
 |          (2) BLISS narrowband signal search            |
 +--------------------------------------------------------+
'''
SNR_threshold = 10
drift_rate_range = 2 #[Hz/s]
fine_channels = 0 #set to 0 for auto detect

n_analyzed_hits = 0

for i in range(len(data_files)):
   
    data_file_path = data_dir + data_files[i]
    print(data_file_path)

    hits_file = output_dir + data_files[i].removesuffix('.h5')+'.dat'    
    
    find_hits_options= f' -d cuda:0 -s '+str(SNR_threshold)+' -md -'+str(drift_rate_range)+' -MD '+str(drift_rate_range)+' --number-coarse 64 --nchan-per-coarse '+str(fine_channels)+' -o '+hits_file
    
    find_hits_command = 'bliss_find_hits ' + data_file_path + find_hits_options
    print(find_hits_command)
    print('BLISS: finding hits of scan '+str(i+1))
    os.system(find_hits_command)
    os.system('sync')  # Ensure the command is fully executed and changes are written to disk
    
    #fix BLISS DAT file whitespace bug
    #the current BLISS version prints a space instead of a tab in the header of the DAT file, which breaks turboseti_find_events
    #this has to be removed if BLISS fixed
    try:
        with open(hits_file, 'r') as file:
            lines = file.readlines()
            lines[5] = lines[5].replace(' max', '\tmax')
        with open(hits_file, 'w') as file:
            file.writelines(lines)
        print('DAT file '+str(i+1)+' whitespace fixed')
        n_analyzed_hits +=1
    except:
        #assuming that the DAT file is not found or does not have a valid header
        print('BLISS failed, skipping file '+str(i+1))
print('BLISS find hits completed for all files')
print('A total of'+str(n_analyzed_hits)+'h5 files out of ' + str(len(data_files))+'have been successfully analyzed')

'''
 +--------------------------------------------------------+
 |                   (3) build cadences                   |
 +--------------------------------------------------------+
'''

if not os.path.exists(events_dir): os.makedirs(events_dir)
if not os.path.exists(image_dir): os.makedirs(image_dir)

# Clear files in events_dir
for file in os.listdir(events_dir):
    file_path = os.path.join(events_dir, file)
    if os.path.isfile(file_path):
        os.remove(file_path)

hits_files = filter(lambda f: f.endswith(".dat"), [output_dir + f for f in os.listdir(output_dir)])
hits_files = list(hits_files)

# Group h5 file names by the fifth field separated by underscore
cadences = {}

for data_file in data_files:
    # Extract the fifth field from the file name
    TIC_name = data_file.split('_')[4]
    if (TIC_name not in cadences) and ('000000_TIC' not in data_file): #exclide duplicate ON or OFF
        cadences[TIC_name] = {'hits_files': [], 'data_files': []}
    # Add the corresponding hits and data files to the group
    cadences[TIC_name]['data_files'].append(data_file)
    cadences[TIC_name]['hits_files'].extend(
        [hits_file for hits_file in hits_files if data_file.removesuffix('.h5') in hits_file]
    )

# run find events on cadences

'''
 +--------------------------------------------------------+
 |   (4) Turboseti event search on cadences and plots     |
 +--------------------------------------------------------+
'''

event_filter=3
print_plots=True

i=0

for cadence_files in cadences.values():
    
    i+=1
    
    cadence_files['data_files'].sort()
    cadence_files['hits_files'].sort()
    
    # Create .lst files for hits and data files
    hits_list_path = os.path.join(events_dir, f'cadence_hits_{i}.lst')
    data_list_path = os.path.join(events_dir, f'cadence_data_{i}.lst')
    
    with open(hits_list_path, 'w') as hits_list_file:
        for hits_file in cadence_files['hits_files']:
            hits_list_file.write(f"{hits_file}\n")
    
    with open(data_list_path, 'w') as data_list_file:
        for data_file in cadence_files['data_files']:
            data_list_file.write(f"{data_dir}{data_file}\n")
    
    # Run the find_event_pipeline
    csvf_path = os.path.join(events_dir, f'found_event_table_{i}.csv')
    try:
        find_event_pipeline(hits_list_path,
                        data_list_path,
                        filter_threshold=event_filter,
                        number_in_cadence=len(cadence_files['hits_files']),
                        csv_name=csvf_path,
                        saving=True)
    except:
        print('FIND EVENTS FAILED for cadence '+str(i))


    if print_plots:
        if not os.path.exists(csvf_path):
            print(f"No events found. Skipping plotting.")
            continue
        else:
            try:
                print('Starting event search for cadence '+str(i))
                plot_event_pipeline(csvf_path, # full path of the CSV file built by find_event_pipeline()
                                data_list_path, # full path of text file containing the list of .h5 files
                                filter_spec=event_filter, # filter threshold
                                user_validation=False) # Non-interactive
            except Exception as e:
                print(f"Plotting failed for cadence {i}: {e}")

            # Copy all png files from data_dir to png_dir
            for file_name in os.listdir(data_dir):
                if file_name.endswith('.png'):
                    src_path = os.path.join(data_dir, file_name)
                    dest_path = os.path.join(image_dir, file_name)
                    os.rename(src_path, dest_path)

print('Pipeline completed👽')