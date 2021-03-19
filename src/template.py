#!/usr/bin/env python

# ===========================================
#			IMPORTING LIBRARIES
# ===========================================

import cv2 as cv


# ===========================================
#		  TEMPLATE SEARCHING CLASS
# ===========================================

class TemplateMatcher:
	
	def uploadComparison(self, comparison):
		self.comparison = comparison
		
	def searchFor(self, img):
		self.smap = cv.matchTemplate(img, self.comparison, cv.TM_SQDIFF_NORMED)
		max_val, min_val, max_loc, min_loc = cv.minMaxLoc(self.smap)
		return 1-max_val

