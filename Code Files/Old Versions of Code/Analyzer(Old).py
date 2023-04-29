import numpy as np
import pandas as pd
import time

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


def getAnalyzerTransmition(dirname, v=1):
    try:
        df_clean = pd.read_csv(dirname+'\\'+'clean.csv')
        df_analyzer = pd.read_csv(dirname+'\\analyzer.csv')
    except:
        return False
    
    if (v == 1):
        # Version 1:
        columns = df_clean.columns.to_list()
        freqs = [element for element in columns[10:]]
        REP_list = df_clean['REP_RATE'].unique().tolist()
        POWER_list = df_clean['POWER'].unique().tolist()
        r = ''
        p = ''
        for row in range(df_analyzer.shape[0]):
            if ( df_analyzer.iloc[row]['REP_RATE'] != r or df_analyzer.iloc[row]['POWER'] != p ):
                r = df_analyzer.iloc[row]['REP_RATE']
                p = df_analyzer.iloc[row]['POWER']
                clean_row = df_clean.loc[(df_clean['REP_RATE'] == r) & (df_clean['POWER'] == p)]
                # clean_row.to_csv(dirname+'\\clean_row.csv', index=False, encoding='utf-8')       
                
                clean_val = clean_row[0,10:] 
            for idx in range(clean_val.shape[1]):
                a = clean_val[idx]
                df_analyzer.iloc[row,10:] = df_analyzer.iloc[row,10:].apply(lambda val : val - clean_row[idx])
        
        df_analyzer.to_csv(dirname+'\\transmittance.csv', index=False, encoding='utf-8')
        return df_analyzer
                # for f in freqs:
                #     a = df_analyzer.iloc[row][f]
                #     b = clean_row.iloc[0][f]
                #     c = a - b
                #df_analyzer[row, df_analyzer.columns.get_loc(f)] = (df_analyzer.iloc[row][f] - clean_row.iloc[0][f])
                # df_analyzer[row][f] = df_analyzer.iloc[row][f] - clean_row.iloc[0][f]
                #print("df_analyzer[row][f]=",df_analyzer.iloc[row][f]," and c=",c)
            #df_analyzer.to_csv(dirname+'\\transmittance.csv', index=False, encoding='utf-8')

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

def beerLambert(df,dirname, databaseFilePath, wavelength,l):
    # This function calculate c (Concentration).
    # A = Absorbance, E = Molar attenuation coefficient, l = Lenght of waveguide, c = Molar concentration.
    # k = The wavenumber = 2*pi/wavelength.
    # To make E minus every result, every rublica. 
    k = wavelength

def allandevation():
    # Calculate divation according to time and this plot to graph.
    # The second graph - LOD
    None

def finalCSVFile():
    # This function create a new csv file that contain additional one column of the concentrations and one column of the chosen waveguide. 
    #allResults_df = pd.DataFrame(columns=['Date', 'Comment', 'CF',	'SPAN',	'REP_RATE',	'POWER', 'Sens','Res', 'Interval', 'SAMPLINGS_NUMBER']+freqs_columns)
    None

def getConcentration(dirname,databaseFile,wavelength,l):
    startTime = time.time()
    df = getAnalyzerTransmition(dirname)
    totalTime = time.time() - startTime
    print("The total time it take was: ", totalTime)
    #beerLambert(df,databaseFile,wavelength,l)
    #allandevation()
    #finalCSVFile()
    #return finalCSVFile(dirname)


if __name__=='__main__':
    now = time.time()
    dirname = "C:\BGUProject\Automation-of-spectral-measurements\Results\Analyzer_Test"
    databaseFile = "C:\BGUProject\Automation-of-spectral-measurements\Databases\CH4_25T.TXT"
    wavelength = 1500
    l = 1
    getConcentration(dirname, databaseFile, wavelength, l)
    print("Everything worked fine!")

# Delete -------------------------------------------------------------------------------------------------------------------


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
