from collections import Counter

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

	def canEmit(self):
	 	return self.emitCounter >= self.emitHeight

	def emitLabel(self):
		emitLabel = Counter(self.emitArr).most_common(1)[0][0]
		self.emitCounter = 0
		self.emitArr = []
		print emitLabel
		return emitLabel
		

		