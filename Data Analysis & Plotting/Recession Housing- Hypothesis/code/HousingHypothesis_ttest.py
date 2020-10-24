# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 16:37:14 2020

@author: Manoj
"""
'''
Definitions:

A quarter is a specific three month period, Q1 is January through March, Q2 is April through June, Q3 is July through September, Q4 is October through December.
A recession is defined as starting with two consecutive quarters of GDP decline, and ending with two consecutive quarters of GDP growth.
A recession bottom is the quarter within a recession which had the lowest GDP.
A university town is a city which has a high percentage of university students compared to the total population of the city.
Hypothesis: University towns have their mean housing prices less effected by recessions. We will run a t-test to compare the ratio of the mean price of houses in
university towns the quarter before the recession starts compared to the recession bottom. (price_ratio=quarter_before_recession/recession_bottom)

The following data files are available for data wrangling.These files are from a specific point in time, websites get regular updates. Ideal to use the files availabe in my 
repository.

From the Zillow research data site there is housing data for the United States. In particular the datafile for all homes at a city level, City_Zhvi_AllHomes.csv, 
has median home sale prices at a fine grained level.
From the Wikipedia page on college towns is a list of university towns in the United States which has been copy and pasted into the file university_towns.txt.
From Bureau of Economic Analysis, US Department of Commerce, the GDP over time of the United States in current dollars (we will use the chained value in 2009 dollars), 
in quarterly intervals, in the file gdplev.xls. For this hypothesis, we will only look at GDP data from the first quarter of 2000 onwards.'''

import pandas as pd
import numpy as np
import re
from scipy.stats import ttest_ind

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 300)

# This dictionary to map state names to two letter acronyms
states = {'OH': 'Ohio', 'KY': 'Kentucky', 'AS': 'American Samoa', 'NV': 'Nevada', 'WY': 'Wyoming', 'NA': 'National', 
          'AL': 'Alabama', 'MD': 'Maryland', 'AK': 'Alaska', 'UT': 'Utah', 'OR': 'Oregon', 'MT': 'Montana', 'IL': 'Illinois',
          'TN': 'Tennessee', 'DC': 'District of Columbia', 'VT': 'Vermont', 'ID': 'Idaho', 'AR': 'Arkansas', 'ME': 'Maine', 
          'WA': 'Washington', 'HI': 'Hawaii', 'WI': 'Wisconsin', 'MI': 'Michigan', 'IN': 'Indiana', 'NJ': 'New Jersey', 
          'AZ': 'Arizona', 'GU': 'Guam', 'MS': 'Mississippi', 'PR': 'Puerto Rico', 'NC': 'North Carolina', 'TX': 'Texas', 
          'SD': 'South Dakota', 'MP': 'Northern Mariana Islands', 'IA': 'Iowa', 'MO': 'Missouri', 'CT': 'Connecticut', 
          'WV': 'West Virginia', 'SC': 'South Carolina', 'LA': 'Louisiana', 'KS': 'Kansas', 'NY': 'New York', 
          'NE': 'Nebraska', 'OK': 'Oklahoma', 'FL': 'Florida', 'CA': 'California', 'CO': 'Colorado', 'PA': 'Pennsylvania', 
          'DE': 'Delaware', 'NM': 'New Mexico', 'RI': 'Rhode Island', 'MN': 'Minnesota', 'VI': 'Virgin Islands', 
          'NH': 'New Hampshire', 'MA': 'Massachusetts', 'GA': 'Georgia', 'ND': 'North Dakota', 'VA': 'Virginia'}

def loadZillowData():
    '''Converts the housing data to quarters and returns it as mean 
    values in a dataframe. This dataframe will be a dataframe with
    columns for 2000q1 through 2016q3, and will have a multi-index
    in the shape of ["State","RegionName"].
    '''
    zillow_df = pd.read_csv('City_Zhvi_AllHomes.csv')
    zillow_df['State'].replace(states,inplace=True)
    zillow_df.set_index(["State","RegionName"],inplace=True)
    zillow_df = zillow_df.iloc[:,49:]
    def grouping(colName):
        if colName[-2:] in ['01','02','03']:
            q_of_year = colName[:4]+'q1'
        elif colName[-2:] in ['04','05','06']:
            q_of_year = colName[:4]+'q2'
        elif colName[-2:] in ['07','08','09']:
            q_of_year = colName[:4]+'q3'
        else:
            q_of_year = colName[:4]+'q4'   
        return q_of_year   
    zillow_df_grp=zillow_df.groupby(grouping,axis=1)   
    zillow_df_final=zillow_df_grp.mean().sort_index().copy()
    
    return zillow_df_final


def loadUniversityRegions():
    '''Returns a DataFrame of towns and the states they are in from the 
    university_towns.txt list.'''
    
    university_df_original = pd.read_csv('university_towns.txt', sep = "\t", names=(['Compound']), index_col=False)
    
    def cleanUniversity(row): #Cleaning
        row['Compound'] =  re.sub('\s\(.*\)\[.*\]', '', row['Compound'])
        row['Compound'] =  re.sub('\s\(.*\)*', '', row['Compound'])
        row['Compound'] =  re.sub('.*:', '', row['Compound'])
        return pd.Series(row)  
    university_df_original=university_df_original.apply(cleanUniversity,axis=1)
    state_df=university_df_original[university_df_original['Compound'].str.contains(pat='\[edit]')]
    university_df = pd.DataFrame(columns=('State', 'RegionName'))
    
    for i in range(len(state_df)):
        stateCurrIdx = state_df.index[i]
        if i != len(state_df)-1:
            stateNextIdx = state_df.index[i+1]
        else:
            stateNextIdx = len(university_df_original)
        
        for j in range(stateCurrIdx+1, stateNextIdx):
            university_df.loc[j] = [state_df.loc[stateCurrIdx]['Compound'],university_df_original.loc[j]['Compound']]
            
    university_df['State']=university_df.apply(lambda x: re.sub('\[.*\]', '', x['State']), axis=1)
    university_df=university_df[university_df['RegionName']!='']
    university_df.reset_index(drop=True,inplace=True)
    
    return university_df

def getRecessionDetails():
    gdp_df=pd.read_excel('gdplev.xls',header=1,skiprows=[1,2,3,4,6,7],usecols=['Unnamed: 4','GDP in billions of chained 2009 dollars.1'])
    gdp_df.columns=['Quarter','GDP 2009 Chained']
    gdp_df=gdp_df[gdp_df['Quarter']>='2000q1']
    gdp_df.reset_index(drop=True,inplace=True)
    
    i=0
    while(i<len(gdp_df)-2):
        if ((gdp_df.loc[i+1,'GDP 2009 Chained'] < gdp_df.loc[i,'GDP 2009 Chained']) and
        (gdp_df.loc[i+2,'GDP 2009 Chained'] < gdp_df.loc[i+1,'GDP 2009 Chained'])):
            j=i
            while(j+2 <= len(gdp_df)-1):
                if ((gdp_df.loc[j+1,'GDP 2009 Chained'] > gdp_df.loc[j,'GDP 2009 Chained']) and
                (gdp_df.loc[j+2,'GDP 2009 Chained'] > gdp_df.loc[j+1,'GDP 2009 Chained'])):
                    start = gdp_df.loc[i+1,'Quarter']
                    end = gdp_df.loc[j+2,'Quarter']
                    recession_df = gdp_df.iloc[i+1:j+2 +1]
                    bottom = gdp_df.loc[recession_df['GDP 2009 Chained'].idxmin(),'Quarter']
                    i=j+1
                    break      
                else:
                    j += 1
        i+= 1 
    return(start,bottom,end)
    
def ttest_hypothesis():
    '''First creates new data showing the decline or growth of housing prices
    between the recession start and the recession bottom. Then runs a ttest
    comparing the university town values to the non-university towns values, 
    return whether the alternative hypothesis (that the two groups are the same)
    is true or not as well as the p-value of the confidence. 
    
    different=True if the t-test is True at a p<0.01 (we reject the null hypothesis), 
    or different=False if otherwise (we cannot reject the null hypothesis). The
    value for better should be either "university town" or "non-university town"
    depending on which has a lower mean price ratio (which is equivilent to a
    reduced market loss).'''
    
    recession_start = getRecessionDetails()[0]
    recession_bottom = getRecessionDetails()[1]
    zillow_data = loadZillowData().copy()
    zillow_data.reset_index(inplace=True)
    
  
    zillow_data['price_ratio'] = zillow_data.iloc[:,zillow_data.columns.get_loc(recession_start)-1]/zillow_data[recession_bottom]
    zillow_data = zillow_data[['State','RegionName','price_ratio']].copy()
    
    university_towns_list=loadUniversityRegions()
    university_towns=pd.merge(zillow_data,university_towns_list,how='inner', on=['State','RegionName'])
    
    non_university_towns=pd.concat([zillow_data,university_towns_list],sort=True).copy()
    non_university_towns.drop_duplicates(['State','RegionName'], keep=False, inplace=True)
    non_university_towns.set_index(['State','RegionName'], inplace=True)
    non_university_towns.reset_index(inplace=True)  
    
    t, p = ttest_ind(university_towns['price_ratio'].dropna(), non_university_towns['price_ratio'].dropna())   
    
    critical_aplha=0.01
    if critical_aplha > p:
        difference =True #null_hypothesis = False 
    else:
        difference =False #null_hypothesis = True 

    if university_towns['price_ratio'].mean() < non_university_towns['price_ratio'].mean(): 
        better = "university town"
    else:
        better = "non-university town"
    return (difference, p, better)    

ttest_hypothesis()
(True, 0.0007376888577938637, 'university town')
