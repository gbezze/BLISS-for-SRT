# VS code + jupyter notebook BLISS setup in blc00/blc01

An user-friendly way to use and develop BLISS scripts is via jupyter notebooks in VS code. This requires some effort at first but it's easy to redo once it's set up.

1. First, we have to edit the SSH configuration file to set up the chain of SSH jumps without repeating the process manually everytime.
We open the `config` file located in `C:\Users\[username]\.ssh\config`, or on VScode CTRL+SHIFT+P → Remote SSH: connect to host → Configure SSH host and add the following lines:
    ```
    Host natsrt
        HostName natsrt.srt.inaf.it
        User USERNAME # <-- your natsrt username
        ForwardX11Trusted yes
        Compression yes

    Host dorian
        HostName dorian
        User bl
        ProxyJump natsrt
        ForwardX11Trusted yes
        Compression yes

    Host obs
        HostName 192.168.100.60
        User obs
        ProxyJump dorian
        ForwardX11Trusted yes
        Compression yes

    Host seti0
        HostName blc00
        User obs
        ProxyJump obs
        ForwardX11Trusted yes
        Compression yes

    Host seti1
        HostName blc01
        User obs
        ProxyJump obs
        ForwardX11Trusted yes
        Compression yes
    ```

2. Now to connect to `blc0` or `blc1` we just open the command palette with `CTRL+SHIFT+P`, run "Remote-SSH: connect to host" and select `seti0` or `seti1`. Select Linux as the remote OS whenever asked.
   
3. >This step can be ignored if one day the `blc` server gets updated.

    The SSH connection might not work due to the server not meeting the VS code prerequisites on `glibc`. If this is the case the simplest soulution I've found is to downgrade VS code to the 1.98 version available [here](https://code.visualstudio.com/updates/v1_98) and disable the VS code automatic update (File → Preferences → Settings → set 'Update: Mode' to 'manual') otherwise you would need to reinstall the old version every time you boot VS code. This will still give you a popup saying that the server is not supported but it can be just ignored.

4. Insert the passwords for the various accounts and press "yes" to the trusted author popups.

5. Once the SSH has connected, go to Files → Open Folder and select the working directory (for example `datax/users/obs/gbezze`) and create a new `.ipynb` file or open an existing one
      
6. Run it selecting the `bliss-giovanni` kernel from the list of environments (you might need to install `ipykernel`).

# SRT data analysis with BLISS 

In this section the complete pipeline from raw data to *events* is illustrated. The way it's been implemented is not perfect, but it's what I've came up with given the software, hardware and time limitatios that I had. In the future it could be simplified and optimized for better performance.

## Observations and their storage

The SRT is able to produce much more data than the servers could permanently store. The raw baseband voltages once recorded are they are shortly after converted in *filterbank files*, which are split between `blc0` or `blc1` and consist in the magnitude of the fourier transform, at various spectral and temporal resolution indicated by the last part of the filename:
* *0000.fil*: High spectral resolution and low temporal resolution.
* *0001.fil*: Low spectral resolution and high temporal resolution.
* *0002.fil*: Something in between the other two.

The files are stored in `blc0` or `blc1`, depending on the frequency band, and are organized in folders depending on the date of acquisition (for example, the folder 20250201 contains observations made in the 1st of Febraury 2025). Different naming schemes are used for different target types, the ones that we are interested in are:

* **Galactic center fields** (1467 files): The observed field is a letter representing the angular distance from the center + a two digit number that increase counter-clockwise (see image below).
  
    <img src=./guide_images/gc_fields.png width=400>

* **TESS Input Catalog pointings** (556 files): These ones have the TIC name and can be ON or OFF. ON observations point the target, OFF observations point to a different direction but are made in between ON ones. This is done to be able to reject signals that are not coming from the target direction.

## H5 Conversion

BLISS works only on h5 files, so it's necessary to convert them before analysis: this is done with the terminal command `fil2h5`.

The script `datax_h5_converter.py` takes care of this, specifically it does the following:

1. selects all high spectral resolution .fil files in `/datax/` and its date subfolders.
2. converts them, saving the .h5 file in `./H5_datax/` in a subfolder with the same date as the one in `/datax/`. The file name stays the same except the extension. 
3. Creates a txt file containing all the names of files that were unable to be converted.
4. moves all the galactic center observations into the `./H5_datax_GC` folder and all the TIC observations into `./H5_datax_TIC`
   
This script is supposed to be run in a detached termial with the command:

```bash
nohup python3 -u datax_h5_converter.py > converter.log 2>&1 &
```
otherwise step 3 will not work. The detached terminal is useful also because it can take hours to complete conversion, and in this way the process can be left running.

For reasons that are still unclear to me, a small fraction of the files (the *cursed files*) cannot be converted. This is the error message that appears:
```log
blimpy.io.base_reader WARNING  Setting t_start = 0.000000,since t_start not given or not valid.
```
Ideally this issue would have been resolved but it wasn't a priority for me because the number of files for which it happens is really low in proportion to the rest. The list of files is:

```
BLC00:

guppi_60784_00508_009035_BLGCsurv_SRT_Kband_C09_0001.0000.h5
guppi_60784_22446_000000_none_0001.0000.h5
guppi_60784_15556_000000_BLGCsurv_SRT_Kband_A00_0001.0000.h5
guppi_60788_68334_001984_3c286_0001.0000.h5
guppi_60788_76541_000000_3c286_0001.0000.h5
guppi_60847_72402_495114_3C286_CS_0001.0000.h5
guppi_60847_72423_495232_3C286_CS_0001.0000.h5
guppi_60847_81304_544859_3C286_CS_0001.0000.h5
guppi_60705_58646_000000_TIC440100539_ON_0001.0000.h5
guppi_60706_17450_000000_TIC424733642_OFF_0001.0000.h5
guppi_60713_64557_000000_3c286_0001.0000.h5
guppi_60787_00810_002179_3c286_0001.0000.h5
guppi_60789_20867_000000_BeamPark_0001.0000.h5
guppi_60790_21271_000000_BeamPark_0001.0000.h5
guppi_60846_71989_000000_3C286_CS_0001.0000.h5
guppi_60846_72301_011754_3C286_CS_0001.0000.h5
guppi_60846_72260_011524_3C286_CS_0001.0000.h5
guppi_60848_73484_983958_3C286_CS_0001.0000.h5
guppi_60848_73505_984076_3C286_CS_0001.0000.h5
guppi_60848_73531_984221_3C286_CS_0001.0000.h5
guppi_60848_73554_000000_BLGCsurv_SRT_Kband_D01_0001.0000.h5
guppi_60848_84990_1048252_3C286_CS_0001.0000.h5
guppi_60848_84940_1047978_3C286_CS_0001.0000.h5
guppi_60849_73438_007432_3C286_CS_0001.0000.h5
guppi_60849_81667_000000_3C286_on_0001.0000.h5
guppi_60849_73508_000000_BeamPark_0001.0000.h5
guppi_60849_73485_007695_3C286_CS_0001.0000.h5


BLC01:

guppi_60788_68334_001984_3c286_0001.0000.fil
guppi_60788_76541_000000_3c286_0001.0000.fil
guppi_60789_20867_000000_BeamPark_0001.0000.fil
guppi_60847_72402_495114_3C286_CS_0001.0000.fil
guppi_60847_72423_495232_3C286_CS_0001.0000.fil
guppi_60847_81304_544859_3C286_CS_0001.0000.fil
guppi_60848_73484_983958_3C286_CS_0001.0000.fil
guppi_60848_73505_984076_3C286_CS_0001.0000.fil
guppi_60848_73531_984221_3C286_CS_0001.0000.fil
guppi_60848_73554_000000_BLGCsurv_SRT_Kband_D01_0001.0000.fil
guppi_60848_84940_1047978_3C286_CS_0001.0000.fil
guppi_60848_84940_1047978_3C286_CS_0001.0000.fil
guppi_60848_84990_1048252_3C286_CS_0001.0000.fil
guppi_60706_17450_000000_TIC424733642_OFF_0001.0000.fil
guppi_60713_64557_000000_3c286_0001.0000.fil
guppi_60784_00508_009035_BLGCsurv_SRT_Kband_C09_0001.0000.fil
guppi_60784_22446_000000_none_0001.0000.fil
guppi_60784_15556_000000_BLGCsurv_SRT_Kband_A00_0001.0000.fil
guppi_60787_00780_002011_3c286_0001.0000.fil
guppi_60787_00810_002179_3c286_0001.0000.fil
guppi_60790_21271_000000_BeamPark_0001.0000.fil
guppi_60846_71989_000000_3C286_CS_0001.0000.fil
guppi_60846_72260_011524_3C286_CS_0001.0000.fil
guppi_60849_73438_007432_3C286_CS_0001.0000.fil
guppi_60849_73508_000000_BeamPark_0001.0000.fil
guppi_60849_73485_007695_3C286_CS_0001.0000.fil
guppi_60705_58646_000000_TIC440100539_ON_0001.0000.fil
```
So in total 6 GC observations and 4 TIC ones.

## BLISS Narrowband signal detection

The h5 files are analyzed by the `bliss-find-hits` commands. The following parameters have been used:

* SNR threshold: $10$
* Drift rate range: $\pm 2$ Hz/s
* Number of coarse channels: $64$
* Number of fine channels per coarse: $2^{20}$ (set to 0 for auto-detect)

The low drift rate range is imposed by the GPU memory: at the best drift rate resolution **drift rate ranges above ±2.7 Hz/s make BLISS run out of memory**, so the standard ±4 Hz/s are not feasable. A workaround could be to split the positive and negative drift rates in two consecutive searches.

The full command reads:
```bash
bliss-find-hits -d cuda:0 -s 10 -md -2 -MD 2 --number-coarse 64 --nchan-per-coarse 0 -o 'H5_FILENAME.dat'
```
This is done automatically for all GC or TIC files in sections 1 and 2 of `BLISS_pipeline.py`. 

The output is a .dat file which contains the *hits* (narrowband signals) in a table, with a 9 line header containing informations about the file followed by tab-separated columns of numerical values of parameters for the hits. Each row corresponds to a hit and the field names of the columns are contained in the 8th line of the header. The imporant ones are:

* **Column 2** `Drift_Rate` - Drift rate in Hz/s of the hit.
* **Column 3** `SNR` - Signal to noise ratio.
* **Column 7** `freq_start` - Signal frequency in MHz at the start of observation.
* **Column 8** `freq_end` - Signal frequency in MHz at the end of observations.
* **Column 12** - This unnamed field (present only in BLISS-processed files) contains the width of the signal in bins (frequency resolution of the h5 file).

Apart from column 12, this DAT output has the same structure as the one that TurboSeti produces, with a tiny but important difference. In the 6th line of the header, BLISS separates the 'DELTAF (Hz)' field and the 'max_drift_rate' with a space (`' '`) while the correct way to do that (the way TurboSeti does it) is to use a tab (`'\t'`):

>*BLISS header*:
>```
>#...                       ↓
>#... DELTAF(Hz):  -2.793968 max_drift_rate: 3.6939406 ...
>#...
>```
>*Turboseti header*:
>```
>#...                        ↓
>#... DELTAF(Hz):  -2.793968    max_drift_rate: 3.6939406 ...
>#...
>```

 **This breaks the TurboSeti event search and has to be fixed for each DAT file**, which in the pipeline is done with the lines:
 ```python
 # hits_file is the DAT file
 with open(hits_file, 'r') as file:
            lines = file.readlines()
            lines[5] = lines[5].replace(' max', '\tmax')
 ```
 
 ## Building cadences

The SRT is designed so that the receiver is ideally sensitive to the radiation coming from where the antenna is pointed to (the antenna 'main lobe') and nowhere else, however the rejection of off-axis sources it's not perfect and unwanted signals coming from other directions can be picked up by if they are sufficiently strong (which is often the case since our aim is to observe signals from half the galaxy away!).
For this reason it's not enough to find hits in one observations, to see if the signal is really coming from the field of view the observations are done in sequences of 6, alternating between pointing at the targets (ON scans) and away from it (OFF scans): if a signal is present only in the ON scans with a coherent drift rate and is not present in the OFF scans then it means that it definetly comes from the target.

The sequences of 6 observations are called *cadences*, the observations that compose them are referred to as *scans* and when a signal passes the ON-OFF test is called an *event*. Once the scans have been analyzed with BLISS, the DAT files need to be grouped in cadences to see if events are present, and this in theory would be very easy to with a naive algorithm that just takes groups of 6 consecutive scans. However, this cannot be done that naively because of the following reasons:
* Some cadences are not 6-scans long, but as low as 2-scans if the observations had to stop due to external factors.
* The cursed files do not produce any DAT file.
* Calibration and non-SETI observations are also present in `datax/`.
* Any type of deviation from the '6-scan periodicity' of the file sequence would throw 'out of phase' the naive algorithm.

For these reasons the cadences are built by more robust algorithms in section 3 of `BLISS_pipeline.py`, depending on the type of target.

### TIC targets

These targets are relatively easy because they contain `[timestamp]_[ticID]_ON` or `[timestamp]_[ticID]_OFF` in the name and every target has just one cadence. The only complication arises with some occasions in which an ON or OFF observations is repeated: when this happens the first file substitutes '000000' to the last field of the timestamp. The cadence building algorithm is structured like this:

1. Extract the TIC ID from the file name (5th field in the name separated by `_`).
2. Group the files in cadences by TIC ID.
3. Sort the files in cadences by file name (same as ordering by timestamp)
4. Remove files that contain `000000_TIC` in the name from the cadences

No checks on the alternating ON/OFF have been found to be necessary.

## GC targets

These are a bit more complicated because instead of ON and OFF scans they alternate between two adjacent pointings, so every cadence can be analyzed two times, considering ON the odd or the even scans. Fortunately the name of the files contain `[timestamp]_[pointingID]` and the algorithm is:

1. Put all TIC files in timestamp-sorted list.
2. Extract the pointing ID of the first 6 consecutive files from the list.
3. Check the longest sequence of alternating IDs starting from the first:
    * if it's less than 3 files remove the first file from the file list.
    * if it's more than 3 add all the alternating file list to a cadence, then remove them from the file list
4. Go back to step 2 until the file list is empty. 

## TurboSeti event finder

Once cadences are built, they are analyzed to search for events. A BLISS command has not been developed yet so the search is done with the `find_event_pipeline()` python command from the `turbo_seti` library in section 4 of `BLISS_pipeline.py`.

Before doing this, for each cadence a `cadence_data_[number].lst` and `cadence_hits_[number].lst` file are created, containing the names of the H5 files and DAT files of the cadence.

A *filter* needs to be applied, i.e. different strengths of RFI rejection algorithms:
* **Filter 1:** a hit is present in at least one of the scans, no ON-OFF checks are done.
* **Filter 2:** a hit is present in *some* of the ON scans and *none* of the OFF scans.
*  **Filter 3:** a hit is present in *all* the ON scans and *none* of the OFF scans

If events that pass the chosen filter are found, they are saved in a CSV file called `found_event_table_[number].csv`

The full sintax of the `find_event_pipeline()` arguments used is:

```python
find_event_pipeline(
    data_list_path='.../cadence_data.lst',
    data_list_path='.../cadence_hits.lst',
    filter_threshold=3,
    cadence_length=len(cadence),
    csv_path='.../found_event_table.csv',
    saving=True)
```
After this, the found events are plotted with `plot_event_pipeline()` python command, still from the `turbo_seti` library, with full sintax:

```python
plot_event_pipeline(
    csv_path='.../found_event_table.csv',
    data_list_path='.../cadence_hits.lst',
    filter_spec=3,
    user_validation=False)
```
Then they are moved in the final lines of the pipeline from their initial path (the h5 data folder, I haven't figured out how to save them elsewhere directly) to a dedicated one, where they can be analzed "by eye".

>NOTE: for the GC targets the event search is done two times per cadence, one for the ON-first and OFF-first (supplying the additional argument `on_off_first='OFF'` to `find_event_pipeline`). Two .csv files are saved, denoted with 'A' (ON-first) and 'B' (OFF-first).


# BLISS performance and findings



## GPU memory limitations
BLISS is very memory-intensive and as mentioned it can exceed the GPU memory of the SRT computers (about 10.9 GB) this influences the maximum drift rate range that is possible to search in one go, depending on the number of fine channels analyzed.

A test has been done to see where the limits are, ananlyzing one of the SRT high spectral resolution files with various drift rate ranges $\dot{\nu}_\text{max}$ and number of fine channels $N_{fc}$, giving the following results:

<img src=./guide_images/memory_test.png width=400>

From this plot the following empyrical law can be infered:

$\dot{\nu}_\text{ range} \lesssim 9.2 \cdot 10^5 \ N_{fc}^{-1} \text{ Hz/s}$

This result shouldn't really be interpreted in absolute values: when analyzing all data with $\dot{\nu}_\text{ range}<3.5 \text{ Hz/s}$ and $2^{20}$ fine channels BLISS would still run out of memory for some files. I haven't had the time to investigate this issue, and it's possible that this was due to other processes happening on the computer that used the GPU and occasionally it coincided with the peak BLISS memory usage. In any case, to avoid skipping files for whihch BLISS would run out of memory the data was analyzed with a ±2 Hz/s range, which with my limited trials (each one would take several hours) seems to be close to the upper limit of no file skipping.

## BLISS hits vs TurboSeti hits

For all h5 files the hit search has also been repeated with `FindDoppler` from the `turbo-seti` Python packages, and all hits have been compared. Here are some plots that compare the two sets of hits:

### Galactic center histograms:
<img src=./guide_images/SNR_hist_GC.png width=400>
<img src=./guide_images/DR_hist_GC.png width=400>
<img src=./guide_images/f0_hist_GC.png width=400>

### TESS input catalog histograms

<img src=./guide_images/SNR_hist_TIC.png width=400>
<img src=./guide_images/DR_hist_TIC.png width=400>
<img src=./guide_images/f0_hist_TIC.png width=400>

### Drift rate - SNR scatter plots

<img src=./guide_images/SNR_DR_GC.png width=400>
<img src=./guide_images/SNR_DR_TIC.png width=400>

The following things can be observed from these plots:

* **BLISS finds many more hits than TurboSeti**, and generally at higher SNR. This may seem a good thing but there are some caveats.
* **Many of the BLISS hits are artifacts**