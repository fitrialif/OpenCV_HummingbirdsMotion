import sys
import sourceM
import argparse

Usage = """

Welcome to MotionMeerkat!

Automated capture of motion frames from a video file.

For help, see the wiki: https://github.com/bw4sz/OpenCV_HummingbirdsMotion/wiki

Default values for parameters are in parenthesis. To select default hit enter.

Affirmative answers to questions are y, negative answers n

Please do not use quotes for any responses. 

"""

def arguments(self):
        #If there were system argument
                self.parser = argparse.ArgumentParser()

                #Read in system arguments if they exist
                if len(sys.argv)< 2:
                                print Usage
                else:
                                self.parser.add_argument("--runtype", help="Batch or single file",default='file')
                                self.parser.add_argument("--batchpool", help="run directory of videos",type=str)
                                self.parser.add_argument("--inDEST", help="path of single video",type=str,default='C:/Program Files (x86)/MotionMeerkat/PlotwatcherTest.tlv')
                                self.parser.add_argument("--fileD", help="output directory",default="C:/MotionMeerkat")
                                self.parser.add_argument("--adapt", help="Adaptive background averaging",action='store_true',default=False)
                                self.parser.add_argument("--accAvg", help="Fixed background averaging rate",default=0.35,type=float)
                                self.parser.add_argument("--frameHIT", help="expected percentage of motion frames",default=0.05,type=float)
                                self.parser.add_argument("--threshT", help="Threshold of movement",default=30,type=int)
                                self.parser.add_argument("--minSIZE", help="Minimum size of contour",default=0.1,type=float)
                                self.parser.add_argument("--burnin", help="Delay time",default=0,type=int)
                                self.parser.add_argument("--scan", help="Scan one of every X frames for motion",default=0,type=int)
                                self.parser.add_argument("--frameSET", help="Set frame_rate?",action='store_true',default=False)
                                self.parser.add_argument("--plotwatcher", help="Camera was a plotwatcher?",action="store_true",default=False)
                                self.parser.add_argument("--frame_rate", help="frames per second",default=1)
				self.parser.add_argument("--moglearning", help="Speed of MOG background detector, lowering values are more sensitive to movement",default=0.1,type=float)                                
                                self.parser.add_argument("--subMethod", help="Accumulated Averaging [Acc] or Mixture of Gaussian [MOG] background method",default='MOG',type=str)                                
                                self.parser.add_argument("--mogvariance", help="Variance in MOG to select background",default=16,type=int)                                
                                self.parser.add_argument("--set_ROI", help="Set region of interest?",action='store_true',default=False)
				self.parser.add_argument("--windy", help="Enable wind correction",action='store_true',default=False)
				self.parser.add_argument("--windy_min", help="How many minutes of continious movement should be ignored?",default='3',type=int)                                
                                self.parser.add_argument("--ROI_include", help="include or exclude?",default="exclude")
                                self.parser.add_argument("--set_areacounter", help="Set region to count area",action="store_true",default=False)
                                self.parser.add_argument("--todraw", help="Draw red boxes to highlight motion' ?",action="store_true",default=False)				
                                self.parser.add_argument("--makeVID", help="Output images as 'frames','video','both', 'none' ?",default='frames',type=str)
                                self.args = self.parser.parse_args(namespace=self)
				if not self.runtype=="pictures":
						self.pictures=False
				self.segment = False
                                print "\n"
                                print "\n"
                    
                if(len(sys.argv)< 2):
                                #Batch or single file
                                self.runtype=raw_input("'batch' run, single video 'file' or folder of ordered 'pictures'? (file):\n")   
                                if not self.runtype: self.runtype="file"
                                
                                if(self.runtype=="file"):
                                                self.inDEST=sourceM.ask_file()
                                                self.pictures=False
                                if(self.runtype=="batch"):
                                                self.batchpool=raw_input("Enter folder containing videos:\n")
                                                self.pictures=False
                                if(self.runtype=="pictures"):
                                                self.inDEST=raw_input("Enter folder containing pictures\n Please note that filenames need to be chronological order \n")                             
                                                self.pictures=True
                                #Destination of file
                                self.fileD=raw_input("File Destination Folder (C:\MotionMeerkat):\n")   
                                if not self.fileD: self.fileD = str("C:\MotionMeerkat")
                
                                #thresholding, a way of differentiating the background from movement, higher values (0-255) disregard more motion, lower values make the model more sensitive to motion
                                self.threshT=raw_input("Threshold for movement tolerance\nRanging from 0 [include any movement] to 255 [include no movement]\nSlow moving animals, like fish, need low thresholds [10].\nFast moving animals, like birds, can have higher thresholds [70] (30):\n")
                                if not self.threshT: self.threshT = 30
                                else: self.threshT=float(self.threshT)
                
                                #minimum size of contour object
                                self.minSIZE=raw_input("Minimum motion contour size\nExpressed as the proportion of the screen.\nFor example, the default (0.3) would ignore objects less than 0.3% of the screen size (0.3):\n")
                                if not self.minSIZE: self.minSIZE = 0.3
                                else: self.minSIZE=float(self.minSIZE)
                
                                self.advanced= 'y'==raw_input("Set advanced options? (n) :\n")
                                
                                if self.advanced:
                                                #background method
                                                self.subMethod=raw_input("\nAccumulated Averaging [Acc] or Mixture of Gaussian [MOG] background method? \nAcc is faster, MOG is more accurate. (MOG):\n")
                                                if not self.subMethod: self.subMethod="MOG"
                                                    
                                                if self.subMethod=="Acc":
								
								#Sensitivity to movement
								self.accAvg=sourceM.ask_acc()
								if not self.accAvg: self.accAvg=0.35
								
                                                                #Should accAVG be adapted every 10minutes based on an estimated hitrate
                                                                self.adapt= 'y'==raw_input("Adapt the motion sensitivity based on expected frequency of visits? (n) :\n")      
                                                                
                                                                if self.adapt:
                                                                    
                                                                                #Hitrate, the expected % of frames per 10 minutes - this is a helpful adaptive setting that helps tune the model, this will be multiplied the frame_rate
                                                                                self.frameHIT=raw_input("Expected percentage of frames with motion (0.02, i.e 2% of frames returned):\n")
                                                                                if not self.frameHIT: self.frameHIT = 0.02
                                                                                else: self.frameHIT=float(self.frameHIT)

                                                #Still need to set moglearning to pass to argument, even if it isn't used.  
                                                self.moglearning = 0.1
                                                self.mogvariance = 16
                                                
                                                if self.subMethod=="MOG":
                                                                self.moglearning=raw_input("Senitivity to background movement, ranging from 0 [very sensitive] to 1. (0.1):\n")
                                                                if not self.moglearning: self.learning = 0.1
								self.moglearning=float(self.moglearning)
								
                                                                self.mogvariance=raw_input("Variance in background threshold (16):\n")
                                                                if not self.mogvariance: self.mogvariance = 16
                                                                
                                                                #Turn off adaptation, not ready V1.8.5
                                                                self.adapt=False
                                                                                                             					
						#Skip initial frames of video, in case of camera setup and shake.       
						self.windy='y'== raw_input("Enable wind correction? (n):\n")
						if not self.windy: self.windy = False
						else: 
								self.windy_min= raw_input("If more than 90% of consecutive frames in X minutes are returned, delete frames. (3):\n")
								if not self.windy_min:
										self.windy_min=float(3.0)
								else:
										self.windy_min=float(self.windy_min)
								
						#set ROI
						self.set_ROI= "y" == raw_input("Exclude a portion of the image? (n) :\n")
				
						if self.set_ROI:
								self.ROI_include=raw_input("Subregion of interest to 'include' or 'exclude'? (exclude):\n")
						else: self.ROI_include='exclude'                                            
						#Decrease frame rate, downsample
                                                self.scan= raw_input("Scan one of every X frames (0):\n")
                                                if not self.scan: self.scan = 0
                                                else: self.scan=int(self.scan)
						
						#Skip initial frames of video, in case of camera setup and shake.       
						self.burnin= raw_input("Burn in, skip initial minutes of video (0):\n")
						if not self.burnin: self.burnin = 0
						else: self.burnin=float(self.burnin)

						#There are specific conditions for the plotwatcher pro, because the frame_rate is off, turn this to a boolean       
						self.plotwatcher='y'==raw_input("Does this video come from a plotwatcher camera? (n) :\n")
						if not self.plotwatcher: self.plotwatcher = False  
						
						#Draw boxes to highlight motion
						self.todraw='y'==raw_input("Draw red boxes to highlight motion? (n) :\n")
						if not self.todraw: self.todraw = False 
						
						#Manually set framerate?
                                                self.frameSET= "y" == raw_input("Set frame rate in frames per second? (n):\n")
                                        
                                                #Set frame rate.
                                                if self.frameSET:
                                                                self.frame_rate = raw_input("frames per second:\n")
                                                else: self.frame_rate=0
						
                            			#Create area counter by highlighting a section of frame
                                                self.set_areacounter='y'==raw_input("Highlight region for area count? (n) \n")
                                                if not self.set_areacounter: self.set_areacounter=False
                            
                                                #make video by stringing the jpgs back into an avi
                                                self.makeVID=raw_input("Write output as 'video', 'frames','both','none'? (frames):\n")
                                                if not self.makeVID:self.makeVID="frames"
                            
                                else:
                                                #Set defaults that weren't specified.
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
						self.accAvg = 0.35
                                                self.subMethod="MOG"
                                                self.moglearning = 0.1
                                                self.mogvariance = 16
                                                self.pictures = False
                                                self.windy = False
						self.todraw=False
						
