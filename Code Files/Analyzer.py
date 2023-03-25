import numpy as np
import pandas as pd
import time

# Helper function
def normalize(x, y):
    x_new = x/y
    return x_new

def getNormlizedByRealFreq(dirname, real_freq = '1500'):
    try:
        # Load clean and substance csvs
        clean_df = pd.read_csv(dirname+'\\'+'clean.csv')
        substance_df = pd.read_csv(dirname+'\\'+'substance.csv')
    except:
        return False

    # Getting the elemnts of normalizations:
    norm_vals = clean_df[real_freq]

    columns = substance_df.columns.to_list()
    freqs = [element for element in columns[10:]]
    R, _ = substance_df.shape
    
    # Normalizing both clean and substance CSVs
    for idx in range(0,R):
        # Iterating over each row and normlizing
        clean_df.iloc[idx,10:] = clean_df.iloc[idx,10:].apply(lambda val : val/norm_vals[idx])
        substance_df.iloc[idx,10:] = substance_df.iloc[idx,10:].apply(lambda val : val/norm_vals[idx])

    divided_df = substance_df.copy()
    divided_df[freqs] = divided_df[freqs].div(clean_df[freqs])

    return divided_df


    
def getNormlizedByCustomFreq(dirname, Freq = '1500'):
    # looking for a frequency closest to the users choice
    clean_df = pd.read_csv(dirname+'\\'+'clean.csv', nrows=1)
    columns = clean_df.columns.to_list()
    freqs = [float(element) for element in columns[10:]]
    distance_from_user = [abs(float(Freq)-element) for element in freqs]
    real_freq = str(freqs[np.argmin(distance_from_user)])
    return getNormlizedByRealFreq(dirname=dirname, real_freq=real_freq)
    


if __name__=='__main__':
    now = time.time()
    getNormlizedByCustomFreq("..\\Results\\2023_03_23_15_29_25_116512_Eyal & Alex", '1475')
    print("normalize and divide time: {:.2f}".format(time.time()-now))