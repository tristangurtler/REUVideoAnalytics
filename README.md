# REUVideoAnalytics

Created for the purpose of analyzing video at a certain points in time
Thank you to Denisolt, https://github.com/Denisolt for helping me out with the beginning of this.

## Prequisites
Python<br>Anaconda<br>Jupyter-Notebook<br>FFMPEG

## Usage
### Getting Started
#### Entering in the file name with directory
```python
try:
    os.system("mkdir images")
    # After the -i, input the video file name to be processed
    # Crops will have to be changed from time to time based on video area/placement
    # With larger videos change the %.png to a larger number than %04d 
    os.system("ffmpeg -i (insert video file here) -an -vf crop=150:200:990:500,eq=contrast=10 images3/%06d.png") 
    # After the -i, input the video file name to be processed, change frames.csv if needed
    os.system("ffprobe -f lavfi -i movie=(insert video file here) -show_frames -show_entries frame=pkt_pts_time -of csv=p=0 >       frames.csv")
    print 'Successful'
except:
    print 'Error Occurred'
```
#### Make sure the directories are consistent throughout
```python
indir = 'images'
```
```python
Time = pd.read_csv("frames.csv", ...)
result = result.reindex(columns=['Time_stamp','Background', 'First', 'Second', 'Third', 'Fourth']).to_csv('results.csv', index=True)
```

```python
newReader = pd.read_csv('results.csv')
```

## History

Uploaded: July 5, 2017 12:04 AM

## Credits

StackOverflow<br>Denisolt(https://github.com/Denisolt)<br>Pandas API
