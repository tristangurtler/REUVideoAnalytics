
# coding: utf-8

# In[1]:

# Thank you to Denisolt, https://github.com/Denisolt
# Package imports
from PIL import Image
import sys
import pandas as pd
import os
import csv


# In[2]:

# Creates directory for frames to be stored, gets frames of videos, and stores timestamps in a csv file
try:
    os.system("mkdir images3")
    # Contrast with dark video has to be brightened via video editor and then contrast ranges from 12-22
    # After the -i, input the video file name to be processed
    # use crop: 150:200:840:500 for standard, crops will have to be changed from time to time due to video camera placement
    # With larger videos change the %.png to a larger number than 04d 
    os.system("ffmpeg -ss 00:02:27.000 -i moreWork.mp4 -an -vf crop=150:200:990:500,eq=contrast=10 images3/%06d.png") 
    # After the -i, input the video file name to be processed, change frames2.csv if needed
    os.system("ffprobe -f lavfi -i movie=moreWork.mp4 -show_frames -show_entries frame=pkt_pts_time -of csv=p=0 > frames3.csv")
    print 'Successful'
except:
    print 'Error Occurred'


# In[3]:

# Analyization of the background
def analys(i,k):
    val = rgb_im.getpixel((i, k))
    # values inside getpixel are the px of the location of each symbol
    if(val == (255,255,255)):
        return False
    else:
        return True


# In[4]:

# Analyization of the pixels, checks two areas because there's a shift on where the hashes are placed
def analys2(i,k,m,n) :
    val0 = rgb_im.getpixel((i,k))
    val1 = rgb_im.getpixel((m,n))
    r0,g0,b0 = val0
    r1,g1,b1 = val1
    if ((abs(r0-g0) <= 5 and abs(b0-g0) <= 3) or (abs(r1-g1) <= 5 and abs(b1-g1) <= 3)):
        if (checkForBlack(val0) == True or checkForBlack(val1) == True):
            return True
        elif (val0 == (255,255,255) or val1 == (255,255,255)):
            return
        else:
            return 'NaN'
    else:
        return False


# In[5]:

def checkForBlack(rgb_val):
    if (rgb_val == (0,0,0) or rgb_val == (192,192,192) or rgb_val == (169,169,169) or rgb_val == (128, 128, 128)
       or rgb_val == (105, 105, 105) or rgb_val == (211, 211, 211)):
        return True


# In[6]:

df = pd.DataFrame()
time_stamp = 0
frame = 0
indir = 'images3'
# f(73,31) s(67,49) t(61,66) fth(58.83), bg(34,24) for standard
for root, dirs, filenames in os.walk(indir):
    for f in sorted(os.listdir(indir)):
        log = open(os.path.join(root, f), 'r')
        im = Image.open(log)
        pix = im.load()
        rgb_im = im.convert('RGB')    
        first_symb = analys2(59,37,53,35)
        second_symb = analys2(56,55,44,52)
        third_symb = analys2(53,74,42,71)
        fourth_symb = analys2(49,94,38,91)
        background = analys(34,24)
        if(background == False):
            df = df.append(pd.DataFrame({'Background': background, 'First': first_symb, 'Second': second_symb, 'Third': third_symb, 'Fourth': fourth_symb, }, index=[frame]), ignore_index=False)
        else:
            df = df.append(pd.DataFrame({'Background': background, 'First': 'NaN', 'Second': 'NaN', 'Third': 'NaN', 'Fourth': 'NaN', }, index=[frame]), ignore_index=False)
        frame = frame + 1

df.head(10) # Here for debugging purposes


# In[8]:

# Reads from frames2.csv file and combines to have timestamp and dataframe together
Time = pd.read_csv("frames3.csv", 
                  names = ["Time_stamp"])
result = pd.concat([df, Time], axis=1, join='inner')

result = result.reindex(columns=['Time_stamp','Background', 'First', 'Second', 'Third', 'Fourth']).to_csv('results3.csv', index=True)
result


# In[47]:

# Purpose of this is to read results csv file and return only the relevant indexes with specific keypresses
# need help with outputting the relevant indexes with the True values to another csv (?)
newReader = pd.read_csv('results3.csv')
firstKP = False
secondKP = False
thirdKP = False
fourthKP = False
pinFound = False
for index, row in newReader.iterrows():
    if (pinFound == False):
        if (newReader.First.iloc[index] == True and firstKP == False and pd.isnull(newReader['Second'].iloc[index]) == True
           and pd.isnull(newReader['Third'].iloc[index]) == True and pd.isnull(newReader['Fourth'].iloc[index]) == True):
            #print newReader.iloc[[index]] #These are here just incase
            print newReader.Time_stamp.iloc[[index]]
            firstKP = True
        elif (newReader.Second.iloc[index] == True and secondKP == False and pd.isnull(newReader['Third'].iloc[index]) == True
             and pd.isnull(newReader['Fourth'].iloc[index]) == True):
            #print newReader.iloc[[index]]
            print newReader.Time_stamp.iloc[[index]]
            secondKP = True
        elif (newReader.Third.iloc[index] == True and thirdKP == False and pd.isnull(newReader['Fourth'].iloc[index]) == True):
            #print newReader.iloc[[index]]
            print newReader.Time_stamp.iloc[[index]]
            thirdKP = True
        else:
            if (newReader.Fourth.iloc[index] == True and fourthKP == False 
                and pd.isnull(newReader['First'].iloc[index]) == False 
                and pd.isnull(newReader['Second'].iloc[index]) == False 
                and pd.isnull(newReader['Third'].iloc[index]) == False):
                print newReader.iloc[[index]]
                print newReader.Time_stamp.iloc[[index]]
                fourthKP = True
                pinFound = True
            elif (pd.isnull(newReader['Fourth'].iloc[index]) == True and fourthKP == True) : 
                firstKP = False
                secondKP = False
                thirdKP = False
                fourthKP = False
    else:
        pinFound = False
        print '--------------------------------------------------------------------'


# In[ ]:



