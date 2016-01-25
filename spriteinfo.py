class SingleIdentifiedObject(object):
	def __init__(self):
		super(SingleIdentifiedObject, self).__init__()

	def getId(self):
		return self._id

	def setId(self, newId):
		assert self._id is None, "Invalid state reached!"
		self._id = newId

class SpriteSelection(SingleIdentifiedObject):
	def __init__(self, x, y, xSize, ySize, xParts = 1, yParts = 1, identifier = None):
		super(SpriteSelection, self).__init__()
		self.__x = x
		self.__y = y
		self.__xSize = xSize
		self.__ySize = ySize
		self.__xParts = xParts
		self.__yParts = yParts
		self._id = identifier

	def compare(self, otherSelection):
		if (self.__x == otherSelection.getX() and self.__xSize == otherSelection.getSizeX() and
				self.__y == otherSelection.getY() and self.__ySize == otherSelection.getSizeY()):
			return True
		else:
			return False

	def getX(self):
		return self.__x

	def getY(self):
		return self.__y

	def getSizeX(self):
		return self.__xSize

	def getSizeY(self):
		return self.__ySize

	def getPartsX(self):
		return self.__xParts

	def getPartsY(self):
		return self.__yParts

class FrameInfo:
	def __init__(self, selectionId, duration = None):
		self.__selectionId = selectionId
		self.__duration = duration

	def getId(self):
		return self.__selectionId

	def getDuration(self):
		return self.__duration

class AnimationInfo(SingleIdentifiedObject):
	def __init__(self, name, duration, identifier = None):
		super(AnimationInfo, self).__init__()
		self.__name = name
		self.__duration = duration
		self.__framesInfo = []
		self._id = identifier

	def getName(self):
		return self.__name

	def getDuration(self):
		return self.__duration

	def getFramesInfo(self):
		return self.__framesInfo

	def addFrameInfo(self, fi):
		assert isinstance(fi, FrameInfo), "Invalid parameter received!"
		self.__framesInfo.append(fi)

	def getUsedSelections(self):
		return list(set(map(lambda x: x.getId(), self.__framesInfo)))


