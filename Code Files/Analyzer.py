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
    real_freq = str(freqs[np.argmin(distance_from_user)])
    df_ratio, df_clean, df_substance = getNormlizedByRealFreq(dirname=dirname, real_freq=real_freq, to_norm=to_norm)
    df_ratio.to_csv(dirname+'transition.csv', index=False, encoding='utf-8')
    return df_ratio, df_clean, df_substance

def getAnalyzerTransmition(dirname, v=1):
    try:
        df_clean = pd.read_csv(dirname+'\\'+'clean.csv')
        df_analyzer = pd.read_csv(dirname+'\\analyzer.csv')
    except:
        return False
    
    ###### Here is the normalize

    if (v == 1):
        # Version 1:
        df_columns = df_clean.columns.to_list()
        freqs = [element for element in df_columns[10:]]
        REP_list = df_clean['REP_RATE'].unique().tolist()
        POWER_list = df_clean['POWER'].unique().tolist()
        r = ''
        p = ''
        df_transmittance = pd.DataFrame(columns=df_columns)
        for row in range(df_analyzer.shape[0]):
            new_row = []
            for idx in range(10):
                new_row.append(df_analyzer.iloc[row][idx])
            if ( df_analyzer.iloc[row]['REP_RATE'] != r or df_analyzer.iloc[row]['POWER'] != p ):
                r = df_analyzer.iloc[row]['REP_RATE']
                p = df_analyzer.iloc[row]['POWER']
                clean_row = df_clean.loc[(df_clean['REP_RATE'] == r) & (df_clean['POWER'] == p)]
            for f in freqs:
                new_row.append( df_analyzer.iloc[row][f] - clean_row.iloc[0][f] )
            df_transmittance.loc[len(df_transmittance)] = new_row
        df_analyzer.to_csv(dirname+'\\transmittance.csv', index=False, encoding='utf-8')
        return df_analyzer

    if (v == 2):
        # Version 2:
        columns = df_clean.columns.to_list()
        freqs = [element for element in columns[10:]]
        REP_list = df_clean['REP_RATE'].unique().tolist()
        POWER_list = df_clean['POWER'].unique().tolist()
        df_transmittance = pd.DataFrame(columns)
        df_transmittance.to_csv(dirname+'\\transmittance.csv', index=False, encoding='utf-8')
        for r in REP_list:
            for p in POWER_list:
                clean_row = df_clean.loc[(df_clean['REP_RATE'] == r) & (df_clean['POWER'] == p)].iloc[0]
                analyzer_rows = df_analyzer.loc[(df_analyzer['REP_RATE'] == r) & (df_analyzer['POWER'] == p)]
                for row in range(analyzer_rows.shape[0]):
                    new_row = analyzer_rows.iloc[row]
                    for f in freqs:
                        new_row.loc[f] = new_row.loc[f] - clean_row.loc[f]
                    df_transmittance = df_transmittance.append(pd.Series(new_row, index = columns), ignore_index=True)
        df_transmittance.to_csv(dirname+'\\transmittance.csv', index=False, encoding='utf-8')
        return df_transmittance

def beerLambert(dirname, databaseFilePath, wavelength,l):
    # This function calculate C (Concentration).
    # k = The wavenumber, A = Absorbance, E = Molar attenuation coefficient, l = Lenght of waveguide, c = Molar concentration.
    # E is minus every result, every rublica. 
    
    # Loading the dataframe of transmittance.csv:
    try:
        df_transmittance = pd.read_csv(dirname+'\\'+'transmittance.csv')
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
    A = AbsorptionList[index]
    
    # Finding the index of the relvant/closest wavelength:
    columns = df_transmittance.columns.to_list()
    wavelengthList = [float(element) for element in columns[10:]]
    distance_from_wavelength = [abs(float(wavelength)-element) for element in wavelengthList]
    real_wavelength = str(wavelengthList[np.argmin(distance_from_wavelength)])

    # Creating a new df_C & Calculating the concetration:
    columnsList = df_transmittance.columns.to_list()[:10]
    columnsList.append('Concetration')
    columnsList.append('Concetration (ppm)')
    columnsList.append('Wavelength')
    df_C = pd.DataFrame(columns=columnsList)
    # 
    for row in range(df_transmittance.shape[0]):
        new_row = []
        for idx in range(10):
            new_row.append(df_transmittance.iloc[row][idx])
        E = - df_transmittance.iloc[row][real_wavelength]
        C = A/l/E
        new_row.append(C)
        new_row.append(C*(1e6))
        new_row.append(real_wavelength)
        df_C.loc[len(df_C)] = new_row

    # Saving the df_C to Concetration.csv
    df_C.to_csv(dirname+'\\Concetration (Wavelength-'+real_wavelength+'nm).csv', index=False, encoding='utf-8')
    return df_C

def allandevation(df_C, wavelength):
    # Calculate divation according to time and this plot to graph - The second graph - LOD
    
    # Compute the fractional frequency data
    # df_C = pd.read_csv(dirname+'\Concetration (Wavelength-'+wavelength+'nm)')
    
    ppm_data = df_C['Concetration (ppm)'].tolist()
    freq_data = ppm_data / 1e6 + 1

    # Compute the Allan deviation
    tau, adev, _, _ = allantools.oadev(freq_data, rate=1, taus='decade')

    # Plot the Allan deviation
    plt.loglog(tau, adev)
    plt.xlabel('Time (s)')
    plt.ylabel('Allan deviation')
    plt.show()

def normalizeAnalyzer():
    None

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def getConcentration(dirname,databaseFile,wavelength,l):
    startTime = time.time()
    # getAnalyzerTransmition(dirname)
    df_C = beerLambert(dirname,databaseFile,wavelength,l)
    # allandevation(dirname, wavelength)
    totalTime = time.time() - startTime
    print("The total time it take was: ", totalTime)
    return df_C


if __name__=='__main__':
    now = time.time()
    dirname = "C:\BGUProject\Automation-of-spectral-measurements\Results\Analyzer_Test"
    databaseFile = "C:\BGUProject\Automation-of-spectral-measurements\Databases\CH4_25T.TXT"
    wavelength = 1550
    l = 1
    getConcentration(dirname, databaseFile, wavelength, l)
    print("Everything worked fine!")

# Delete -------------------------------------------------------------------------------------------------------------------

######################################################  To Ignore  ########################################################
def getNormlizedAllanVariance(dirname):
    allan_df = pd.read_csv(dirname+'\\'+'allan.csv')
    allanNorm_df = allan_df.copy()
    columns = allan_df.columns.to_list()
    freqs = [element for element in columns[11:]]
    #
    normRow = allan_df.loc[0, columns[11:]].values.flatten().tolist()
    repName = allan_df.loc[0, columns[4]]
    powerName = allan_df.loc[0, columns[5]]
    for index, irow in allan_df.iterrows():
        if (index != 0):
            if ( (repName != allan_df.loc[index, columns[4]]) or (powerName != allan_df.loc[index, columns[5]]) ):
                normRow = allan_df.loc[index, columns[11:]].values.flatten().tolist()
                repName = allan_df.loc[index, columns[4]]
                powerName = allan_df.loc[index, columns[5]]
                # The row (index) stay as it is.
            else:
                thisRow = allan_df.loc[index, columns[11:]].values.flatten().tolist()
                normalizedRow = []
                for i in range(0, len(thisRow)):
                    # normalizedRow.append(thisRow[i]/normRow[i])
                    normalizedRow.append(round(thisRow[i]/normRow[i], 2))
                allanNorm_df.loc[index,freqs] = normalizedRow
    # The for loop is over. Save all the data.
    allanNorm_df.to_csv(dirname+'\\allan_norm.csv', index=False, encoding='utf-8')
    del allan_df
    del allanNorm_df
######################################################   To Ignore ########################################################

    # getNormlizedByCustomFreq("..\\Results\\2023_03_23_15_29_25_116512_Eyal & Alex\\", '1475')
    # getNormlizedAllanVariance(dirname)
    # print("normalize and divide time: {:.2f}".format(time.time()-now))


# def getAnalyzerTransmition(dirname):
    # Analyzer - Clean.###################### Main Idea.
    # This function will get the dir name
    # 1) Read 'clean' & 'analyzer' to df - OK
    # 2) Create clean/empty transmition df
    # 3) Iterate over analyzer dataframe
    #     if: 'analyzer' row same as 'clean' row appand to transmition (hilok mainpulation)
    #     else: update 'clean' row and continue.
    # 4) Save as transmission_analyzer.csv
    # This function result is I/I0.
    # clean_row.to_csv(dirname+'\\clean_row.csv', index=False, encoding='utf-8')
    # analyzer_rows.to_csv(dirname+'\\analyzer_rows.csv', index=False, encoding='utf-8')
    # analyzer_rowsNumber = analyzer_rows.shape[0] # The nuber of the rows of the dataframe.
    # a = analyzer_rows.loc[row,f]
    # b = clean_row.loc[0,f]
    # c = new_row.loc[f]

        # columns = df_A.columns.to_list()
    # if index != -1: # It will take the correspond value from the list.
    #     A = AbsorptionList[index]
    # else: # It will take the last possible value.
    #     A = AbsorptionList[-1]


                #clean_val = (clean_row.loc[0]).to_numpy()
            # print(df_analyzer.iloc[row,10:15])
            # for idx in range(10,len(clean_val)):
                # a = clean_val[idx]
                # df_analyzer.iloc[row,idx] = df_analyzer.iloc[row,idx].apply(lambda val : val - clean_val[idx])
                # df_analyzer[row][idx] = df_analyzer.iloc[row][idx] - clean_val[idx]
                # print(df_analyzer.iloc[row,10:15])     
                # for f in freqs:
                #     a = df_analyzer.iloc[row][f]
                #     b = clean_row.iloc[0][f]
                #     c = a - b
                #df_analyzer[row, df_analyzer.columns.get_loc(f)] = (df_analyzer.iloc[row][f] - clean_row.iloc[0][f])
                # df_analyzer[row][f] = df_analyzer.iloc[row][f] - clean_row.iloc[0][f]
                #print("df_analyzer[row][f]=",df_analyzer.iloc[row][f]," and c=",c)
            #df_analyzer.to_csv(dirname+'\\transmittance.csv', index=False, encoding='utf-8')

            # clean_row.to_csv(dirname+'\\clean_row.csv', index=False, encoding='utf-8')       
                # clean_val = (clean_row.iloc[0,10:]).to_numpy()
                #a = df_analyzer.iloc[row][f]
                #b = clean_row.iloc[0][f]
                #c = a - b
                #a = len(new_row)
            #df_analyzer[row][10:] = new_row
            
# def finalCSVFile():
#     # This function create a new csv file that contain additional one column of the concentrations and one column of the chosen waveguide. 
#     #allResults_df = pd.DataFrame(columns=['Date', 'Comment', 'CF',	'SPAN',	'REP_RATE',	'POWER', 'Sens','Res', 'Interval', 'SAMPLINGS_NUMBER']+freqs_columns)
#     None
