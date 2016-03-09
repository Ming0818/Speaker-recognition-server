from collections import Counter
import numpy as np

class EmitStack(object):
	"""docstring for EmitStack"""
	def __init__(self, emitHeight):
		super(EmitStack, self).__init__()
		self.emitHeight = emitHeight
		self.emitCounter = 0
		self.emitArr = []

	def append(self, item):
		self.emitArr.append(item)
		self.emitCounter += 1

	def extend(self, arr, length):
		self.emitArr.extend(arr)
		self.emitCounter += length

	def canEmit(self, frameRate):
	 	return self.emitCounter >= self.emitHeight * frameRate

	def emitLabel(self):
		emitLabel = np.array(self.emitArr)
		self.emitCounter = 0
		self.emitArr = []
		
		return emitLabel
		

		