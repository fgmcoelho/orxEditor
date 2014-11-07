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

	@staticmethod
	def copy(resource):
		pass

	def __init__(self, path):
		self.__path = path
		self.__selectionDict = {}

	def addSelection(self, selection):
		self.__selectionDict[self.__selectionId] = selection
		self.__selectionId += 1

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

class SplittedImageMap:

	def __init__(self, baseImagePath = '', numberOfImages = 0, divisions = (0, 0), size = (0, 0)):
		self.__baseImagePath = baseImagePath
		self.__numberOfImages = numberOfImages
		self.__divisions = divisions
		self.__size = size
		self.__imagesList = []
		self.__coordsList = []

	def __basicAssertions(self):
		assert (self.__baseImagePath != '' and self.__numberOfImages != 0 and len(self.__divisions) == 2 and
			self.__divisions[0] != 0 and self.__divisions[1] != 0 and len(self.__size) == 2 and self.__size[0] != 0
			and self.__size[1] != 0)

	def __loadImages(self):

		if (self.__imagesList != []):
			return

		else:
			self.__basicAssertions()

		i = 0

		width = self.__size[0] / self.__divisions[0]
		height = self.__size[1] / self.__divisions[1]

		xList = range(0, self.__size[0], width)
		yList = range(0, self.__size[1], height)
		yList.reverse()

		self.__baseImage = Image(source = self.__baseImagePath)
		coordI = 0

		for y in yList:
			coordJ = 0
			for x in xList:
				newTexture = self.__baseImage.texture.get_region(x, y, width, height)
				self.__imagesList.append(
					Image(texture = newTexture,	size = (width, height), size_hint = (None, None))
				)
				self.__coordsList.append((coordI, coordJ))

				i += 1
				coordJ += 1
				if (i == self.__numberOfImages):
					return
			coordI += 1

		assert (i == self.numberOfImages)


	def exportToOpf(self, filename):

		self.__basicAssertions()

		parser = ConfigParser()
		sectionName = 'SplittedImage'
		parser.add_section(sectionName)
		parser.set(sectionName, 'path', self.__baseImagePath)
		parser.set(sectionName, 'numberofimages', self.__numberOfImages)
		parser.set(sectionName, 'divisions', str(self.__divisions))
		parser.set(sectionName, 'size', str(self.__size))

		f = open(filename, 'w')
		parser.write(f)

	def importFromOpf(self, filename):
		parser = ConfigParser()
		parser.read(filename)

		sectionName = 'SplittedImage'
		self.__baseImagePath = str(parser.get(sectionName, 'path'))
		self.__numberOfImages = int(parser.get(sectionName, 'numberofimages'))
		self.__divisions = strToDoubleIntTuple(parser.get(sectionName, 'divisions'))
		self.__size = strToDoubleIntTuple(parser.get(sectionName, 'size'))

		self.__basicAssertions()

	def getImagesList(self):
		if (self.__imagesList == []):
			self.__loadImages()

		return self.__imagesList

	def getCoordsList(self):
		if (self.__imagesList == []):
			self.__loadImages()
		return self.__coordsList

	def getBaseImagePath(self):
		return self.__baseImagePath

	def getSize(self):
		return self.__size

class SplittedImageExporter:
	@staticmethod
	def save(resourceInfo):
		filename = resourceInfo.getPath()[:-4] + '.opf'
		parser = ConfigParser()
		parser.optionxform = str

		parser.set('General', 'Amount', str(resourceInfo.getNumberOfSelections()))
		#parser.set('General', 'KeepOriginal', '')

		i = 0
		for selection in resourceInfo.getSelectionList():
			sectionName = 'SelectionInfo' + str(i)
			parser.set(sectionName, 'Position', str((selection.getX(), selection.getY())))
			parser.set(sectionName, 'Size', str((selection.getSizeX(), selection.getSizeY())))
			i += 1

		f = open(filename, 'w')
		parser.write(f)
		f.close()

		return filename

class SplittedImageImport:
	@staticmethod
	def load(path):
		if (path[-4:] != '.opf'):
			filename = path[:-4] + '.opf'
		else:
			filename = path

		resourceInfo = ResourceInformation()
		parser = ConfigParser()
		parser.read(filename)
		numberOfImages = int(parser.get('General', 'Amount'))
		for i in range(numberOfImages):
			sectionName = 'SelectionInfo' + str(i)
			x, y = strToDoubleIntTuple(parser.get(sectionName, 'Position'))
			sizeX, sizeY = strToDoubleIntTuple(parser.get(sectionName, 'Size'))
			selection = SpriteSelection(x, y, sizeX, sizeY)
			resourceInfo.addSelection(selection)

		return resourceInfo

