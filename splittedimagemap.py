
from ConfigParser import ConfigParser
from editorutils import strToDoubleElementTuple

class SplittedImageMap:
	
	def __init__(self, baseImagePath = '', numberOfImages = 0, divisions = (0, 0), size = (0, 0)):
		self.__baseImagePath = baseImagePath
		self.__numberOfImages = numberOfImages
		self.__divisions = divisions
		self.__size = size
		self.__imagesList = []

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

		for y in yList:
			for x in xList:
				
				newTexture = self.__baseImage.texture.get_region(x, y, width, height)
				self.__imagesList.append(
					Image(texture = newTexture, on_touch_up = self.__handleTouchOnSplittedImage,
					size = (width, height), size_hint = (None, None))
				)
				
				i += 1
				if (i == self.__numberOfImages):
					return

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
		self.__divisions = strToDoubleElementTuple(parser.get(sectionName, 'divisions'))
		self.__size = strToDoubleElementTuple(parser.get(sectionName, 'size'))
		
		self.__basicAssertions()

	def getImagesList(self):
		if (self.__imagesList == []):
			self.__loadImages()

		return self.__imagesList
