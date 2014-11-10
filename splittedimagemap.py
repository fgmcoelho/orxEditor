from kivy.uix.image import Image

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

	def __init__(self, path):
		self.__path = path
		self.__selectionDict = {}
		self.__selectionId = 0

	def addSelection(self, selection):
		self.__selectionDict[self.__selectionId] = selection
		self.__selectionId += 1
		return self.__selectionId - 1

	def removeSelectionById(self, identifier):
		if (identifier in self.__selectionDict):
			del self.__selectionDict[identifier]

	def getSelectionById(self, identifier):
		if (identifier in self.__selectionDict):
			return self.__selectionDict[identifier]
		else:
			return None

	def getNumberOfSelections(self):
		return len(self.__selectionDict)

	def clear(self):
		self.__selectionDict = {}

	def hasSame(self, otherSelection):
		for savedSelection in self.__selectionDict.values():
			if (savedSelection.compare(otherSelection) == True):
				return True

		return False

	def getPath(self):
		return self.__path

	def getSelectionList(self):
		return self.__selectionDict.values()

	def getSelectionItems(self):
		return self.__selectionDict.items()

class SplittedImageExporter:
	@staticmethod
	def save(resourceInfo):
		filename = resourceInfo.getPath()[:-4] + '.opf'
		parser = ConfigParser()
		parser.optionxform = str

		parser.add_section('General')
		parser.set('General', 'Amount', str(resourceInfo.getNumberOfSelections()))
		#parser.set('General', 'KeepOriginal', '')
		parser.set('General', 'Path', resourceInfo.getPath())

		i = 0
		for selection in resourceInfo.getSelectionList():
			sectionName = 'SelectionInfo' + str(i)
			parser.add_section(sectionName)
			parser.set(sectionName, 'Position', str((selection.getX(), selection.getY())))
			parser.set(sectionName, 'Size', str((selection.getSizeX(), selection.getSizeY())))
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
		numberOfImages = int(parser.get('General', 'Amount'))
		resourceInfo = ResourceInformation(parser.get('General', 'Path'))
		for i in range(numberOfImages):
			sectionName = 'SelectionInfo' + str(i)
			x, y = strToDoubleIntTuple(parser.get(sectionName, 'Position'))
			sizeX, sizeY = strToDoubleIntTuple(parser.get(sectionName, 'Size'))
			selection = SpriteSelection(x, y, sizeX, sizeY)
			resourceInfo.addSelection(selection)

		return resourceInfo

