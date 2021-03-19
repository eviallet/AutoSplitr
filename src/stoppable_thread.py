#!/usr/bin/env python

# ===========================================
#			IMPORTING LIBRARIES
# ===========================================

from threading import Thread


# ===========================================
#		   STOPPABLE THREAD CLASS
# ===========================================

class StoppableThread:

	def __init__(self, target):
		self.target = target
		self.shouldRun = True
		self.thread = Thread(target=self.run)
		self.thread.start()
		
	def run(self):
		while self.shouldRun:
			self.target()
	
	def stop(self):
		self.shouldRun = False
		self.thread.join()
