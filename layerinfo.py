from singleton import Singleton

class LayerRegister:
	def __init__(self, name, priority):
		self.__name = name
		self.__priority = priority

	def setPriority(self, newPriority):
		self.__priority = newPriority

	def getPriority(self):
		return self.__priority

	def getName(self):
		return self.__name

@Singleton
class LayerGuardian:
	
	def __startLayers(self):
		self.__defaultLayer = LayerRegister('default', 0)
		self.__layersDict = { 0 : self.__defaultLayer }
		for i in range(1, 16):
			self.__layersDict[i] = None

		self.__highestPriority = 0

		assert(len(self.__layersDict) == 16)

	def __init__(self):
		self.__startLayers()

	def __getIndex(self, layerName):
		for i in range(self.__highestPriority + 1):
			if(self.__layersDict[i].getName() == layerName):
				return i

		raise Exception('Fatal error on layer manager.')

	def addNewLayer(self, newLayer):
		self.__highestPriority += 1
		self.__layersDict[self.__highestPriority] = LayerRegister(newLayer, self.__highestPriority)

	def decreasePriority(self, layerName):
		i = self.__getIndex(layerName)
		if (i == 0):
			return
		else:
			swap = self.__layersDict[i-1]
			self.__layersDict[i-1] = self.__layersDict[i]
			self.__layersDict[i] = swap
			self.__layersDict[i-1].setPriority(i-1)
			self.__layersDict[i].setPriority(i)

	def increasePriority(self, layerName):
		i = self.__getIndex(layerName)
		if (i == self.__highestPriority):
			return
		else:
			swap = self.__layersDict[i+1]
			self.__layersDict[i+1] = self.__layersDict[i]
			self.__layersDict[i] = swap
			self.__layersDict[i].setPriority(i)
			self.__layersDict[i+1].setPriority(i+1)
	
	def deleteLayerByName(self, layerName):
		i = self.__getIndex(layerName)
		while (self.__layersDict[i] != None):
			self.__layersDict[i] = self.__layersDict[i + 1]
			if (self.__layersDict[i] is not None):
				self.__layersDict[i].setPriority(i)
			i += 1

		self.__highestPriority -= 1

	def getLayerList(self):
		l = []
		formerKey = -1
		for key in self.__layersDict.keys():
			if (self.__layersDict[key] is not None):
				l.append(self.__layersDict[key])
				assert key == formerKey + 1
				formerKey = key
			else:
				break

		return l

	def getNameToPriorityDict(self):
		d = {}
		for key in self.__layersDict:
			if (self.__layersDict[key] is not None):
				d[self.__layersDict[key].getName()] = self.__layersDict[key].getPriority()
			else:
				break
		return d
	
	def reset(self):
		self.__startLayers()

