#!/usr/bin/env python


# ===========================================
#			IMPORTING LIBRARIES
# ===========================================

# Files import libraries
import json # to load settings.cfg
from glob import glob # find files
import re # regex for file filtering

# System interaction libraries
import sys # startup arguments

# Multiprocessing libraries
from threading import Thread # multithread is used to reach the highest fps possible
from queue import Queue # queue frames for further processing in a dedicated thread
import time # sleep between frames to synchronize to game fps

# Custom classes
from capture import Capture # frame getter from video or game window
from ssim import BufferedSSIM # full picture recognition
from template import TemplateMatcher # small image recognition in bigger picture
from server import Server # server to accept LiveSplitOne connection
from stoppable_thread import StoppableThread # custom Thread class that have a stop() method


# ===========================================
#	    PARSING SETTINGS FILE AND ARGS
# ===========================================

settingsPath = './settings.cfg'
splitsLocationFromSettings = True

for i in range(1,len(sys.argv)):
	arg = sys.argv[i]
	if '--settings=' in arg:
		settingsPath = arg.split('=')[1]
		assert '.cfg' in settingsPath, 'Custom .cfg path need to include filename'
	elif '--splits=' in arg:
		splitsLocationFromSettings = False
		splitsLocArg = arg.split('=')[1]
	elif '--help' in arg:
		print('usage : python3 splitr.py [--settings=/path/to/settings.cfg] [--splits=/path/to/splits/folder/]')
	

with open(settingsPath) as settingsFile:
	settings = json.load(settingsFile)

if splitsLocationFromSettings:
	splitsLoc = settings['splitsPath']
else:
	splitsLoc = splitsLocArg
	
	
# ===========================================
#			 SERVER INITIALISATION
# ===========================================

if settings['server']:
	s = Server(ip=settings['ip'], port=settings['port'], useSsl=settings['useSsl'], sslLoc=settings['sslLoc'])
	# Wait here forever until LiveSplitOne connects
	s.waitForConnection()


# ===========================================
#	    CAPTURE AND SSIM MANAGER INIT
# ===========================================

capture = Capture(
	captureType=settings['source'], 
	path=settings['sourcePath'],
	gameWindow=settings['gameWindow'],
	captureFullscreen=settings['captureFullscreen'],
	monitorIndex=settings['monitorIndex']
)

# create SSIM and TemplateMatcher classes
ssimManager = BufferedSSIM(capture.getPixelsCount())
templateManager = TemplateMatcher()
# create another ones dedicated to the first split (to detect resets)
ssimManagerFS = BufferedSSIM(capture.getPixelsCount())
templateManagerFS = TemplateMatcher()


# ===========================================
#			 LOADING COMPARISONS
# ===========================================

class ComparisonLoader:
	
	def __init__(self):
		self.files = [ f
			for f in glob(splitsLoc + '/*.' + settings['splitsExt']) 
				if re.search(r'\d{3}.+\.png$', f)
		]
		self.files.sort()
		self.idx = -1
		self.count = len(self.files)
		
		assert self.count != 0, 'No ' + settings['splitsExt'] + ' file found in "' + splitsLoc + '"'
		
		if settings['verbose']:
			print('Loaded', len(self.files), 'splits.')
		
		self.loadNext()
		
		# upload the comparison to the first split managers
		if self.isTemplate:
			templateManagerFS.uploadComparison(self.comp)
		else:
			ssimManagerFS.uploadComparison(self.comp)
			
		
	def loadNext(self):
		self.idx = self.idx + 1
		if self.idx >= self.count:
			self.idx = 0 # last split reached : start over
			
		self.isTemplate = re.search(r'\d{3}=.+\.png$', self.files[self.idx]) != None
		
		self.comp = capture.loadImage(self.files[self.idx], self.isTemplate)
		
		if self.isTemplate:
			templateManager.uploadComparison(self.comp)
		else:
			ssimManager.uploadComparison(self.comp)
			
			
	# Called when last split has been reached ; next comparison will be first split (idx 0)
	def endRun(self):
		self.idx = -1
		self.loadNext()
			
			
	# First split has been detected while in run, meaning we need to compare to the 2nd split (idx 1)
	def restart(self):
		self.idx = 0
		self.loadNext()
			

comparisons = ComparisonLoader()
firstSplitIsTemplate = comparisons.isTemplate


# ===========================================
#		   	    TIMER INIT
# ===========================================

class Timer:
		
	def __init__(self):
		self.hasStarted = False

	def start(self):
		self.t0 = cv.getTickCount()
		self.hasStarted = True
		
	def hasStarted(self):
		return self.hasStarted
		
	def elapsed(self):
		return (cv.getTickCount() - self.t0) / cv.getTickFrequency()
	
	def stop(self):
		self.hasStarted = False
		
	def fps(self):
		if not hasattr(self, 'tick'):
			self.tick = cv.getTickCount()
			return 0
		else:
			fps = cv.getTickFrequency() / (cv.getTickCount() - self.tick)
			self.tick = cv.getTickCount()
			return fps
		

timer = Timer()
	

# ===========================================
#		   IMAGE EVALUATION FUNCTION
# ===========================================

# This small wrapper allow to embed frame info from capture.py up until evaluation thread
class Frame:

	def __init__(self, frame, idx, isTemplate):
		self.frame = frame
		self.idx = idx
		self.isTemplate = isTemplate
		
		

def getFrame():
	# get current frame
	frame, idx, isTemplate = capture.getFrame()
	
	frameWrapper = Frame(frame, idx, isTemplate)
	queue.put(frameWrapper)
	
	
def evaluate():
	if queue.qsize() == 0:
		return
		
	frameWrapper = queue.get()
	
	# if comparison type changed since parsing, discard this frame
	if frameWrapper.isTemplate != comparisons.isTemplate:
		return
		
	curCompIdx = comparisons.idx
	frame = frameWrapper.frame
	
	# compare it to the current comparison
	if comparisons.isTemplate:
		score = templateManager.searchFor(frame)
	else:
		score = ssimManager.ssim(frame)
	
	if settings['verbose'] and settings['ultraVerbose']:
		print('Score = ', score)
		
	# if similarity between comparison and frame is more than 80%
	if score >= 0.7:
		queue.queue.clear()
		# prevent splitting when comparing to an outdated frame
		if curCompIdx != comparisons.idx:
			return
			
		# load next comparison and send split to server
		if curCompIdx == 0:
			timer.start()
			comparisons.loadNext()
			if settings['server']:
				s.firstSplit()
		elif curCompIdx == comparisons.count - 1:
			comparisons.endRun()
			timer.stop()
			if settings['server']:
				s.split()
		else:
			comparisons.loadNext()
			if settings['server']:
				s.split()
			
		if settings['verbose']:
			if curCompIdx == 0:
				print('First split! (%d/%d)' % (curCompIdx + 1, comparisons.count))
			elif curCompIdx == comparisons.count - 1:
				print('Last split ! %.3fs after first split.' % timer.elapsed())
			else:
				print('Split ! (%d/%d) %.3fs after first split.' % (curCompIdx + 1, comparisons.count, timer.elapsed()))
	
	# wait for at least 500ms before searching for a reset
	elif timer.hasStarted and timer.elapsed() > 0.5:
		comp = capture.imgSsim if comparisons.isTemplate else frame
		if firstSplitIsTemplate:
			fs = templateManagerFS.searchFor(comp)
		else:
			fs = ssimManagerFS.ssim(comp)
		
		if fs >= 0.7:
			queue.queue.clear()
			
			# prevent resets when comparing to an outdated frame
			if curCompIdx != comparisons.idx:
				return
				
			if settings['server']:
				s.firstSplit()
				
			if settings['verbose']:
				print('Restart ! %.3fs after first split.' % timer.elapsed())
			
			comparisons.restart()
			timer.start()	


# ===========================================
#		   FRAME BY FRAME COMPARISON
# ===========================================

queue = Queue()

# prepare the evaluation thread
evaluateThread = StoppableThread(evaluate)

if settings['verbose']:
	print('Starting acquisition.')

while capture.shouldContinue():
	# do not start too many threads
	while queue.qsize() >= 75:
		time.sleep(1e-6)
	
	# start a thread that will capture a frame
	t = Thread(target=getFrame)
	t.start()
	
	# limit fps here
	time.sleep(1/1000)

# wait for the 'evaluate' thread to finish
evaluateThread.stop()

if settings['verbose']:
	print('Done.')


