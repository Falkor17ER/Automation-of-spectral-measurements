import numpy as np
import pandas as pd
import time
import allantools
from scipy.signal import butter, cheby1, filtfilt

# Helper function
def normalize(x, y):
    x_new = x/y
    return x_new

def substractWatt(x_dBm, y_dBm):
    # y is the dark.
    x_watt = 10**((x_dBm-30)/10)
    y_watt = 10**((y_dBm-30)/10)
    res = x_watt - y_watt
    x_dBm = 10*(np.log10(res/0.001))
    return x_dBm

def minusDark(dirname,df_clean, df_substance, df_dark, mode):
    
    #
    # clean minus dark:
    R, C = df_clean.shape
    for idi in range(0,R):
        for idj in range(10,C):
            # Iterating over each row and normlizing
            df_clean.iloc[idi,idj] = substractWatt(df_clean.iloc[idi,idj], df_dark.iloc[0,idj])
    # substance minus dark:
    R, C = df_substance.shape
    for idi in range(0,R):
        for idj in range(10,C):
            # Iterating over each row and normlizing
            df_substance.iloc[idi,idj] = substractWatt(df_substance.iloc[idi,idj], df_dark.iloc[0,idj])
    # Save the dataframes:
    df_clean.to_csv(dirname+'\\clean_minusDark.csv', index=False, encoding='utf-8')
    if (mode == "allan"):
        df_substance.to_csv(dirname+'\\analyzer_minusDark.csv', index=False, encoding='utf-8')
    else:
        df_substance.to_csv(dirname+'\\substance_minusDark.csv', index=False, encoding='utf-8')
    # Return:
    return df_clean, df_substance, True

def get_clean_substance_transmittance(val_list):
    dirname = val_list[0]
    darkMinus = val_list[1]
    filter_values = val_list[2]
    to_norm = val_list[3]
    real_freq = val_list[4]
    to_filter = val_list[5]
    
    try:
        # Load clean and substance csvs
        clean_df = pd.read_csv(dirname+'\\'+'clean.csv')
        substance_df = pd.read_csv(dirname+'\\'+'substance.csv')
    except:
        return False
    
    try:
        df_dark = pd.read_csv(dirname+'\\'+'dark.csv')
    except:
        df_dark = pd.DataFrame()

    # filter if requested 
    if to_filter:
        df_dark = filter_df(df_dark, filter_values)
        clean_df = filter_df(clean_df, filter_values)
        substance_df = filter_df(substance_df, filter_values)
    #
    
    columns = substance_df.columns.to_list()
    clean_df.columns = columns
    if darkMinus and (not df_dark.empty):
        df_dark.columns = columns
    freqs = [element for element in columns[10:]]
    R_substance, _ = substance_df.shape
    R_clean, _ = clean_df.shape
    R_dark, _ = df_dark.shape

    if to_norm:
        
        # Getting the elemnts of normalizations:
        real_freq = get_closeset_wavelength(clean_df.columns[10:], real_freq)
        norm_vals_clean = clean_df[real_freq]
        real_freq = get_closeset_wavelength(substance_df.columns[10:], real_freq)
        norm_vals_substance = substance_df[real_freq]
        real_freq = get_closeset_wavelength(df_dark.columns[10:], real_freq)
        norm_vals_dark = df_dark[real_freq]

        # Normalizing both clean and substance CSVs
        for idx in range(0,R_substance):
            # Iterating over each row and normlizing
            substance_df.iloc[idx,10:] = substance_df.iloc[idx,10:].apply(lambda val : val - norm_vals_substance[idx])
        for idx in range(0,R_clean):
            # Iterating over each row and normlizing
            clean_df.iloc[idx,10:] = clean_df.iloc[idx,10:].apply(lambda val : val - norm_vals_clean[idx])
        if darkMinus and (not df_dark.empty):
            for idx in range(0,R_dark):
                # Iterating over each row and normlizing
                df_dark.iloc[idx,10:] = df_dark.iloc[idx,10:].apply(lambda val : val - norm_vals_dark[idx])

    if darkMinus and (not df_dark.empty):
        clean_df, substance_df, darkStatus = minusDark(dirname,clean_df, substance_df, df_dark, "sweepGraph")
    else:
        darkStatus = False

    
    df_transmittance = substance_df.copy()
    if R_clean < R_substance:
        df_columns = df_transmittance.columns.to_list()
        freqs = df_columns[10:]
        r = None
        p = None
        df_clean_multipled = pd.DataFrame(columns=df_columns)
        clean_df.columns = df_columns
        for idx, row in substance_df.iterrows():
            if ( row['REP_RATE'] != r or row['POWER'] != p ):
                r = row['REP_RATE']
                p = row['POWER']
                clean_row = clean_df.loc[(clean_df['REP_RATE'] == r) & (clean_df['POWER'] == p)]
                # https://sparkbyexamples.com/pandas/pandas-add-row-to-dataframe/
            df_clean_multipled = pd.concat([df_clean_multipled.loc[:],clean_row]).reset_index(drop=True)
        df_clean_multipled = df_clean_multipled.reset_index(drop=True)
        df_transmittance[freqs] = df_transmittance[freqs].subtract(df_clean_multipled[freqs])
    else:
        df_transmittance[freqs] = df_transmittance[freqs].subtract(clean_df[freqs])
    
    df_transmittance.to_csv(dirname+'\\transmittance.csv', index=False, encoding='utf-8')
    return df_transmittance, clean_df, substance_df, darkStatus

def get_closeset_wavelength(freqs, Freq):
    freqs = np.asarray(freqs, float)
    distance_from_user = [abs(float(Freq)-element) for element in freqs]
    real_freq = freqs[np.argmin(distance_from_user)]
    if real_freq.is_integer():
        # convert x to integer
        real_freq = int(real_freq)
        return str(real_freq)+'.0'
    return str(real_freq)

def getAnalyzerTransmition(val_list):
    dirname = val_list[0]
    to_norm = val_list[1]
    waveLength = val_list[2]
    darkMinus = val_list[3]
    to_filter = False
    #
    try:
        # Load clean and substance csvs
        df_clean = pd.read_csv(dirname+'\\'+'clean.csv')
        df_analyzer = pd.read_csv(dirname+'\\'+'analyzer.csv')
    except:
        return False
    try:
        df_dark = pd.read_csv(dirname+'\\'+'dark.csv')
    except:
        df_dark = pd.DataFrame()

    # filter if requested 
    if to_filter:
        df_dark = filter_df(df_dark, {})
        clean_df = filter_df(clean_df, {})
        substance_df = filter_df(substance_df, {})
    #
    if darkMinus and not df_dark.empty:
        clean_df, substance_df, darkStatus = minusDark(dirname,clean_df, substance_df, df_dark, "sweepGraph")
    else:
        darkStatus = False
    columns = df_clean.columns.to_list()
    
    if to_norm:
        wavelengths = [float(element) for element in columns[10:]]
        distance_from_user = [abs(float(waveLength)-element) for element in wavelengths]
        real_wavelength_from_user = wavelengths[np.argmin(distance_from_user)]
        #if real_wavelength_from_user.is_integer():
            # convert x to integer
            #real_wavelength_from_user = int(real_wavelength_from_user)
        real_wavelength_from_user = str(real_wavelength_from_user)
        # Getting the elemnts of normalizations:
        norm_vals_clean = df_clean[real_wavelength_from_user]
        norm_vals_analyzer = df_analyzer[real_wavelength_from_user]

        # Normalizing both clean and substance CSVs
        R, _ = df_analyzer.shape
        for idx in range(0,R):
            # Iterating over each row and normlizing
            df_analyzer.iloc[idx,10:] = df_analyzer.iloc[idx,10:].apply(lambda val : val - norm_vals_analyzer[idx])
        R, _ = df_clean.shape
        for idx in range(0,R):
            # Iterating over each row and normlizing
            df_clean.iloc[idx,10:] = df_clean.iloc[idx,10:].apply(lambda val : val - norm_vals_clean[idx])
    
    ## [dB], [dBm] --> [dB]

    df_columns = columns
    freqs = [element for element in df_columns[10:]]
    r = None
    p = None
    df_transmittance = df_analyzer
    df_clean_multipled = pd.DataFrame(columns=df_columns)
    for idx, row in df_analyzer.iterrows():
        if ( row['REP_RATE'] != r or row['POWER'] != p ):
            r = row['REP_RATE']
            p = row['POWER']
            clean_row = df_clean.loc[(df_clean['REP_RATE'] == r) & (df_clean['POWER'] == p)]
        df_clean_multipled = pd.concat([df_clean_multipled.loc[:],clean_row]).reset_index(drop=True)
    df_clean_multipled = df_clean_multipled.reset_index(drop=True)
    df_transmittance.columns = columns
    df_transmittance[freqs] = df_transmittance[freqs].subtract(df_clean_multipled[freqs])
    df_transmittance.to_csv(dirname+'\\transmittance.csv', index=False, encoding='utf-8')
    return df_transmittance, darkStatus

def beerLambert(val_list):
    dirname = val_list[0]
    databaseFilePath = val_list[1]
    wavelength = val_list[2]
    l = val_list[3]
    G = val_list[4]
    df_transmittance = val_list[5]
    G = float(G)
    #
    # This function calculate C (Concentration).
    # k = The wavenumber, A = Absorbance, E = Molar attenuation coefficient, l = Lenght of waveguide, c = Molar concentration.
    # E is minus every result, every rublica. 

    # Getting the wavenumber from waveguide:
    k = 10000000/wavelength # In unit of cm^(-1)
    
    # Finding the relevant Absorption from the txt file:
    df_A = pd.read_csv(databaseFilePath, delimiter = "\t", names=['Wavenumber', 'Absorption']) # databaseFilePath=dirname+filename.txt
    wavenumberList = df_A['Wavenumber'].tolist()
    AbsorptionList = df_A['Absorption'].tolist()
    index = -1
    for element in wavenumberList:
        if (element < k):
            index = wavenumberList.index(element)
            if ( abs(k-wavenumberList[index]) > abs(k-wavenumberList[index-1]) ):
                index = index - 1
            break
    epsilon = abs((AbsorptionList[index]))
    l = l/1000 # Convert from mm to meter (For correct units to calculate).
    # Finding the index of the relvant/closest wavelength:
    columns = df_transmittance.columns.to_list()
    wavelengthList = [float(element) for element in columns[10:]]
    distance_from_wavelength = [abs(float(wavelength)-element) for element in wavelengthList]
    real_wavelength = wavelengthList[np.argmin(distance_from_wavelength)]
    #if real_wavelength.is_integer():
        # convert x to integer
    #    real_wavelength = int(real_wavelength)
    real_wavelength = str(real_wavelength)
    
    # Creating a new df_C & Calculating the concetration:
    columnsList = df_transmittance.columns.to_list()[:10]
    columnsList.append('Concentration [ppm]')
    columnsList.append('Concentration [%]')
    columnsList.append('Concentration [mol/L]=[M]')
    columnsList.append('Wavelength')
    df_C = pd.DataFrame(columns=columnsList)
    # 
    for row in range(df_transmittance.shape[0]):
        new_row = []
        for idx in range(10):
            new_row.append(df_transmittance.iloc[row][idx])
        A = - df_transmittance.iloc[row][real_wavelength]
        A = A/10 # from 10*log(I0/I) [dB] to log(I0/I) (for beer lambert)
        if A == 0:
            C = 0
        else:
            # Site 1: https://chem.libretexts.org/Bookshelves/Inorganic_Chemistry/Inorganic_Chemistry_(LibreTexts)/11%3A_Coordination_Chemistry_III_-_Electronic_Spectra/11.01%3A_Absorption_of_Light/11.1.01%3A_Beer-Lambert_Absorption_Law
            # Site 2: https://www.nexsens.com/knowledge-base/technical-notes/faq/how-do-you-convert-from-molarity-m-to-parts-per-million-ppm-and-mgl.htm
            # C = ((A/l)/epsilon)/G # [ppm]
            C = A/(l*epsilon*G) # [ppm]
        new_row.append(C)
        new_row.append(C/10000) #   '1%' = 10,000ppm 
        # From database gama is 1, but here from the measurment of the waveguide the value is the manipulation of the value and Gama.
        C = C/35500 # Converting from [ppm] to [M]=[L/mol]
        new_row.append(C)
        new_row.append(real_wavelength)
        df_C.loc[len(df_C)] = new_row

    # Saving the df_C to Concetration.csv
    real_wavelength = str("{:.3f}".format(float(real_wavelength)))
    df_C.to_csv(dirname + '\\Concentration (Wavelength-'+real_wavelength.replace('.','_')+'nm).csv', index=False, encoding='utf-8')
    return df_C, real_wavelength

def getMeanInterval(timeStamps):
    sum = 0;
    for idx in range(len(timeStamps)-1):
        sum = sum + timeStamps[idx+1]-timeStamps[idx]
    rate = sum/(len(timeStamps)-1)
    return rate

def allandevation(df_C):
    # Calculate divation according to time and this plot to graph - The second graph - LOD
    # Compute the fractional frequency data
    # df_C = pd.read_csv(dirname+'\Concetration (Wavelength-'+wavelength+'nm)')
    # ppm_data = df_C['Concentration [ppm]'].tolist()
    ppm_data = df_C['Concentration [ppm]']
    freq_data = ppm_data # / 1e6 + 1

    rate = getMeanInterval(df_C['Interval'].tolist())
    
    # Compute the Allan deviation
    tau, adev, _, _ = allantools.oadev(freq_data, 1/rate, taus='decade')
    return tau, adev, rate

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def getConcentration(dirname,databaseFile,wavelength,l):
    to_norm = False
    startTime = time.time()
    getAnalyzerTransmition(dirname, to_norm)
    df_C = beerLambert(dirname,databaseFile,wavelength,l,G='1')
    # allandevation(dirname, wavelength)
    totalTime = time.time() - startTime
    print("The total time it take was: ", totalTime)
    return df_C

def filter_df(df, values):
    filter_type = values['_FILTER_TYPE_']
    if filter_type == 'BW':
        filtered_df = butterworth_filter(df.copy(), float(values['_cutoff_BW']), int(values['_order_BW']))
    elif filter_type == 'cheby1':
        filtered_df = cheby1_filter(df.copy(), float(values['_cutoff_cheby1']), int(values['_order_cheby1']), float(values['_ripple_cheby1']))
    return filtered_df

def butterworth_filter(df, cutoff_freq, order):
    # Design the Butterworth low-pass filter
    b, a = butter(order, cutoff_freq, btype='low', analog=False, output='ba')
    for idx, row in df.iterrows():
        sample = np.asarray(row.iloc[10:], dtype=float)
        mean_of_sample = np.mean(sample)
        # Apply the filter to the sample signal
        filtered_signal = filtfilt(b, a, sample-mean_of_sample)
        df.iloc[idx,10:] = filtered_signal + mean_of_sample
    return df

def cheby1_filter(df, cutoff_freq, order, ripple):
    # Design the chebyshev 1 low-pass filter
    b, a = cheby1(order, ripple, cutoff_freq, btype='low', analog=False, output='ba')
    for idx, row in df.iterrows():
        sample = np.asarray(row.iloc[10:], dtype=float)
        mean_of_sample = np.mean(sample)
        # Apply the filter to the sample signal
        filtered_signal = filtfilt(b, a, sample-mean_of_sample)
        df.iloc[idx,10:] = filtered_signal + mean_of_sample
    return df


if __name__=='__main__':
    now = time.time()
    dirname = "C:\BGUProject\Automation-of-spectral-measurements\Results\Simulation"
    #dirname = "C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\Analyzer_Test\\"
    databaseFile = "C:\BGUProject\Automation-of-spectral-measurements\Databases\CH4_25T.TXT"
    wavelength = 1475.125
    l = 5
    #getAnalyzerTransmition(dirname,to_norm=False)
    getConcentration(dirname, databaseFile, wavelength, l)
    print("Everything worked fine!")
