#!/usr/bin/env python

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

class MotionCombined:

        def __init__(self):
                #Empty list for time stamps
                self.stamp=[]

                #Write header row
                self.stamp.append(("Time","Frame","X","Y"))
                #Empty list for area counter
                self.areaC=[]
                self.areaC.append(("Time","Frame","X","Y"))
                
                self.top = 0
                self.bottom = 1
                self.left = 0
                self.right = 1
                
                ###########Failure Classes, used to format output and illustrate number of frames
                ##No motion, the frame was not different enough compared to the background due to accAvg 
                self.nodiff=0
                
                ##No contours, there was not enough motion compared to background, did not meet threshold
                self.nocountr=0
                
                ###Not large enough, the movement contour was too small to be included 
                self.toosmall=0 
                
                #create hit counter to track number of outputs
                self.hitcounter=0      
                
                #Count the number of frames returned
                self.frame_count=0
                self.total_count=0
                
                #Set time and frame constants
                self.frameC_announce=0
    
                #Start with motion flag on
                self.noMotion=False                   
        
        def prep(self):
                
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
                if self.subMethod=="Acc":
                        print("AccAvg begin value is: %s" % (self.accAvg))

                #If its batch, give an extra folder
                if self.runtype == 'batch':
                        self.file_destination=os.path.join(self.fileD,IDFL,shortname)
                else:
                        self.file_destination=os.path.join(self.fileD,shortname)
                
                if not os.path.exists(self.file_destination):
                        os.makedirs(self.file_destination)
                
                print("Output path will be %s" % (self.file_destination))
                
                #########################
                ##Begin video capture
                #########################
                
                ##Get Video Properties
                self.cap = cv2.VideoCapture(self.inDEST)
                #Get frame rate if the plotwatcher setting hasn't been called
                # not the most elegant solution, but get global frame_rate
                if not self.frameSET:
                                
                        self.frame_rate=round(self.cap.get(5))
                
                #get frame time relative to start
                frame_time=self.cap.get(0)     
                #get total number of frames
                self.total_frameC=self.cap.get(7)     
                sys.stderr.write("frame rate: %s\n" % self.frame_rate)
                
                ####Burnin and first image
                
                #apply burn in, skip the the first X frames according to user input
                for x in range(1,int(float(self.burnin) * int(self.frame_rate) * 60)): 
                        self.cap.grab()
                        self.frame_count=self.frame_count+1
                        
                print("Beginning Motion Detection")
                
                #Set frame skip counter if downsampling 
                frameSKIP=0
                
                # Capture the first frame from file for image properties
                orig_image = self.cap.read()[1]  
                        
                #Have to set global for the callback, feedback welcome. 
                global orig
                
                if self.plotwatcher:
                        #cut off the self.bottom 5% if the timing mechanism is on the self.bottom. 
                        orig = orig_image[1:700,1:1280]
                else:
                        orig = orig_image.copy()
                                
                #make a copy of the image
                orig_ROI=orig.copy()

                #make a copy for the markup
                iorig=orig.copy()    

                #Set region of interest 
                if self.set_ROI:
                        self.roi_selected=sourceM.Urect(iorig,"Region of Interest")
                        
                        print(self.roi_selected)
                        
                        if self.ROI_include == "include": self.display_image=orig_ROI[self.roi_selected[1]:self.roi_selected[3], self.roi_selected[0]:self.roi_selected[2]]
                        else:
                                orig_ROI[self.roi_selected[1]:self.roi_selected[3], self.roi_selected[0]:self.roi_selected[2]]=255
                                self.display_image=orig_ROI                             
                else:
                        self.display_image=orig              
                        
                self.width = np.size(self.display_image, 1)
                self.height = np.size(self.display_image, 0)
                frame_size=(self.width, self.height)

                ###If set area counter, draw another box.
                if self.set_areacounter:
                        area_box=sourceM.Urect(orig,"Set Area Counter")

                        #Draw and show the area to count inside
                        cv2.rectangle(orig, (area_box[1],area_box[3]), (area_box[0],area_box[2]), (255,0,0), 1)     
                
                ###Background Constructor, create class
                self.BC=BackgroundSubtractor.Background(self.subMethod,self.display_image,self.accAvg,self.threshT,self.moghistory)
           
######################################################             
##Function to compute background during the video loop
######################################################

        def run(self):

                while True:
                        #Was the last frame no motion; if not, scan frames
                        if not self.scan ==0:
                                if self.noMotion:
                                        for x in range(1,self.scan):
                                                self.cap.grab()
                                                self.frame_count=self.frame_count+1
                                else:
                                        pass
                        else:
                                pass
                                        
                        # Capture frame from file
                        ret,current_image = self.cap.read()
                        if not ret:
                                #If there are no more frames, break
                                break
                                      
                        #Cut off the self.bottom 5% if the plotwatcher option is called. 
                        if not self.plotwatcher:
                                camera_image = current_image   
                        else:
                                camera_image = current_image[1:700,1:1280]
                        
                        #If set roi, subset the image
                        if not self.set_ROI:
                                current_imageROI=camera_image
                        else:
                                if self.ROI_include == "include":current_imageROI=camera_image[self.roi_selected[1]:self.roi_selected[3], self.roi_selected[0]:self.roi_selected[2]]
                                else: 
                                        #Exclude area by making it a white square
                                        current_imageROI=camera_image.copy()
                                        current_imageROI[self.roi_selected[1]:self.roi_selected[3], self.roi_selected[0]:self.roi_selected[2]]=255
                                        
                        self.frame_count += 1
                        frame_t0 = time.time()
                        #create iterable for scanner
                
                        #Print trackbar
                        #for some videos this capture doesn't work, and we need to ignore frame
                        if not self.total_frameC == 0.0:
                                #This is a bit convulted, but because of scanning, we might miss the flag to calculate time, give it a step size equal to scan size
                                countR=self.frame_count - np.arange(0,self.scan+1)
                                
                                #If percent compelted is a multiple of 10, print processing rate.
                                #format frame count to percentage and interger
                                numbers = [ round(x/float(self.total_frameC),4)*100 for x in countR ]
                                
                                #is frame count a multiple of 10
                                if any([x %10 ==0 for x in numbers]):
                                        
                                        fc=float(self.frame_count)/self.total_frameC*100
                                        
                                        #Give it a pause feature so it doesn't announce twice on the scan, i a bit ugly, but it doesn't run very often.
                                        #if the last time the percent complete was printed was within the scan range, don't print again. 
                                        if abs(self.frameC_announce - self.frame_count) >= self.scan:
                                                print("%.0f %% completed" % fc)
                                                print( "%.0f candidate motion frames" % self.total_count)
                                                self.frameC_announce=self.frame_count                                                
                                                
                                        #Reset the last time it was printed. 
                                        
                        ###Adaptively set the aggregate threshold 
                        #set floor flag, we can't have negative accAVG
                        floor=0
                        if self.adapt:
                                sourceM.adapt(frame_rate=self.frame_rate,accAvg=self.accAvg,file_destination=self.file_destination,floorvalue=self.floorvalue,frame_count=self.frame_count) 
                        
                        #############################
                        ###BACKGROUND SUBTRACTION
                        #############################
                        grey_image=self.BC.BackGroundSub(current_imageROI)
                        
                        #######################################
                        ##Contour Analysis and Post-Proccessing
                        #######################################
                        points = []   # Was using this to hold camera_imageROIeither pixel coords or polygon coords.
                        bounding_box_list = []
                        
                        contourImage=grey_image.copy()
                        # Now calculate movements using the white pixels as "motion" data
                        _,contours,hierarchy = cv2.findContours(contourImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE )
                        
                        if len(contours) == 0 :
                                #No movement, add to counter
                                self.nocountr=self.nocountr+1
                                #self.noMotion flag
                                self.noMotion=True
                                continue                    
                        
                        for cnt in contours:
                                bounding_rect = cv2.boundingRect( cnt )
                                point1 = ( bounding_rect[0], bounding_rect[1] )
                                point2 = ( bounding_rect[0] + bounding_rect[2], bounding_rect[1] + bounding_rect[3] )
                                bounding_box_list.append( ( point1, point2 ) )
                                
                        # Find the average size of the bbox (targets), then
                        # remove any tiny bboxes (which are probably just noise).
                        # "Tiny" is defined as any box with 1/10th the area of the average box.
                        # This reduces false positives on tiny "sparkles" noise.
                        box_areas = []
                        for box in bounding_box_list:
                                box_width = box[self.right][0] - box[self.left][0]
                                box_height = box[self.bottom][0] - box[self.top][0]
                                box_areas.append( box_width * box_height )
                                
                        average_box_area = 0.0
                        if len(box_areas): average_box_area = float( sum(box_areas) ) / len(box_areas)
                        
                        trimmed_box_list = []
                        for box in bounding_box_list:
                                box_width = box[self.right][0] - box[self.left][0]
                                box_height = box[self.bottom][0] - box[self.top][0]
                                
                                # Only keep the box if it's not a tiny noise box:
                                if (box_width * box_height) > average_box_area*.3: 
                                        trimmed_box_list.append( box )

                        #shapely does a much faster job of polygon union
                        #format into shapely bounding feature
                        shape_list=[]
                        
                        ## Centroids of each target and hold on to target blobs
                        bound_center=[]
                        bound_casc_box=[]
                        grabCUTimage=camera_image.copy()
                        
                        for out in trimmed_box_list:
                                sh_out=sg.box(out[0][0],out[0][1],out[1][0],out[1][1])
                                shape_list.append(sh_out)

                        #shape_pol=sg.MultiPolygon(shape_list)
                        casc=cascaded_union(shape_list).buffer(1)
                        
                        if casc.type=="MultiPolygon":
                            #draw shapely bounds
                            for p in range(1,len(casc.geoms)):
                                b=casc.geoms[p].bounds
                                if casc.geoms[p].area > ((self.width * self.height) * (float(self.minSIZE/100))):
                                                cv2.rectangle(camera_image,(int(b[0]),int(b[1])),(int(b[2]),int(b[3])),(0,0,255),thickness=2)
                                                        
                                                #Return the centroid to list, rounded two decimals
                                                x=round(casc.geoms[p].centroid.coords.xy[0][0],2)
                                                y=round(casc.geoms[p].centroid.coords.xy[1][0],2)
                                                bound_center.append((x,y))
                                                bound_casc_box.append(casc.geoms[p])
                        else:
                                b=casc.bounds
                                #If bounding polygon is larger than the minsize, draw a rectangle
                                if casc.area > ((self.width * self.height) * (float(self.minSIZE/100))):
                                                cv2.rectangle(camera_image,(int(b[0]),int(b[1])),(int(b[2]),int(b[3])),(0,0,255),thickness=2)
                                                y=round(casc.centroid.coords.xy[1][0],2)
                                                bound_center.append((x,y))
                                                bound_casc_box.append(casc)
                                                
                        if len(bound_center) == 0:
                                self.toosmall=self.toosmall+1
                                self.noMotion=True                   
                                continue
                        
                        ##############################
                        ###Grabcut Image Segmentation#
                        ##############################
                        if self.segment:
                                ####get bounding box of the current blob
                                for blob in bound_casc_box:
                                        b=blob.buffer(100).bounds
                                        rect=[int(x) for x in b]
                                        
                                        ###Format into x,y,w,h shapely is different from opencv
                                        rectf=tuple([rect[0],rect[1],rect[2]-rect[0],rect[3]-rect[1]])
                                                                                         
                                        mask = np.zeros(grabCUTimage.shape[:2],np.uint8)
                                        mask[grey_image == 0] = 0
                                        
                                        #Set the rectangle as probable background                                
                                        mask[rect[1]:rect[3],rect[0]:rect[2]] = 2
                                        
                                        #Add the background subtracted image
                                        mask[grey_image == 255] = 1
                                        bgdModel = np.zeros((1,65),np.float64)
                                        fgdModel = np.zeros((1,65),np.float64)    
                                        
                                        if not mask.sum()==0:
                                                cv2.grabCut(grabCUTimage,mask,rectf,bgdModel,fgdModel,4,cv2.GC_INIT_WITH_MASK)
                                                mask2 = np.where((mask==2)|(mask==0),0,1).astype('uint8')
                                
                                                _,contours,hierarchy = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE )
                                                for cnt in contours:
                                                        bounding_rect = cv2.boundingRect( cnt )
                                                        point1 = ( bounding_rect[0], bounding_rect[1] )
                                                        point2 = ( bounding_rect[0] + bounding_rect[2], bounding_rect[1] + bounding_rect[3] )                                
                                                        cv2.rectangle(camera_image,point1,point2,(0,255,255),thickness=2)
                                        
                        #Set flag for inside area
                        inside_area=False
                        if self.set_areacounter:
                        #test drawing center circle
                                for box in bound_center:
                                        
                                        #is the x coordinate within
                                        if area_box[2] > box[0] > area_box[0]:
                                                if area_box[3] > box[1] > area_box[1]:
                                                                inside_area= not inside_area
                                                                cv2.rectangle(camera_image,(area_box[0],area_box[1]),(area_box[2],area_box[3]),(242,221,61),thickness=1,lineType=4)
  
                        ##################################################
                        ###############Write image to file################
                        ##################################################
                        
                        if not self.makeVID == "none":
                                if self.makeVID in ("frames","both"):
                                        cv2.imwrite(self.file_destination + "/"+str(self.frame_count)+".jpg",camera_image)

                        #save the frame count and the time in video, in case user wants to check in the original
                        #create a time object, this relies on the frame_rate being correct!
                        #set seconds
                        sec = timedelta(seconds=int(self.frame_count/float(self.frame_rate)))             
                        d = datetime(1,1,1) + sec

                        for target in bound_center:
                                stampadd=(str("%d:%d:%d "  % (d.hour,d.minute, d.second)), int(self.frame_count),target[0],target[1])
                                self.stamp.append(stampadd)

                        #if inside area and counter is on, write stamp to a seperate file
                        if self.set_areacounter & inside_area:
                                for target in bound_center:
                                        stampadd=(str("%d:%d:%d "  % (d.hour,d.minute, d.second)), int(self.frame_count),target[0],target[1])
                                        self.areaC.append(stampadd)
                                
                        #Have a returned counter to balance hitRate
                        self.hitcounter=self.hitcounter+1
                        self.total_count=self.total_count+1
                        
                        #set flag to motion
                        self.noMotion=False
                                
        def videoM(self):
                
                ## Methods for video writing in the class Motion
                if self.makeVID not in ("video","both"): return("No Video Output")
                                
                normFP=os.path.normpath(self.inDEST)
                (filepath, filename)=os.path.split(normFP)
                (shortname, extension) = os.path.splitext(filename)
                (_,IDFL) = os.path.split(filepath)
                
                #we want to name the output a folder from the output destination with the named extension 
                if self.runtype == 'batch':
                        self.file_destination=os.path.join(self.fileD,IDFL)
                        self.file_destination=os.path.join(self.file_destination,shortname)
                        
                else:
                        self.file_destination=os.path.join(self.fileD,shortname)
                
                if self.fileD =='':
                        vidDEST=os.path.join(filepath, shortname,shortname +'.avi')
                else:
                        vidDEST=os.path.join(self.fileD, shortname,shortname +'.avi')
                
                print("Video output path will be %s" % (vidDEST))
                
                if not os.path.exists(self.file_destination):
                        os.makedirs(self.file_destination)
                
                #Find all jpegs
                jpgs=glob.glob(os.path.join(self.file_destination,"*.jpg"))                  
                
                #Get frame rate and size of images
                self.cap = cv2.VideoCapture(self.inDEST)
                
                        #Get frame rate if the plotwatcher setting hasn't been called
                        # not the most elegant solution, but get global frame_rate
                if not self.frameSET:
                        fr=round(self.cap.get(5))
                else:
                        fr=self.frame_rate
                
                orig_image = self.cap.read()[1]  
                
                ###Get information about camera and image
                width = np.size(orig_image, 1)
                height = np.size(orig_image, 0)
                frame_size=(width, height)                      
                
                # Define the codec and create VideoWriter object
                fourcc = self.cap.get(6)
                
                out = cv2.VideoWriter(vidDEST,int(fourcc),float(fr), frame_size)                    
                
                #split and sort the jpg names
                jpgs.sort(key=sourceM.getint)
                
                #Loop through every frame and write video
                for f in jpgs:
                        fr=cv2.imread(f)
                        out.write(fr)
                
                # Release everything if job is finished
                self.cap.release()
                out.release()
                
                #If video only, delete jpegs
                if self.makeVID == "video":
                        for f in jpgs:
                                os.remove(f)