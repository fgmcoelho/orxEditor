from editorutils import strToDoubleIntTuple
from spriteinfo import FrameInfo, AnimationInfo, SpriteSelection

from ConfigParser import ConfigParser
from os.path import isfile

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
		self.__animationInfoDict = {}
		self.__selectionId = selectionId
		self.__animationInfoId = animationId

	def addSelection(self, selection):
		identifier = selection.getId()
		if (identifier is None):
			self.__selectionDict[self.__selectionId] = selection
			selection.setId(self.__selectionId)
			self.__selectionId += 1
			return selection.getId()
		else:
			return self.__addValueToDictWithId(self.__selectionDict, selection, identifier, self.__selectionId)

	def addAnimationInfo(self, animationInfo):
		identifier = animationInfo.getId()
		if (identifier is None):
			self.__animationInfoDict[self.__animationInfoId] = animationInfo
			animationInfo.setId(self.__animationInfoId)
			self.__animationInfoId += 1
			return self.__animationInfoId - 1
		else:
			return self.__addValueToDictWithId(self.__animationInfoDict, animationInfo, identifier,
				self.__animationInfoId)

	def removeSelectionById(self, identifier):
		self.__removeById(self.__selectionDict, identifier)
		toRemove = []
		for animationId, animationInfo in self.__animationInfoDict.iteritems():
			if (identifier in animationInfo.getUsedSelections()):
				toRemove.append(animationId)

		for key in toRemove:
			del self.__animationInfoDict[key]

	def removeAnimationInfoById(self, identifier):
		self.__removeById(self.__animationInfoDict, identifier)

	def getSelectionById(self, identifier):
		return self.__getById(self.__selectionDict, identifier)

	def getAnimationInfoById(self, identifier):
		return self.__getById(self.__animationInfoDict, identifier)

	def getNumberOfSelections(self):
		return len(self.__selectionDict)

	def getNumberOfAnimationInfos(self):
		return len(self.__animationInfoDict)

	def getSelectionList(self):
		return self.__selectionDict.values()

	def getAnimationInfoList(self):
		return self.__selectionDict.values()

	def getSelectionItems(self):
		return self.__selectionDict.items()

	def getAnimationInfoItems(self):
		return self.__animationInfoDict.items()

	def getSelectionId(self):
		return self.__selectionId

	def getAnimationInfoId(self):
		return self.__animationInfoId

	def clear(self):
		self.__selectionDict = {}
		self.__animationInfoDict = {}

	def hasSameSelection(self, otherSelection):
		for savedSelection in self.__selectionDict.values():
			if (savedSelection.compare(otherSelection) == True):
				return True
		return False

	def countAnimationInfoWithSelectionId(self, selectionId):
		count = 0
		for animationInfo in self.__animationInfoDict.values():
			if (selectionId in animationInfo.getUsedSelections()):
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
		parser.set('General', 'AnimationInfoIdNext', resourceInfo.getAnimationInfoId())

		for identifier, selection in resourceInfo.getSelectionItems():
			sectionName = 'SelectionInfo' + str(identifier)
			parser.add_section(sectionName)
			parser.set(sectionName, 'Id', str(identifier))
			parser.set(sectionName, 'Position', str((selection.getX(), selection.getY())))
			parser.set(sectionName, 'Size', str((selection.getSizeX(), selection.getSizeY())))

		for identifier, animationInfo in resourceInfo.getAnimationInfoItems():
			sectionName = 'AnimationInfo' + str(identifier)
			parser.add_section(sectionName)
			parser.set(sectionName, 'Id', str(animationInfo.getId()))
			parser.set(sectionName, 'Name', str(animationInfo.getName()))
			parser.set(sectionName, 'Duration', str(animationInfo.getDuration()))
			parser.set(sectionName, 'NumberOfFrames', str(len(animationInfo.getFramesInfo())))
			i = 0
			for frameInfo in animationInfo.getFramesInfo():
				frameSectionName = 'Animation%dFrame%d' % (identifier, i)
				parser.add_section(frameSectionName)
				parser.set(frameSectionName, 'SelectionId', str(frameInfo.getId()))
				if (frameInfo.getDuration() is not None):
					parser.set(frameSectionName, 'Duration', str(frameInfo.getDuration()))

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
		selectionId = int(parser.get('General', 'SelectionIdNext'))
		animationInfoId = int(parser.get('General', 'AnimationInfoIdNext'))
		resourceInfo = ResourceInformation(imagePath, selectionId, animationInfoId)
		loadedSelectionsSet = set()
		animationUsedSelectionsSet = set()
		for sectionName in parser.sections():
			if sectionName.startswith('SelectionInfo'):
				x, y = strToDoubleIntTuple(parser.get(sectionName, 'Position'))
				sizeX, sizeY = strToDoubleIntTuple(parser.get(sectionName, 'Size'))
				identifier = int(parser.get(sectionName, 'Id'))
				selection = SpriteSelection(x, y, sizeX, sizeY, identifier = identifier)
				resourceInfo.addSelection(selection)
				loadedSelectionsSet.add(identifier)

			elif sectionName.startswith('AnimationInfo'):
				name = parser.get(sectionName, 'Name')
				duration = float(parser.get(sectionName, 'Duration'))
				identifier = int(parser.get(sectionName, 'Id'))
				animationInfo = AnimationInfo(name, duration, identifier)
				numberOfFrames = int(parser.get(sectionName, 'NumberOfFrames'))
				for i in range(numberOfFrames):
					frameSectionName = 'Animation%dFrame%d' % (identifier, i)
					selectionId = int(parser.get(frameSectionName, 'SelectionId'))
					if parser.has_option(frameSectionName, 'Duration'):
						duration = float(parser.get(frameSectionName, 'Duration'))
					else:
						duration = None
					fi = FrameInfo(selectionId, duration)
					animationInfo.addFrameInfo(fi)
					animationUsedSelectionsSet.add(selectionId)

				resourceInfo.addAnimationInfo(animationInfo)

		assert animationUsedSelectionsSet <= loadedSelectionsSet, \
			"Error, animations on file %s use non existant selection!" % (filename, )
		return resourceInfo
