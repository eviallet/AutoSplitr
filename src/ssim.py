#!/usr/bin/env python


# ===========================================
#			IMPORTING LIBRARIES
# ===========================================

import cv2 as cv
import numpy as np


# ===========================================
#		STRUCTURAL SIMILARITY CLASS
# ===========================================

class BufferedSSIM:

	def __init__(self, pixelsCount):
		self.pixelsCount = pixelsCount
		
	
	def uploadComparison(self, img):
		# float conversion
		self.i1 = img.astype(np.float32)
		self.i1u = cv.UMat(self.i1)
		# ux = gaussian_filter(im1)
		self.ux = cv.GaussianBlur(self.i1u, (11, 11), 1.5)
		# uxx = gaussian_filter(im1 * im1)
		self.uxx = cv.pow(self.i1u, 2)
		self.uxx = cv.GaussianBlur(self.uxx, (11, 11), 1.5)
		# vx = cov_norm * (uxx - ux * ux)
		self.ux2 = cv.multiply(self.ux, self.ux)
		self.vx = cv.subtract(self.uxx, self.ux2)
		self.vx = cv.multiply(self.vx, 1.008333333)
		

	def ssim(self, img):
		c1 = 6.5025
		c2 = 58.5225
		# float conversion
		self.i2 = img.astype(np.float32)
		self.i2u = cv.UMat(self.i2)
    	# uy = gaussian_filter(im2)
		self.uy = cv.GaussianBlur(self.i2u, (11, 11), 1.5)
    	# uyy = gaussian_filter(im2 * im2)
		self.uyy = cv.pow(self.i2u, 2)
		self.uyy = cv.GaussianBlur(self.uyy, (11, 11), 1.5)
    	# uxy = gaussian_filter(im1 * im2)
		self.uxy = cv.multiply(self.i1u, self.i2u)
		self.uxy = cv.GaussianBlur(self.uxy, (11, 11), 1.5)
		# vy = cov_norm * (uyy - uy * uy)
		self.uy2 = cv.multiply(self.uy, self.uy)
		self.vy = cv.subtract(self.uyy, self.uy2)
		self.vy = cv.multiply(self.vy, 1.008333333)
    	# vxy = cov_norm * (uxy - ux * uy)
		self.ux_uy = cv.multiply(self.ux, self.uy)
		self.vxy = cv.subtract(self.uxy, self.ux_uy)
		self.vxy = cv.multiply(self.vxy, 1.008333333)		
    	# a1 = 2 * ux * uy + C1
		self.a1 = cv.multiply(self.ux_uy, 2)
		self.a1 = cv.add(self.a1, c1)
		# a2 = 2 * vxy + C2
		self.a2 = cv.multiply(self.vxy, 2)
		self.a2 = cv.add(self.a2, c2)
		# b1 = ux ** 2 + uy ** 2 + C1
		self.b1 = cv.addWeighted(self.ux2, 1, self.uy2, 1, c1)	
		# b2 = vx + vy + C2
		self.b2 = cv.addWeighted(self.vx, 1, self.vy, 1, c2)	
    	# d = b1 * b2
		self.d = cv.multiply(self.b1, self.b2)
		# s = (a1 * a2) / d
		self.s = cv.multiply(self.a1, self.a2)
		self.s = cv.divide(self.s, self.d)
		
		s_sum = cv.sumElems(self.s)[0]
		
		return s_sum/self.pixelsCount


