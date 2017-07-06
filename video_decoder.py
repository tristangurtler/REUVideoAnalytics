##
# REUVideoDecoder.py
# This program obtains timestamps from our videos marking when asterisks appear on our ATM
# @author: Denisolt Shakhbulatov, Kendall Molas, Tristan Gurtler

from PIL import Image
import sys
import pandas as pd
import os
import csv
import argparse

# units are frames/second
VIDEO_RECORDING_FREQUENCY = 120

##
# This function takes a video and grabs all the individual frames from it
#
# @input video_name - the name of the video file we want to get frames from
def get_frames_from_video(video_name):
    ##
    # This is a range (from a pixel 150 from the left and 200 from the top,
    # to 990 from the left and 500 from the top) that should be able to
    # capture the PIN entry box in the video (this is determined empirically)
    frame_cropper_range = "150:200:990:500"

    ##
    # This sets the frame image names to be 6 digit numbers that are zero-padded on the left.
    # Larger videos may require more padding
    image_name_template = "%06d"

    # Create the directory for frames to be stored
    os.system("mkdir images")

    ##
    # Get every frame from our videos into its own .png file
    #
    # Note that we assume the contrast is sufficiently high so that we can better distinguish asterisks from their background
    # (this can be accomplished with external video editors, if necessary)
    os.system("ffmpeg -i " + video_name + " -an -vf crop=" + frame_cropper_range + ",eq=contrast=10 images/" + image_name_template + ".png") 

##
# This function checks if the image we are looking at is actually a PIN entry screen at all
#
# @input image - the image we want to check for being a PIN Entry screen
# @returns whether or not we are in a PIN Entry screen
def is_in_PIN_entry(image):
    ##
    # This is a location (determined empirically) that should always be inside the PIN entry box
    # (i.e. blank and white) unless we are in a screen that is not PIN entry (where it will not be white)
    background_coordinate = (34,24)
    val = image.getpixel(background_coordinate)
    
    # Return whether or not our chosen location is white, and therefore if it is in the PIN entry box
    return val == (255,255,255)


# This function checks if a given color (by rgb values) is black or gray
def is_color_black(r, g, b):
    flag_color_is_grayscale = r == g and g == b
    flag_color_is_dark = r <= 211 and g <= 211 and b <= 211
    
    return flag_color_is_grayscale and flag_color_is_dark

##
# This function checks at specified locations to determine if an asterisk is present there
#
# @input image - the image we want to check if an asterisk has appeared inside of
# @input coord - the coordinate we want to check if an asterisk has appeared at
# @returns whether or not an asterisk has appeared at the specified location
def is_asterisk_present(image, coord):
    r, g, b = image.getpixel(coord)
    
    return is_color_black(r, g, b)

##
# This function checks at specified locations to determine if an asterisk is present there
#
# @input image - the image we want to check if an asterisk has appeared inside of
# @input coord_topleft - the top left corner of the box we are checking
# @input coord_bottomright - the bottom right corner of the box we are checking
# @input threshold - what percentage of pixels should be black to determine that an asterisk has appeared
# @returns whether or not an asterisk has appeared at the specified location
def is_asterisk_present_in_area(image, coord_topleft, coord_bottomright, threshold=0.7):
    total_pixels = 0
    num_black_pixels = 0

    # range through our box and check for black pixels
    for x in range(coord_topleft[0], coord_bottomright[0] + 1):
        for y in range(coord_topleft[1], coord_bottomright[1] + 1):
            curr = (x,y)
            r, g, b = image.getpixel(curr)
            if is_color_black(r, g, b):
                num_black_pixels += 1
            total_pixels += 1

    return (float(num_black_pixels) / total_pixels) >= threshold

##
# This function runs through every frame we collected and checks if asterisks have appeared in each
#
# @returns a dictionary where the keys are frame numbers and the values are a list of booleans showing what asterisks have appeared
def find_asterisk_appearances():
    # the directory where all our frame images are
    indir = 'images'

    ##
    # default locations for each asterisk
    # (there are two for each, because they move on our feed sometimes)
    # (determined empirically)
    first_asterisk_loc_1 = (59, 37)
    first_asterisk_loc_2 = (53, 35)
    second_asterisk_loc_1 = (56, 55)
    second_asterisk_loc_2 = (44, 52)
    third_asterisk_loc_1 = (53, 74)
    third_asterisk_loc_2 = (42, 71)
    fourth_asterisk_loc_1 = (49, 94)
    fourth_asterisk_loc_2 = (38, 91)

    asterisk_appearances = dict()
    frame = 0

    # walk through every frame
    for root, dirs, filenames in os.walk(indir):
        for f in sorted(os.listdir(indir)):
            im = Image.open(open(os.path.join(root, f), 'r'))
            rgb_im = im.convert('RGB')

            # ignore all cases where we're just looking at things that aren't PIN entry
            if is_in_PIN_entry(rgb_im):
                # but check on each asterisk in all frames that are PIN entry
                first_asterisk = is_asterisk_present(rgb_im, first_asterisk_loc_1) or is_asterisk_present(rgb_im, first_asterisk_loc_2)
                second_asterisk = is_asterisk_present(rgb_im, second_asterisk_loc_1) or is_asterisk_present(rgb_im, second_asterisk_loc_2)
                third_asterisk = is_asterisk_present(rgb_im, third_asterisk_loc_1) or is_asterisk_present(rgb_im, third_asterisk_loc_2)
                fourth_asterisk = is_asterisk_present(rgb_im, fourth_asterisk_loc_1) or is_asterisk_present(rgb_im, fourth_asterisk_loc_2)
                
                asterisk_appearances[frame] = [first_asterisk, second_asterisk, third_asterisk, fourth_asterisk]
            
            frame += 1

    return asterisk_appearances

##
# This function traces through every asterisk appearance and tracks the real time difference between asterisk appearances, per PIN
#
# @input asterisk_appearances - the dictionary of frames to what asterisks have appeared
# @returns a list of lists, where each sublist is the timings associated with an individual PIN entry
def obtain_timing_sequences(asterisk_appearances):
    list_of_all_pin_entries = []
    
    prev_frame = 0
    num_asterisks = 0
    current_pin_entry = []
    
    for frame, asterisks in asterisk_appearances.items():
        # when no asterisks have appeared yet, just watch for the first
        if num_asterisks == 0:
            if asterisks[0]:
                prev_frame = frame
                num_asterisks += 1

        # after one asterisk has appeared...
        elif num_asterisks == 1:
            # ...watch for it to be deleted; if so, it's not a big deal, we start over from scratch
            if not asterisks[0]:
                num_asterisks -= 1
                current_pin_entry = []
            # ...watch for the next one; jot down the frame difference between appearances and move on
            elif asterisks[1]:
                current_pin_entry.append(frame - prev_frame)
                prev_frame = frame
                num_asterisks += 1

        # after multiple asterisks have appeared...
        elif num_asterisks == 2 or num_asterisks == 3:
            # ...watch for them to be deleted; if so, there will necessarily be a "CLEAR" press in the middle of our data. Jot it down
            if not asterisks[num_asterisks - 1]:
                current_pin_entry.append(frame - prev_frame)
                prev_frame = frame
                num_asterisks -= 1
            # ...watch for the next one again and move on
            elif asterisks[num_asterisks]:
                current_pin_entry.append(frame - prev_frame)
                prev_frame = frame
                num_asterisks += 1

        # after 4 asterisks have appeared...
        else:
            # watch until something happens
            if not asterisks[3]:
                # if all asterisks are gone, enter was pressed: jot it down and look for a new PIN
                if not asterisks[2] and not asterisks[1] and not asterisks[0]:
                    current_pin_entry.append(frame - prev_frame)
                    list_of_all_pin_entries.append(current_pin_entry)
                    current_pin_entry = []
                    num_asterisks = 0
                # if the last asterisk is the only one missing, clear was pressed. Jot it down, but stay on this PIN
                else:
                    current_pin_entry.append(frame - prev_frame)
                    prev_frame = frame
                    num_asterisks -= 1

    # turn our frame difference timings into real world timings (in microseconds)
    list_of_all_pin_entries = [[float(x * (10 ** 6)) / VIDEO_RECORDING_FREQUENCY for x in sublist] for sublist in list_of_all_pin_entries]
    return list_of_all_pin_entries

def main(args):
    get_frames_from_video(args.video_file)
    asterisk_appearances = find_asterisk_appearances()
    pin_entries = obtain_timing_sequences(asterisk_appearances)

    print "Timings between keystrokes in microseconds:"
    for single_pin in pin_entries:
        printable = [str(x) for x in single_pin]
        print ", ".join(printable)

# python video_decoder.py <video_file>
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process videos for timing data')
    parser.add_argument('video_file', help='the video file')
    
    args = parser.parse_args()
    
    main(args)