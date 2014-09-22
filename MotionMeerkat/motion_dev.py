#!/usr/bin/env python

Usage = """

Welcome to MotionMeerkat!

Automated capture of motion frames from a video file.

For help, see the wiki: https://github.com/bw4sz/OpenCV_HummingbirdsMotion/wiki

Default values for parameters are in parenthesis. To select default hit enter.

Affirmative answers to questions are y, negative answers n

Please use double quotes for file paths, but no quotes for any other responses. 

"""
import cv2
import numpy as np
import time
import sys, os, random, hashlib
import re
from math import *
import glob
from datetime import datetime, timedelta
import csv
import argparse
from shapely.ops import cascaded_union
import shapely.geometry as sg
import traceback
import sourceM
import BackgroundSubtractor
          
###Create motion class with sensible defaults

class Motion:

        def __init__(self):
                #Empty list for time stamps
                self.stamp=[]

                #Write header row
                self.stamp.append(("Time","Frame","X","Y"))
                #Empty list for area counter
                self.areaC=[]
                self.areaC.append(("Time","Frame","X","Y"))

        #If there were system arguments
                self.parser = argparse.ArgumentParser()

                #Read in system arguments if they exist
                if len(sys.argv)< 2:
                        print Usage
                else:
                    self.parser.add_argument("--runtype", help="Batch or single file",default='file')
                    self.parser.add_argument("--batchpool", help="run directory of videos",type=str)
                    self.parser.add_argument("--inDEST", help="path of single video",type=str,default="C:/Program Files (x86)/MotionMeerkat/PlotwatcherTest.tlv")
                    self.parser.add_argument("--fileD", help="output directory",default="C:/MotionMeerkat")
                    self.parser.add_argument("--subMethod", help="Background Subtraction Method",type=str,default="Acc")                    
                    self.parser.add_argument("--adapt", help="Adaptive background averaging",action='store_true',default=False)
                    self.parser.add_argument("--accAvg", help="Fixed background averaging rate",default=0.35,type=float)
                    self.parser.add_argument("--frameHIT", help="expected percentage of motion frames",default=0.1,type=float)
                    self.parser.add_argument("--floorvalue", help="minimum background averaging",default=0.01,type=float)
                    self.parser.add_argument("--threshT", help="Threshold of movement",default=30,type=int)
                    self.parser.add_argument("--minSIZE", help="Minimum size of contour",default=0.1,type=float)
                    self.parser.add_argument("--burnin", help="Delay time",default=0,type=int)
                    self.parser.add_argument("--scan", help="Scan one of every X frames for motion",default=0,type=int)
                    self.parser.add_argument("--frameSET", help="Set frame_rate?",action='store_true',default=False)
                    self.parser.add_argument("--plotwatcher", help="Camera was a plotwatcher?",action="store_true",default=False)
                    self.parser.add_argument("--frame_rate", help="frames per second",default=0)
                    self.parser.add_argument("--set_ROI", help="Set region of interest?",action='store_true',default=False)
                    self.parser.add_argument("--ROI_include", help="include or exclude?",default="include")
                    self.parser.add_argument("--set_areacounter", help="Set region to count area",action="store_true",default=False)
                    self.parser.add_argument("--makeVID", help="Output images as 'frames','video','both', 'none' ?",default='frames')
                    self.args = self.parser.parse_args(namespace=self)

                    print "\n"
                    print "\n"
                                
        #########################################
        #Get user inputs if no system arguments
        #########################################
        def arguments(self):
                if(len(sys.argv)< 2):
                        #Batch or single file
                        self.runtype=raw_input("'batch' run or single 'file'? (file):\n")   
                        if not self.runtype: self.runtype="file"
                        
                        if(self.runtype=="file"):
                                self.inDEST=ask_file()
                                        
                        if(self.runtype=="batch"):
                                self.batchpool=raw_input("Enter folder containing videos:\n")
                        
                        #Destination of file
                        self.fileD=raw_input("File Destination Folder (C:/MotionMeerkat/):\n")   
                        if not self.fileD: self.fileD = "C:/MotionMeerkat/"

                        #Sensitivity to movement
                        self.accAvg=ask_acc()
                        if not self.accAvg: self.accAvg=0.35

                        #thresholding, a way of differentiating the background from movement, higher values (0-255) disregard more motion, lower values make the model more sensitive to motion
                        self.threshT=raw_input("Threshold for movement tolerance\nranging from 0 [all] to 255 [no movement] (30):\n")
                        if not self.threshT: self.threshT = 30
                        else: self.threshT=float(self.threshT)

                        #minimum size of contour object
                        self.minSIZE=raw_input("Minimum motion contour size (0.2):\n")
                        if not self.minSIZE: self.minSIZE = 0.2
                        else: self.minSIZE=float(self.minSIZE)

                        self.advanced= 'y'==raw_input("Set advanced options? (n) :\n")
                        
                        if self.advanced:
                            
                            #Set background subtractor
                            self.subMethod=raw_input("Accumulated Averaging [Acc] or Mixture of Gaussian [MOG] background method? (Acc)")
                            if not self.subMethod: self.subMethod="Acc"
                            
                            #Should accAVG be adapted every 10minutes based on an estimated hitrate
                            self.adapt= 'y'==raw_input("Adapt the motion sensitivity based on hitrate? (n) :\n")      
                                        
                            if self.adapt:
                                        self.accAvg=ask_acc()
                                        if not self.accAvg: self.accAvg = 0.35
                                        
                                        #Hitrate, the expected % of frames per 10 minutes - this is a helpful adaptive setting that helps tune the model, this will be multiplied the frame_rate
                                        self.frameHIT=raw_input("Expected percentage of frames with motion (decimal 0.01):\n")
                                        if not self.frameHIT: self.frameHIT = 0.01
                                        else: self.frameHIT=float(self.frameHIT)
                                        
                                        #Floor value, if adapt = TRUE, what is the minimum AccAVG allowed. If this is unset, and it is a particularly still video, the algorithm paradoically spits out alot of frames, because its trying to find the accAVG that matches the frameHit rate below. We can avoid this by simply placing a floor value for accAVG 
                                        self.floorvalue=raw_input("Minimum allowed sensitivity (0.05):\n")
                                        if not self.floorvalue: self.floorvalue = 0.05
                                        else: self.floorvalue=float(self.floorvalue)
                        
                                #Skip initial frames of video, in case of camera setup and shake.       
                            self.burnin= raw_input("Burn in, skip initial minutes of video (0):\n")
                            if not self.burnin: self.burnin = 0
                            else: self.burnin=float(self.burnin)
      
                                #Decrease frame rate, downsample
                            self.scan= raw_input("Scan one of every X frames (0):\n")
                            if not self.scan: self.scan = 0
                            else: self.scan=int(self.scan)

                            #Manually set framerate?
                            self.frameSET= "y" == raw_input("Set frame rate in fps? (n):\n")
                                
                            #Set frame rate.
                            if self.frameSET:
                                    self.frame_rate = raw_input("frames per second:\n")
                            else: self.frame_rate=0
                                
                            #There are specific conditions for the plotwatcher, because the frame_rate is off, turn this to a boolean       
                            self.plotwatcher='y'==raw_input("Does this video come from a plotwatcher camera? (n) :\n")
                            if not self.plotwatcher: self.plotwatcher = False
                            
                            #set ROI
                            self.set_ROI= "y" == raw_input("Subsect the image by selecting a region of interest? (n) :\n")
                                
                            if self.set_ROI:
                                    self.ROI_include=raw_input("Subregion of interest to 'include' or 'exclude'?:\n")
                            else: self.ROI_include='exclude'

                                #Create area counter by highlighting a section of frame
                            self.set_areacounter='y'==raw_input("Highlight region for area count? (n) \n")
                            if not self.set_areacounter: self.set_areacounter=False

                            #make video by stringing the jpgs back into an avi
                            self.makeVID=raw_input("Write output as 'video', 'frames','both','none'? (frames):\n")
                            if not self.makeVID:self.makeVID="frames"

                        else:
                                self.floorvalue=0
                                self.frameHIT=0
                                self.adapt=False
                                self.makeVID="frames"
                                self.scan = 0
                                self.burnin = 0
                                self.ROI_include='exclude'
                                self.frameSET=False
                                self.plotwatcher=False
                                self.frame_rate=0
                                self.set_ROI=False
                                self.set_areacounter=False
                                
        ###########Inputs Read in #################

        #define video function
        #Find path of jpegs

        def videoM(self):
                if self.makeVID not in ("video","both"):
                        return("")
                
                normFP=os.path.normpath(self.inDEST)
                (filepath, filename)=os.path.split(normFP)
                (shortname, extension) = os.path.splitext(filename)
                (_,IDFL) = os.path.split(filepath)

                #we want to name the output a folder from the output destination with the named extension 
                if self.runtype == 'batch':
                        file_destination=os.path.join(self.fileD,IDFL)
                        file_destination=os.path.join(file_destination,shortname)
                        
                else:
                        file_destination=os.path.join(self.fileD,shortname)

                if self.fileD =='':
                        vidDEST=os.path.join(filepath, shortname,shortname +'.avi')
                else:
                        vidDEST=os.path.join(self.fileD, shortname,shortname +'.avi')

                print("Video output path will be %s" % (vidDEST))

                if not os.path.exists(file_destination):
                        os.makedirs(file_destination)

                #Find all jpegs
                jpgs=glob.glob(os.path.join(file_destination,"*.jpg"))                  

                #Get frame rate and size of images
                cap = cv2.VideoCapture(self.inDEST)

                        #Get frame rate if the plotwatcher setting hasn't been called
                        # not the most elegant solution, but get global frame_rate
                if not self.frameSET:
                        fr=round(cap.get(5))
                else:
                        fr=self.frame_rate

                orig_image = cap.read()[1]  

                ###Get information about camera and image
                width = np.size(orig_image, 1)
                height = np.size(orig_image, 0)
                frame_size=(width, height)                      

                # Define the codec and create VideoWriter object
                fourcc = cap.get(6)
                
                out = cv2.VideoWriter(vidDEST,int(fourcc),float(fr), frame_size)                    

                #split and sort the jpg names
                jpgs.sort(key=getint)

                #Loop through every frame and write video
                for f in jpgs:
                        fr=cv2.imread(f)
                        out.write(fr)

                # Release everything if job is finished
                cap.release()
                out.release()

                #If video only, delete jpegs
                if self.makeVID == "video":
                        for f in jpgs:
                                os.remove(f)
                 
        #Define the run function
        def run(self):
                
                #Report name of file
                sys.stderr.write("Processing file %s\n" % (self.inDEST))
                
                #start timer
                self.start=time.time()
                
                #Define directories, here assuming that we want to append the file structure of the last three folders to the file destination
                normFP=os.path.normpath(self.inDEST)
                (filepath, filename)=os.path.split(normFP)
                (shortname, extension) = os.path.splitext(filename)
                (_,IDFL) = os.path.split(filepath)
                
                #we want to name the output a folder from the output destination with the named extension        
                print("AccAvg begin value is: %s" % (self.accAvg))

                ###########Failure Classes, used to format output and illustrate number of frames
                ##No motion, the frame was not different enough compared to the background due to accAvg 
                self.nodiff=0
                ##No contours, there was not enough motion compared to background, did not meet threshold
                self.nocountr=0
                ###Not large enough, the movement contour was too small to be included 
                self.toosmall=0      
                
                #If its batch, give an extra folder
                if self.runtype == 'batch':
                        file_destination=os.path.join(self.fileD,IDFL,shortname)
                else:
                        file_destination=os.path.join(self.fileD,shortname)
                
                if not os.path.exists(file_destination):
                        os.makedirs(file_destination)
                
                print("Output path will be %s" % (file_destination))
                
                # Create a log file with each coordinates

                #create hit counter to track number of outputs
                hitcounter=0
                
                #Begin video capture
                cap = cv2.VideoCapture(self.inDEST)
                
                #Get frame rate if the plotwatcher setting hasn't been called
                # not the most elegant solution, but get global frame_rate
                if not self.frameSET:
                                
                        self.frame_rate=round(cap.get(5))
                
                #get frame time relative to start
                frame_time=cap.get(0)     
                
                #get total number of frames
                total_frameC=cap.get(7)     

                sys.stderr.write("frame rate: %s\n" % self.frame_rate)
                
                ####Burnin and first image
                #Count the number of frames returned
                frame_count=0
                self.total_count=0
                
                #apply burn in, skip the the first X frames according to user input
                for x in range(1,int(float(self.burnin) * int(self.frame_rate) * 60)): 
                        cap.grab()
                        frame_count=frame_count+1
                        
                print("Beginning Motion Detection")
                #Set frame skip counter if downsampling 
                frameSKIP=0
                
                # Capture the first frame from file for image properties
                orig_image = cap.read()[1]  
                        
                #Have to set global for the callback, feedback welcome. 
                global orig
                
                if self.plotwatcher:
                        #cut off the bottom 5% if the timing mechanism is on the bottom. 
                        orig = orig_image[1:700,1:1280]
                else:
                        orig = orig_image.copy()
                
                #make a copy of the image
                orig_ROI=orig.copy()

                #make a copy for the markup
                iorig=orig.copy()    

                #Set region of interest 
                if self.set_ROI:
                        
                        roi=sourceM.Urect(iorig)
                        
                        if self.ROI_include == "include": display_image=orig_ROI[roi[1]:roi[3], roi[0]:roi[2]]
                        else:
                                orig_ROI[roi[1]:roi[3], roi[0]:roi[2]]=255
                                display_image=orig_ROI                        
                else:
                        display_image=orig              
                        
                width = np.size(display_image, 1)
                height = np.size(display_image, 0)
                frame_size=(width, height)

                ###If set area counter, draw another box.
          
                if self.set_areacounter:
                        area_box=sourceM.Urect(orig,"Set Area Counter")
                
                        #Draw and show the area to count inside
                        cv2.rectangle(orig, (area_box[1],area_box[3]), (area_box[0],area_box[2]), (255,0,0), 1)     
                        #display("AreaCounter",2000,orig)
                        
                ############################
                #Initialize Background Subtraction
                ############################
                
                backgr=BackgroundSubtractor.Background(subMethod,orig_image,self.accAvg,self.threshT)
        
                frameC_announce=0
                
                #Set time
                t0 = time.time()

                #Start with motion flag on
                noMotion=False
        
                while True:
                        
                        #Was the last frame no motion; if not, scan frames
                        if not self.scan ==0:
                                if noMotion:
                                        for x in range(1,self.scan):
                                                cap.grab()
                                                frame_count=frame_count+1
                                else:
                                        pass
                        else:
                                pass
                                        
                        # Capture frame from file
                        ret,camera_imageO = cap.read()
                        if not ret:
                                #finalize the counters for reporting
                                self.frame_count=frame_count
                                self.file_destination=file_destination
                                break
                                      
                        #Cut off the bottom 5% if the plotwatcher option is called. 
                        if not self.plotwatcher:
                                camera_image = camera_imageO.copy()     
                        else:
                                camera_image = camera_imageO[1:700,1:1280]
                        
                        #If set roi, subset the image
                        if not self.set_ROI:
                                camera_imageROI=camera_image
                        else:
                                if self.ROI_include == "include":camera_imageROI=camera_image[roi[1]:roi[3], roi[0]:roi[2]]
                                else: 
                                        #Exclude area by making it a white square
                                        camera_imageROI=camera_image.copy()
                                        camera_imageROI[roi[1]:roi[3], roi[0]:roi[2]]=255
                                        
                        frame_count += 1
                        frame_t0 = time.time()
                        #create iterable for scanner
                
                        #Print trackbar
                        #for some videos this capture doesn't work, and we need to ignore frame
                        if not total_frameC == 0.0:
                                #This is a bit convulted, but because of scanning, we might miss the flag to calculate time, give it a step size equal to scan size
                                countR=frame_count - np.arange(0,self.scan+1)
                                
                                #If percent compelted is a multiple of 10, print processing rate.
                                #format frame count to percentage and interger
                                numbers = [ round(x/float(total_frameC),3)*100 for x in countR ]
                                
                                #is frame count a multiple of 10
                                if any([x %10 ==0 for x in numbers]):
                                        
                                        fc=float(frame_count)/total_frameC*100
                                        
                                        #Give it a pause feature so it doesn't announce twice on the scan, i a bit ugly, but it doesn't run very often.
                                        #if the last time the percent complete was printed was within the scan range, don't print again. 
                                        if abs(frameC_announce - frame_count) >= self.scan:
                                                print("%.0f %% completed" % fc)
                                                print( "%.0f candidate motion frames" % total_count)
                                                frameC_announce=frame_count                                                
                                                
                                        #Reset the last time it was printed. 
                                        
                        ####Adaptively set the aggregate threshold, we know that about 95% of data are negatives. 
                        #set floor flag, we can't have negative accAVG
                        floor=0
                        if self.adapt:
                                       sourceM.adapt() 


                        #############################
                        ##BACKGROUND SUBTRACTION
                        #############################
                        grey_image=backgr.BackGroundSub(camera_imageROI)
                        
                        #############################
                        ###Contour filters
                        #############################
                        
                        bound_center=backgr.contourFilter(grey_image)
    
                        if len(bound_center) == 0:
                                self.toosmall=self.toosmall+1
                                noMotion=True                   
                                continue

                        #Set flag for inside area
                        inside_area=False
                        if self.set_areacounter:
                        #test drawing center circle
                                for box in bound_center:
                                        
                                        #Do this the simple way for now

                                        #is the x coordinate within
                                        if area_box[2] > box[0] > area_box[0]:
                                                if area_box[3] > box[1] > area_box[1]:
                                                                inside_area= not inside_area
                                                                if self.ROI_include == "exclude":
                                                                        cv2.rectangle(camera_imageO,(area_box[0],area_box[1]),(area_box[2],area_box[3]),(242,221,61),thickness=1,lineType=4)
                                                                else:
                                                                        cv2.rectangle(display_image,(area_box[0],area_box[1]),(area_box[2],area_box[3]),(242,221,61),thickness=1,lineType=4)
                                                                
                                                                
                        ##################################################
                        #Write image to file
                        ##################################################
                        
                        if not self.makeVID == "none":
                                if self.makeVID in ("frames","both"):
                                        if self.ROI_include == "exclude":
                                                cv2.imwrite(file_destination + "/"+str(frame_count)+".jpg",camera_imageO)
                                        else:
                                                cv2.imwrite(file_destination + "/"+str(frame_count)+".jpg",display_image)

                        
                        #save the frame count and the time in video, in case user wants to check in the original
                        #create a time object, this relies on the frame_rate being correct!
                        #set seconds
                        sec = timedelta(seconds=int(frame_count/float(self.frame_rate)))             
                        d = datetime(1,1,1) + sec

                        for target in bound_center:
                                stampadd=(str("%d:%d:%d "  % (d.hour,d.minute, d.second)), int(frame_count),target[0],target[1])
                                self.stamp.append(stampadd)

                        #if inside area and counter is on, write stamp to a seperate file
                        if self.set_areacounter & inside_area:
                                for target in bound_center:
                                        stampadd=(str("%d:%d:%d "  % (d.hour,d.minute, d.second)), int(frame_count),target[0],target[1])
                                        self.areaC.append(stampadd)
                                
                       ##################################################
                        #Have a returned counter to balance hitRate
                        hitcounter=hitcounter+1
                        self.total_count=self.total_count+1
                        #set flag to motion
                        noMotion=False
        
        ########################################
        ###Run Analysis on a Pool of videos
        ########################################
        def wrap(self) :
                #quick error check.
                if self.runtype=="file":
                        if os.path.isfile(self.inDEST): pass
                        else:
                                print("File path does not exist!")
                else:
                        if os.path.isdir(self.batchpool): pass
                        else:
                                print("Directory does not exist!")

                ###Run Batch Mode                
                if (self.runtype == "batch"):
                        ##Overall destination
                        
                        videoPool= []
                        #Create Pool of Videos
                        for (root, dirs, files) in os.walk(self.batchpool):
                                for files in files:
                                        if files.endswith((".TLV",".AVI",".avi",".MPG",".mp4",".MOD",".MTS",".wmv",".WMV")):
                                                videoPool.append(os.path.join(root, files))
                        
                        for vid in videoPool:      
                             
                                #Place run inside try catch loop; in case of error, step to next video
                                ##Run Motion Function
                                #override to set the inDEST file to loop from batch videos
                                self.inDEST=vid
                                try:
                                        self.run()
                                        self.videoM()
                                        self.report()
                                except Exception, e:
                                        print( "Error %s " % e + "\n" )
                                        print 'Error in Video:',vid

                ###If runtype is a single file - run file destination        
                if (self.runtype == "file"):
                     
                    try:
                            self.run()
                            self.videoM()
                            self.report()                                
                    except:
                        traceback.print_exc()
                        print 'Error in input file:',self.inDEST

        def report(self):
                #Create log file
                log_file_report = self.file_destination + "/" + "Parameters_Results.log"
                log_report = file(log_file_report, 'a' )

                #Print parameters
                #Batch or single file
                log_report.write("\nRun type: %s" % self.runtype)
                if self.runtype=="file":
                        log_report.write("\nInput file path: %s" % self.fileD)
                        
                else:
                        log_report.write("\nInput file path: %s" % self.batchpool)
                log_report.write("\nOutput dir: %s" % self.inDEST)
                log_report.write("\nAdapt accAvg? %s" % self.adapt)
                
                if self.adapt:
                        log_report.write("\nExpected hitrate: %s" % self.frameHIT)
                        log_report.write("\nMinimum accAvg: %s" % self.floorvalue)
                log_report.write("\nThreshold %s" % self.threshT)
                log_report.write("\nMinimum contour area: %s" % self.minSIZE)
                log_report.write("\nBurnin: %s" % self.burnin)
                log_report.write("\nScan frames: %s" % self.scan)
                
                if self.frameSET:
                        log_report.write("\nManual framerate: %s" % self.frame_rate)
                log_report.write("\nSet ROI: %s" % self.ROI_include)
                log_report.write("\nArea counter?: %s" % self.set_areacounter)
                log_report.write("\nOutput type?: %s\n\n" % self.makeVID)

                #Ending time
                end=time.time()

                #total_time()
                total_min=(end-self.start)/60

                #processed frames per second
                pfps=float(self.frame_count)/(total_min*60)

                ##Write to log file
                log_report.write("Total run time (min): %.2f \n " % total_min)
                log_report.write("Average frames per second: %.2f \n " % pfps)

                #End of program, report some statistic to screen and log
                #log
                log_report.write("\n Thank you for using MotionMeerkat! \n")
                log_report.write("Candidate motion events: %.0f \n " % self.total_count )
                log_report.write("Frames skipped due to AccAvg: %.0f \n " % self.nodiff)
                log_report.write("Frames skipped due to Threshold: %.0f \n " % self.nocountr)
                log_report.write("Frames skipped due to minSIZE: %.0f \n " % self.toosmall)
                log_report.write("Total frames in files: %.0f \n " % self.frame_count)
                rate=float(self.total_count)/self.frame_count*100
                log_report.write("Hitrate: %.2f %% \n" % rate)
                log_report.write("Exiting")

                #print to screen
                print("\n\nThank you for using MotionMeerkat! \n")
                print("Total run time (min): %.2f \n " % total_min)
                print("Average frames processed per second: %.2f \n " % pfps)   
                print("Candidate motion events: %.0f \n " % self.total_count )
                print("Frames skipped due to AccAvg: %.0f \n " % self.nodiff)
                print("Frames skipped due to Threshold: %.0f \n " % self.nocountr)
                print("Frames skipped due to minSIZE: %.0f \n " % self.toosmall)
                print("Total frames in files: %.0f \n " % self.frame_count)

                rate=float(self.total_count)/self.frame_count*100
                print("Hitrate: %.2f %% \n" % rate)

                #Write csv of time stamps and frame counts
                #file name
                time_stamp_report = self.file_destination + "/" + "Frames.csv"

                with open(time_stamp_report, 'wb') as f:
                        writer = csv.writer(f)
                        writer.writerows(self.stamp)
                if self.set_areacounter:
                        area_report = self.file_destination + "/" + "AreaCounter.csv"
                        with open(area_report, 'wb') as f:
                                writer = csv.writer(f)
                                writer.writerows(self.areaC)
                                        
