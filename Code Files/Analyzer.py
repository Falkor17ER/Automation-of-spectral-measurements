import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import allantools

# Helper function
def normalize(x, y):
    x_new = x/y
    return x_new

def getNormlizedByRealFreq(dirname, to_norm, real_freq = '1500'):
    try:
        # Load clean and substance csvs
        clean_df = pd.read_csv(dirname+'\\'+'clean.csv')
        substance_df = pd.read_csv(dirname+'\\'+'substance.csv')
    except:
        return False

    columns = substance_df.columns.to_list()
    freqs = [element for element in columns[10:]]
    R, _ = substance_df.shape

    if to_norm:
        # Getting the elemnts of normalizations:
        norm_vals_clean = clean_df[real_freq]
        norm_vals_substance = substance_df[real_freq]

        # Normalizing both clean and substance CSVs
        for idx in range(0,R):
            # Iterating over each row and normlizing
            clean_df.iloc[idx,10:] = clean_df.iloc[idx,10:].apply(lambda val : val - norm_vals_clean[idx])
            substance_df.iloc[idx,10:] = substance_df.iloc[idx,10:].apply(lambda val : val - norm_vals_substance[idx])

    divided_df = substance_df.copy()
    divided_df[freqs] = divided_df[freqs].subtract(clean_df[freqs])
    
    return divided_df, clean_df, substance_df

def getNormlizedByCustomFreq(dirname, Freq = '1500', to_norm = False):
    # looking for a frequency closest to the users choice
    clean_df = pd.read_csv(dirname+'\\'+'clean.csv', nrows=1)
    columns = clean_df.columns.to_list()
    freqs = [float(element) for element in columns[10:]]
    distance_from_user = [abs(float(Freq)-element) for element in freqs]
    real_freq = freqs[np.argmin(distance_from_user)]
    if real_freq.is_integer():
        # convert x to integer
        real_freq = int(real_freq)
    real_freq = str(real_freq)
    df_ratio, df_clean, df_substance = getNormlizedByRealFreq(dirname=dirname, real_freq=real_freq, to_norm=to_norm)
    df_ratio.to_csv(dirname+'\\transition.csv', index=False, encoding='utf-8')
    return df_ratio, df_clean, df_substance

def getAnalyzerTransmition(dirname, to_norm=False, waveLength = '1550'):
    try:
        df_clean = pd.read_csv(dirname+'\\'+'clean.csv')
        df_analyzer = pd.read_csv(dirname+'\\analyzer.csv')
    except:
        return False
    
    ###### Here is the normalize
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
            # https://sparkbyexamples.com/pandas/pandas-add-row-to-dataframe/
        df_clean_multipled = pd.concat([df_clean_multipled.loc[:],clean_row]).reset_index(drop=True)
    df_clean_multipled = df_clean_multipled.reset_index(drop=True)
    df_transmittance[freqs] = df_transmittance[freqs].subtract(df_clean_multipled[freqs])
    df_transmittance.to_csv(dirname+'\\transmittance.csv', index=False, encoding='utf-8')
    return df_transmittance

def beerLambert(dirname, databaseFilePath, wavelength,l,G):
    # This function calculate C (Concentration).
    # k = The wavenumber, A = Absorbance, E = Molar attenuation coefficient, l = Lenght of waveguide, c = Molar concentration.
    # E is minus every result, every rublica. 
    
    # Loading the dataframe of transmittance.csv:
    try:
        df_transmittance = pd.read_csv(dirname+'\\transmittance.csv')
    except:
        return False

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
    A = abs((AbsorptionList[index])*(1e10))
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
    columnsList.append('Concentration [mol/L]=[M]')
    columnsList.append('Wavelength')
    df_C = pd.DataFrame(columns=columnsList)
    # 
    for row in range(df_transmittance.shape[0]):
        new_row = []
        for idx in range(10):
            new_row.append(df_transmittance.iloc[row][idx])
        E = - df_transmittance.iloc[row][real_wavelength]
        if E == 0:
            C = 0
        else:
            # Site 1: https://chem.libretexts.org/Bookshelves/Inorganic_Chemistry/Inorganic_Chemistry_(LibreTexts)/11%3A_Coordination_Chemistry_III_-_Electronic_Spectra/11.01%3A_Absorption_of_Light/11.1.01%3A_Beer-Lambert_Absorption_Law
            # Site 2: https://www.nexsens.com/knowledge-base/technical-notes/faq/how-do-you-convert-from-molarity-m-to-parts-per-million-ppm-and-mgl.htm
            C = ((E/l)/A)/float(G) # [ppm]
        #new_row.append(C)
        new_row.append(C)
        # From database gama is 1, but here from the measurment of the waveguide the value is the manipulation of the value and Gama.
        C = C/35000 # Converting from [ppm] to [M]=[L/mol]
        new_row.append(C)
        new_row.append(real_wavelength)
        df_C.loc[len(df_C)] = new_row

    # Saving the df_C to Concetration.csv
    real_wavelength = str("{:.3f}".format(float(real_wavelength)))
    df_C.to_csv(dirname+'\\Concentration (Wavelength-'+real_wavelength.replace('.','_')+'nm).csv', index=False, encoding='utf-8')
    return df_C, real_wavelength

def getMeanInterval(timeStamps):
    sum = 0;
    for idx in range(len(timeStamps)-1):
        sum = timeStamps[idx+1]-timeStamps[idx]
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
    tau, adev, _, _ = allantools.oadev(freq_data, rate, taus='decade')
    return tau, adev, _, _

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


### --- To Delete --- ### :
    #df_clean_multipled = df_clean_multipled.append(clean_row, ignore_index=True)
    #df_clean_multipled[idx] = clean_row
#E = - df_transmittance.iloc[row][real_wavelength]
        # real_wavelength = str(1524.9500000001818)
        #C = abs(C)
        #C_mol = (A/l)/E # [M] = [mol/L] = Units of mols.
        # A = A*(1e10) # A is Unitless.