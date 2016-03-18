from editorutils import strToDoubleIntTuple
from spriteinfo import FrameInfo, AnimationInfo, SpriteSelection, LinkInfo

from ConfigParser import ConfigParser
from os.path import isfile

class ResourceInformation:
	def __addValueToDictWithId(self, whichDict, value, identifier, maxId):
		assert identifier not in whichDict, 'Error, selection already added.'
		assert identifier < maxId, 'Error invalid state reached. Id: %d | Max id: %d' % (identifier, maxId)
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

	def __init__(self, path, selectionId = 0, animationId = 0, linkId = 0):
		self.__path = path
		self.__selectionDict = {}
		self.__animationInfoDict = {}
		self.__linkDict = {}
		self.__selectionId = selectionId
		self.__animationInfoId = animationId
		self.__linkId = linkId
		self.__removedAnimations = []

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

	def addLink(self, linkInfo):
		identifier = linkInfo.getId()
		if (identifier is None):
			self.__linkDict[self.__linkId] = linkInfo
			linkInfo.setId(self.__linkId)
			self.__linkId += 1
			return self.__linkId - 1
		else:
			return self.__addValueToDictWithId(self.__linkDict, linkInfo, identifier, self.__linkId)

	def removeSelectionById(self, identifier):
		self.__removeById(self.__selectionDict, identifier)
		toRemove = []
		for animationId, animationInfo in self.__animationInfoDict.iteritems():
			if (identifier in animationInfo.getUsedSelections()):
				toRemove.append(animationId)

		for key in toRemove:
			self.removeAnimationInfoById(key)

	def removeAnimationInfoById(self, identifier):
		self.__removedAnimations.append(self.__animationInfoDict[identifier])
		self.__removeById(self.__animationInfoDict, identifier)
		toRemove = []
		for linkId, linkInfo in self.__linkDict.iteritems():
			if (identifier == linkInfo.getSourceId() or identifier == linkInfo.getDestinationId()):
				toRemove.append(linkId)

		for key in toRemove:
			del self.__linkDict[key]

	def removeLinkById(self, identifier):
		self.__removeById(self.__linkDict, identifier)

	def getSelectionById(self, identifier):
		return self.__getById(self.__selectionDict, identifier)

	def getAnimationInfoById(self, identifier):
		return self.__getById(self.__animationInfoDict, identifier)

	def getLinkById(self, identifier):
		return self.__getById(self.__linkDict, identifier)

	def getNumberOfSelections(self):
		return len(self.__selectionDict)

	def getNumberOfAnimationInfos(self):
		return len(self.__animationInfoDict)

	def getNumberOfLinks(self):
		return len(self.__linkDict)

	def getSelectionList(self):
		return self.__selectionDict.values()

	def getAnimationInfoList(self):
		return self.__animationInfoDict.values()

	def getLinksList(self):
		return self.__linkDict.values()

	def getSelectionItems(self):
		return self.__selectionDict.items()

	def getAnimationInfoItems(self):
		return self.__animationInfoDict.items()

	def getLinkItems(self):
		return self.__linkDict.items()

	def getSelectionId(self):
		return self.__selectionId

	def getAnimationInfoId(self):
		return self.__animationInfoId

	def getLinkId(self):
		return self.__linkId

	def clear(self):
		self.__selectionDict = {}
		self.__animationInfoDict = {}
		self.__linkDict = {}

	def hasSameSelection(self, otherSelection):
		for savedSelection in self.__selectionDict.values():
			if (savedSelection.compare(otherSelection) == True):
				return True
		return False

	def countAnimationInfoAndLinksWithSelectionId(self, selectionId):
		relatedAnims = set()
		for animationInfo in self.__animationInfoDict.itervalues():
			if (selectionId in animationInfo.getUsedSelections()):
				relatedAnims.add(animationInfo.getId())

		relatedLinks = set()
		for link in self.__linkDict.itervalues():
			if (link.getSourceId() in relatedAnims or link.getDestinationId() in relatedAnims):
				relatedLinks.add(link.getId())

		return len(relatedAnims), len(relatedLinks)

	def getAnimationNamesWithSelectionId(self, selectionId):
		relatedAnims = []
		for animationInfo in self.__animationInfoDict.itervalues():
			if (selectionId in animationInfo.getUsedSelections()):
				relatedAnims.append(animationInfo.getName())
		return relatedAnims

	def countLinkWithAnimationId(self, animationId):
		count = 0
		for link in self.__linkDict.values():
			if (link.getSourceId() == animationId or link.getDestinationId() == animationId):
				count += 1
		return count

	def getPath(self):
		return self.__path

	def getRemovedAnimationNames(self):
		l = []
		for animationInfo in  self.__removedAnimations:
			l.append(animationInfo.getName())
		return l

	def getAnimationNames(self):
		l = []
		for animationInfo in self.__animationInfoDict.itervalues():
			l.append(animationInfo.getName())
		return l

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
		parser.set('General', 'LinkIdNext', str(resourceInfo.getLinkId()))

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

		for identifier, linkInfo in resourceInfo.getLinkItems():
			sectionName = 'LinkInfo' + str(linkInfo.getId())
			parser.add_section(sectionName)
			parser.set(sectionName, 'Id', str(linkInfo.getId()))
			parser.set(sectionName, 'SourceId', str(linkInfo.getSourceId()))
			parser.set(sectionName, 'DestinationId', str(linkInfo.getDestinationId()))
			parser.set(sectionName, 'Property', str(linkInfo.getProperty()))
			parser.set(sectionName, 'Priority', str(linkInfo.getPriority()))

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
			assert isfile(filename), 'File not found.'

		parser = ConfigParser()
		parser.read(filename)

		imagePath = parser.get('General', 'Path')
		selectionId = int(parser.get('General', 'SelectionIdNext'))
		animationInfoId = int(parser.get('General', 'AnimationInfoIdNext'))
		linkId = int(parser.get('General', 'LinkIdNext'))
		resourceInfo = ResourceInformation(imagePath, selectionId, animationInfoId, linkId)
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

			elif sectionName.startswith('LinkInfo'):
				identifier = int(parser.get(sectionName, 'Id'))
				sourceId = int(parser.get(sectionName, 'SourceId'))
				destinationId = int(parser.get(sectionName, 'DestinationId'))
				property = parser.get(sectionName, 'Property')
				priority  = int(parser.get(sectionName, 'Priority'))
				li = LinkInfo(sourceId, destinationId, priority, property, identifier)
				resourceInfo.addLink(li)

		assert animationUsedSelectionsSet <= loadedSelectionsSet, \
			"Error, animations on file %s use non existant selection!" % (filename, )
		return resourceInfo
