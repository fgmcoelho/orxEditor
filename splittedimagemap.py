from editorutils import strToDoubleIntTuple

from ConfigParser import ConfigParser
from os.path import isfile

class SpriteSelection:
	def __init__(self, x, y, xSize, ySize, xParts = 1, yParts = 1):
		self.__x = x
		self.__y = y
		self.__xSize = xSize
		self.__ySize = ySize
		self.__xParts = xParts
		self.__yParts = yParts

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

class ResourceInformation:
	def __addValueToDictWithId(self, whichDict, value, identifier, maxId):
		assert identifier not in whichDict, 'Error, selection already added.'
		assert identifier < maxId, 'Error invalid state reached.'
		whichDict[identifier] = value
		return identifier

	def __getById(self, whichDict, identifier):
		if (identifier in whichDict):
			return whichDict[identifier]
		else:
			return None

	def __removeById(self, whichDict, identifier):
		if (identifier in whichDict):
			del whichDict[identifier]

	def __init__(self, path, selectionId = 0, animationId = 0):
		self.__path = path
		self.__selectionDict = {}
		self.__animationDict = {}
		self.__selectionId = selectionId
		self.__animationId = animationId

	def addSelection(self, selection, identifier = None):
		if (identifier is None):
			self.__selectionDict[self.__selectionId] = selection
			self.__selectionId += 1
			return self.__selectionId - 1
		else:
			return self.__addValueToDictWithId(self.__selectionDict, selection, identifier, self.__selectionId)

	def addAnimation(self, animation, identifier = None):
		if (identifier is None):
			self.__animationDict[self.__animationId] = animation
			self.__animationId += 1
			return self.__animationId - 1
		else:
			return self.__addValueToDictWithId(self.__animationDict, animation, identifier, self.__animationId)

	def removeSelectionById(self, identifier):
		self.__removeById(self.__selectionDict, identifier)
		for animationId, animation in self.__animationDict.iteritems():
			if (identifier in animation.getUsedSelections()):
				del self.__animationDict[animationId]

	def removeAnimationById(self, identifier):
		self.__removeById(self.__animationDict, identifier)

	def getSelectionById(self, identifier):
		return self.__getById(self.__selectionDict, identifier)

	def getAnimationById(self, identifier):
		return self.__getById(self.__animationDict, identifier)

	def getNumberOfSelections(self):
		return len(self.__selectionDict)

	def getNumberOfAnimations(self):
		return len(self.__animationDict)

	def getSelectionList(self):
		return self.__selectionDict.values()

	def getAnimationList(self):
		return self.__selectionDict.values()

	def getSelectionItems(self):
		return self.__selectionDict.items()

	def getAnimationItems(self):
		return self.__animationDict.items()

	def getSelectionId(self):
		return self.__selectionId

	def getAnimationId(self):
		return self.__animationId

	def clear(self):
		self.__selectionDict = {}
		self.__animationDict = {}

	def hasSameSelection(self, otherSelection):
		for savedSelection in self.__selectionDict.values():
			if (savedSelection.compare(otherSelection) == True):
				return True
		return False

	def countAnimationWithSelectionId(self, selectionId):
		count = 0
		for animation in self.__animationDict.values():
			if (selectionId in animation.getUsedSelections()):
				count += 1
		return count

	def getPath(self):
		return self.__path

class SplittedImageExporter:
	@staticmethod
	def save(resourceInfo):
		filename = resourceInfo.getPath()[:-4] + '.opf'
		parser = ConfigParser()
		parser.optionxform = str

		parser.add_section('General')
		parser.set('General', 'Path', resourceInfo.getPath())
		parser.set('General', 'SelectionIdNext', resourceInfo.getSelectionId())

		for id, selection in resourceInfo.getSelectionItems():
			sectionName = 'SelectionInfo' + str(id)
			parser.add_section(sectionName)
			parser.set(sectionName, 'Id', str(id))
			parser.set(sectionName, 'Position', str((selection.getX(), selection.getY())))
			parser.set(sectionName, 'Size', str((selection.getSizeX(), selection.getSizeY())))

		for id, animation in resourceInfo.getAnimationItems():
			sectionName = 'AnimationInfo' + str(id)
			parser.add_section(sectionName)
			parser.set(sectionName, 'Name', str(animation.getName()))
			parser.set(sectionName, 'Duration', str(animation.getDuration()))
			parser.set(sectionName, 'NumberOfFrames', str(len(animation.getFrames())))
			i = 0
			for frame in animation.getFrames():
				frameSectionName = 'Animation%dFrame%d' % (id, i)
				parser.add_section(frameSectionName)
				parser.set(frameSectionName, 'SelectionId', str(frame.getSelectionId()))
				if (frame.hasDuration() == True):
					parser.set(frameSectionName, 'Duration', str(frame.getDuration()))

				i += 1

		f = open(filename, 'w')
		parser.write(f)
		f.close()

		return filename

class SplittedImageImporter:
	@staticmethod
	def load(path):
		if (path[-4:] != '.opf'):
			filename = path[:-4] + '.opf'
			if (isfile(filename) == False):
				return ResourceInformation(path)
		else:
			filename = path
			assert(isfile(filename))

		parser = ConfigParser()
		parser.read(filename)

		imagePath = parser.get('General', 'Path')
		selectionId = parser.get('General', 'SelectionIdNext')
		resourceInfo = ResourceInformation(imagePath, selectionId)
		for sectionName in parser.sections():
			if sectionName.startswith('SelectionInfo'):
				x, y = strToDoubleIntTuple(parser.get(sectionName, 'Position'))
				sizeX, sizeY = strToDoubleIntTuple(parser.get(sectionName, 'Size'))
				id = int(parser.get(sectionName, 'Id'))
				selection = SpriteSelection(x, y, sizeX, sizeY)
				resourceInfo.addSelection(selection, id)

		return resourceInfo
