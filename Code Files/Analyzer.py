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

def getAnalyzerTransmition(dirname):
    # Analyzer - Clean.###################### Main Idea.
    # This function will get the dir name
    # 1) Read 'clean' & 'analyzer' to df
    # 2) Create clean/empty transmition df
    # 3) Iterate over analyzer dataframe
    #     if: 'analyzer' row same as 'clean' row appand to transmition (hilok mainpulation)
    #     else: update 'clean' row and continue.
    # 4) Save as transmission_analyzer.csv
    # This function result is I/I0.
    None

def beerLambert(dirname, databaseFilePath, wavelength,l):
    # This function calculate c (Concentration).
    # A = Absorbance, E = Molar attenuation coefficient, l = Lenght of waveguide, c = Molar concentration.
    # The df is 

    df = getAnalyzerTransmition(dirname) # = -E

    # To make E minus every result, every rublica. 
    None

def allandevation():
    # Calculate divation according to time and this plot to graph.
    # The second graph - LOD
    None

def finalCSVFile():
    # This function create a new csv file that contain additional one column of the concentrations and one column of the chosen waveguide. 
    None

def getConcentration(databaseFilePath,l,wavelength):
    None


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

if __name__=='__main__':
    now = time.time()
    dirname = "C:\BGUProject\Automation-of-spectral-measurements\Results\AllanVariance"
    #getNormlizedByCustomFreq("..\\Results\\2023_03_23_15_29_25_116512_Eyal & Alex\\", '1475')
    getNormlizedAllanVariance(dirname)
    print("normalize and divide time: {:.2f}".format(time.time()-now))

