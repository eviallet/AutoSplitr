#!/usr/bin/env python


# ===========================================
#			IMPORTING LIBRARIES
# ===========================================

# Image processing libraries
import cv2 as cv # opencv
from mss import mss # screen capture
import numpy as np # images to matrixes for opencv

# Unix window management (to find game window position and size)
# https://stackoverflow.com/a/16703307/ helped a lot
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Gtk, Wnck # window manager 


# ===========================================
#			  CLASS DEFINITION
# ===========================================

class Capture:
	
	
	#### Constructor ####
	def __init__(self, captureType, 
		path=None, gameWindow=None, captureFullscreen=True, 
		monitorIndex=0, ratioSsim=0.02, ratioTemplate=0.3):
	
		self.captureType = captureType
		self.ratioSsim = ratioSsim
		self.ratioTemplate = ratioTemplate
		self.isTemplate = False
		self.curFrame = 0
		
		if self.captureType == 'Game':
			assert gameWindow != None, 'Argument "gameWindow" is required when using "Game" as source.'
			self.initGameCapture(gameWindow, monitorIndex, captureFullscreen)
			
		elif self.captureType == 'Video':
			assert path != None, 'Argument "path" is required when using "Video" as source.'
			self.initVideoCapture(path)
			
		else:
			print('Invalid source choice. Should be "Game" or "Video".')
			exit()
			
			
	
	# Destructor
	def __del__(self):
		
		if self.captureType == 'Video':
			self.video.release()
	
	
	#### Find game window location and size ####
	def initGameCapture(self, gameWindow, monitorIndex, captureFullscreen):
	
		self.winCapture = mss()
		
		# find default monitor resolution
		if captureFullscreen:
			window = Gtk.Window()
			screen = window.get_screen()
				
			self.width = screen.get_monitor_geometry(monitorIndex).width
			self.height = screen.get_monitor_geometry(monitorIndex).height
			
			self.winGame = {
				'top': screen.get_monitor_geometry(monitorIndex).y, 
				'left': screen.get_monitor_geometry(monitorIndex).x, 
				'width': self.width, 
				'height': self.height
			}

			self.reducedSizeSsim = (
				int(self.width * self.ratioSsim), 
				int(self.height * self.ratioSsim)
			)
			self.reducedSizeTemplate = (
				int(self.width * self.ratioTemplate), 
				int(self.height * self.ratioTemplate)
			)
			
		# try to find a window names after settings.gameWindow
		else:
			Gtk.init([]); screen = Wnck.Screen.get(monitorIndex); screen.force_update()

			winGeometry = 0

			for window in screen.get_windows() :
				if window.get_name() == gameWindow :
					winGeometry = window.get_geometry()
					break

			window = None; screen = None; Wnck.shutdown()
			assert winGeometry != 0, gameWindow + ' not found; exiting...'
			
			self.width = winGeometry.widthp
			self.height = winGeometry.heightp
			
			self.winGame = {
				'top': winGeometry.yp, 
				'left': winGeometry.xp, 
				'width': self.width, 
				'height': self.height
			}
			
			self.reducedSizeSsim = (
				int(winGeometry.widthp * self.ratioSsim), 
				int(winGeometry.heightp * self.ratioSsim)
			)
			self.reducedSizeTemplate = (
				int(winGeometry.widthp * self.ratioTemplate), 
				int(winGeometry.heightp * self.ratioTemplate)
			)
	
	
	
	#### Loads video path into cv.VideoCapture ####
	def initVideoCapture(self, path):
	
		self.video = cv.VideoCapture(path)
		
		self.width = self.video.get(cv.CAP_PROP_FRAME_WIDTH)
		self.height = self.video.get(cv.CAP_PROP_FRAME_HEIGHT)
		self.frames = int(self.video.get(cv.CAP_PROP_FRAME_COUNT))
		self.reducedSizeSsim = (int(self.width * self.ratioSsim), int(self.height * self.ratioSsim))
		self.reducedSizeTemplate = (int(self.width * self.ratioTemplate), int(self.height * self.ratioTemplate))
			
			
	
	#### Load image with current capture parameters ####
	def loadImage(self, path, isTemplate):
	
		self.isTemplate = isTemplate
		img = cv.imread(path,cv.IMREAD_GRAYSCALE)
		img = np.array(img)
		
		# Keep template aspect ratio and relative size with frame to compare
		if self.isTemplate:
			reducedSizeTmp = (int(img.shape[1] * self.ratioTemplate), int(img.shape[0] * self.ratioTemplate))
			img = cv.resize(img, reducedSizeTmp, cv.INTER_CUBIC)
		else:
			img = cv.resize(img, self.reducedSizeSsim, cv.INTER_CUBIC)
		
		return img


	
	#### Get source next frame ####
	def getFrame(self):
	
		self.curFrame = self.curFrame + 1
	
		if self.captureType == 'Game':
			self.frame = self.winCapture.grab(self.winGame)
			
		elif self.captureType == 'Video':
			success, self.frame = self.video.read()
		
		# Try to be consistent with variables types and sizes upon calls to avoid dynamic allocations
		self.arr = np.array(self.frame)
		self.ars = cv.cvtColor(self.arr, cv.COLOR_BGR2GRAY);
		self.imgSsim = cv.resize(self.ars, self.reducedSizeSsim, cv.INTER_CUBIC)
		
		if self.isTemplate:
			self.img = cv.resize(self.ars, self.reducedSizeTemplate, cv.INTER_CUBIC)
		else:
			self.img = self.imgSsim 
		
		return self.img, self.curFrame, self.isTemplate
		
		
		
	#### Should continue to capture next frame ? ####
	def shouldContinue(self):
		if self.captureType == 'Game':
			return True
			
		elif self.captureType == 'Video':
			return self.curFrame < self.getCount()
		
	
	
	#### Get source length ####
	def getCount(self):
		if self.captureType == 'Video':
			return self.frames
				
			
	
	#### Get pixel count ####
	def getPixelsCount(self):
		
		return self.reducedSizeSsim[0] * self.reducedSizeSsim[1]
			
			
			
	
