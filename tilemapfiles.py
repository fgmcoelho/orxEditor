from kivy.uix.image import Image

from editorutils import vector2ToVector3String, strToDoubleFloatTuple, boolToStr, convertKivyCoordToOrxCoord, distance
from editorutils import isClockWise, createSpriteImage, strToDoubleIntTuple, strToBool
from editorobjects import BaseObject
from ConfigParser import ConfigParser
from collisioninfo import CollisionInformation, CollisionPartInformation
from modulesaccess import ModulesAccess
from scene import SceneAttributes

from os.path import sep, isfile, join
from shutil import copyfile

class FilesManager:
	def __compileObjListWithName(self, listToCompile):
		l = []
		for flag in listToCompile:
			l.append(flag.getName())
		return '#'.join(l)

	def __getSpriteCoords(self, parser, sectionName):
		if (strToBool(parser.get(sectionName, 'IsSprite')) == True):
			return strToDoubleIntTuple(parser.get(sectionName, 'SpriteCoords'))
		else:
			return (None, None)

	def __loadCollisionFlagsList(self, parser, sectionName, attribute):
		l = []
		for flag in parser.get(sectionName, attribute).split('#'):
			flagObj = ModulesAccess.get('CollisionGuardian').getFlagByName(flag)
			assert flagObj is not None, \
				'collision flag ' + flag + ' from section ' + sectionName + 'was not loaded.'
			l.append(flagObj)
		return l

	def __convertObjectPosition(self, obj, sceneMaxY, posAdjust):
		x, y = obj.getPos()
		sx, sy = obj.getSize()
		return convertKivyCoordToOrxCoord((x + posAdjust[0], y + sy - posAdjust[1]), sceneMaxY)

	def __init__(self):
		ModulesAccess.add('FilesManager', self)
		self.__tileEditorSectionName = 'TileEditor'
		self.__assetsSectionName = 'Assets'
		self.__objectListName = 'ObjectList'
		self.__groupsListName = 'LayersList'
		self.__collisionListName = 'CollisionFlagList'

	def saveScene(self, filename):
		parser = ConfigParser()
		parser.optionxform = str

		sceneAttributes = ModulesAccess.get('SceneHandler').getCurrentSceneAttributes()
		parser.add_section(self.__tileEditorSectionName)
		parser.set(self.__tileEditorSectionName, 'MaxX', sceneAttributes.getValue('TilesMaxX'))
		parser.set(self.__tileEditorSectionName, 'MaxY', sceneAttributes.getValue('TilesMaxY'))
		parser.set(self.__tileEditorSectionName, 'Size', sceneAttributes.getValue('TilesSize'))

		parser.add_section(self.__assetsSectionName)
		parser.set(self.__assetsSectionName, 'Path', 'tiles')

		parser.add_section(self.__groupsListName)
		parser.set(self.__groupsListName, 'LayerNames',
			self.__compileObjListWithName(ModulesAccess.get('LayerGuardian').getLayerList())
		)

		parser.add_section(self.__collisionListName)
		parser.set(self.__collisionListName, 'Flags',
			self.__compileObjListWithName(ModulesAccess.get('CollisionGuardian').getFlags())
		)

		renderedObjects = ModulesAccess.get('SceneHandler').getAllObjects()
		objectsInScene = []
		for obj in renderedObjects:
			objectsInScene.append(obj.getName())

		parser.add_section(self.__objectListName)
		parser.set(self.__objectListName, 'ObjectNames', '#'.join(objectsInScene))
		parser.set(self.__objectListName, 'LastId', str(ModulesAccess.get('SceneHandler').getSceneObjectId()))

		for obj in renderedObjects:
			newSectionName = obj.getName()
			parser.add_section(newSectionName)
			spriteInfo = obj.getSpriteInfo()
			if (spriteInfo is None):
				parser.set(newSectionName, 'IsSprite', boolToStr(False))
				parser.set(newSectionName, 'AbsolutePath', str(obj.getPath()))
			else:
				parser.set(newSectionName, 'IsSprite', boolToStr(True))
				parser.set(newSectionName, 'AbsolutePath', spriteInfo.getVirtualPath())
				parser.set(newSectionName, 'SpriteCoords', spriteInfo.getSpriteCoords())
				parser.set(newSectionName, 'SpriteSize', spriteInfo.getSpriteSize())

			parser.set(newSectionName, 'Position', str(obj.getPos()))
			parser.set(newSectionName, 'FlipX', boolToStr(obj.getFlipX()))
			parser.set(newSectionName, 'FlipY', boolToStr(obj.getFlipY()))
			parser.set(newSectionName, 'Scale', str(obj.getScale()))
			parser.set(newSectionName, 'Layer', obj.getLayer())
			parser.set(newSectionName, 'Size', str(obj.getBaseSize()))

			collisionObject = obj.getCollisionInfo()
			if (collisionObject is None):
				parser.set(newSectionName, 'HasCollisionInfo', boolToStr(False))
			else:
				parser.set(newSectionName, 'HasCollisionInfo', boolToStr(True))
				collisionInfoSectionName = newSectionName + '_CollisionInfo'
				parts = collisionObject.getPartsList()

				parser.add_section(collisionInfoSectionName)
				parser.set(collisionInfoSectionName, 'Dynamic', boolToStr(collisionObject.getDynamic()))
				parser.set(collisionInfoSectionName, 'FixedRotation', boolToStr(collisionObject.getFixedRotation()))
				parser.set(collisionInfoSectionName, 'HighSpeed', boolToStr(collisionObject.getHighSpeed()))
				parser.set(collisionInfoSectionName, 'NumberOfParts', len(parts))

				i = 0
				for part in parts:
					partSectionName = newSectionName + '_Part_' + str(i)
					parser.add_section(partSectionName)
					parser.set(partSectionName, 'Solid', boolToStr(part.getSolid()))
					parser.set(partSectionName, 'SelfFlags', self.__compileObjListWithName(part.getSelfFlags()))
					parser.set(partSectionName, 'CheckMask', self.__compileObjListWithName(part.getCheckMask()))
					parser.set(partSectionName, 'Type', part.getFormType())
					points = part.getPoints()
					if (points is not None):
						strPoints = []
						for point in points:
							strPoints.append(str(point))
						parser.set(partSectionName, 'Points', '#'.join(strPoints))
					i += 1

		parser.set(self.__objectListName, 'LastId', str(ModulesAccess.get('SceneHandler').getSceneObjectId()))

		f = open(filename, 'w')
		parser.write(f)
		f.close()

	def loadScene(self, filename):
		try:
			parser = ConfigParser()
			parser.optionxform = str
			parser.read(filename)
		except:
			raise Exception("Error opening the file.")

		try:
			# At first we need to recreate the base objects that were used, since the selections
			# may even no longer exist.
			objectNames = parser.get(self.__objectListName, 'ObjectNames').split('#')
			tempBaseImages = {}
			for name in objectNames:
				fullPath = parser.get(name, 'AbsolutePath')
				if (fullPath not in tempBaseImages):
					tempBaseImages[fullPath] = None

		except Exception, e:
			raise Exception('Error parsing the file: ' + str(e))

		try:
			for key in tempBaseImages.keys():
				tempBaseImages[key] = Image(source = key)
		except Exception, e:
			raise Exception('Error loading files needed to load the scene: ' + str(e))

		try:
			tempBaseObjects = {}
			identifier = 0
			for name in objectNames:
				fullPath = parser.get(name, 'AbsolutePath')
				if (fullPath not in tempBaseObjects):
					coords = self.__getSpriteCoords(parser, name)
					if (coords == (None, None)):
						tempBaseObjects[(fullPath, coords)] = BaseObject(tempBaseImages[fullPath], identifier)
					else:
						width, height = strToDoubleIntTuple(parser.get(name, 'Size'))
						x, y = coords
						imageToUse = createSpriteImage(tempBaseImages[fullPath], x, y, width, height)
						textureSize = strToDoubleIntTuple(parser.get(name, 'SpriteSize'))
						tempBaseObjects[(fullPath, coords)] = BaseObject(imageToUse, identifier, fullPath, (x, y),
							textureSize)
					identifier += 1

		except Exception, e:
			raise Exception('Error creating the base objects: ' + str(e))

		try:
			ModulesAccess.get('LayerGuardian').reset()
			ModulesAccess.get('LayerGuardian').deleteLayerByName('default')
			defaultPresent = False
			for layer in parser.get(self.__groupsListName, 'LayerNames').split('#'):
				if (layer == 'default'):
					defaultPresent = True
				ModulesAccess.get('LayerGuardian').addNewLayer(layer)
			assert defaultPresent == True, 'default group is missing.'

		except Exception, e:
			raise Exception('Error creating the layer groups: ' + str(e))

		try:
			ModulesAccess.get('CollisionGuardian').reset()
			for collisionFlag in parser.get(self.__collisionListName, 'Flags').split('#'):
				collisionFlag = collisionFlag.strip()
				if (collisionFlag != ''):
					ModulesAccess.get('CollisionGuardian').addNewFlag(collisionFlag)

		except Exception, e:
			raise Exception('Error creating the collision flags: ' + str(e))

		try:
			tilesOnX = int(parser.get(self.__tileEditorSectionName, 'MaxX'))
			tilesOnY = int(parser.get(self.__tileEditorSectionName, 'MaxY'))
			tilesSize = int(parser.get(self.__tileEditorSectionName, 'Size'))

		except Exception, e:
			raise Exception('Error parsing the file: ' + str(e))

		try:
			newSceneAttributes = SceneAttributes(tilesSize, tilesOnX, tilesOnY)
			ModulesAccess.get('SceneHandler').getAllObjects().newScene(newSceneAttributes)
		except Exception, e:
			raise Exception('Error creating the base scene to load: ' + str(e))

		loadedLayers = []
		for layer in ModulesAccess.get('LayerGuardian').getLayerList():
			loadedLayers.append(layer.getName())

		try:
			for name in objectNames:
				fullPath = parser.get(name, 'AbsolutePath')
				coords = self.__getSpriteCoords(parser, name)
				identifier = int(name.split('_')[-1])
				position = strToDoubleFloatTuple(parser.get(name, 'Position'))
				scale = float(parser.get(name, 'Scale'))
				flipX = strToBool(parser.get(name, 'FlipX'))
				flipY = strToBool(parser.get(name, 'FlipY'))
				layer = parser.get(name, 'Layer')
				assert layer in loadedLayers, 'layer of the object ' + name + ' was not loaded.'
				if (strToBool(parser.get(name, 'HasCollisionInfo')) == False):
					collisionInfo = None
				else:
					collisionInfoSectionName = name + '_CollisionInfo'
					dynamic = strToBool(parser.get(collisionInfoSectionName, 'Dynamic'))
					fixedRotation = strToBool(parser.get(collisionInfoSectionName, 'FixedRotation'))
					highSpeed = strToBool(parser.get(collisionInfoSectionName, 'HighSpeed'))
					collisionInfo = CollisionInformation(dynamic, highSpeed, fixedRotation)
					numberOfParts = int(parser.get(collisionInfoSectionName, 'NumberOfParts'))
					for i in range(numberOfParts):
						partSectionName = name + '_Part_' + str(i)
						checkMask = self.__loadCollisionFlagsList(parser, partSectionName, 'CheckMask')
						selfFlags = self.__loadCollisionFlagsList(parser, partSectionName, 'SelfFlags')
						solid = strToBool(parser.get(partSectionName, 'Solid'))
						formType = parser.get(partSectionName, 'Type')
						if (parser.has_option(partSectionName, 'Points') == True):
							points = []
							for point in parser.get(partSectionName, 'Points').split('#'):
								points.append(strToDoubleIntTuple(point))
						else:
							points = None

						newPart = CollisionPartInformation(checkMask, selfFlags, solid, formType, points)
						collisionInfo.addPart(newPart)

				ModulesAccess.get('SceneHandler').addObjectByInfo(tempBaseObjects[(fullPath, coords)], identifier,
					position, scale, flipX, flipY, layer, collisionInfo)

		except Exception, e:
			raise Exception('Error loading the objecs to the list:' + str(e))

		ModulesAccess.get('SceneHandler').setSceneObjectId(int(parser.get(self.__objectListName, 'LastId')))

	def exportScene(self, filename, assetsPath, shouldSmooth, defaults = None):
		parser = ConfigParser()
		parser.optionxform = str

		if (defaults is not None):
			for section in defaults.keys():
				parser.add_section(section)
				for option, value in defaults[section].iteritems():
					parser.set(section, option, value)

		parser.add_section('General')
		parser.set('General', 'CollisionFlagList', self.__compileObjListWithName(
			ModulesAccess.get('CollisionGuardian').getFlags())
		)
		parser.set('General', 'GroupList', self.__compileObjListWithName(
			ModulesAccess.get('LayerGuardian').getLayerList())
		)

		renderedObjectsList = ModulesAccess.get('SceneHandler').getAllObjects()
		numberOfLists = 1 + len(renderedObjectsList)/64
		if (len(renderedObjectsList) % 64 == 0):
			numberOfLists -= 1

		parser.set('General', 'ObjectListsNumber', str(numberOfLists))
		objectsInScene = []
		i = 0
		j = 0
		for obj in renderedObjectsList:
			objectsInScene.append(obj.getName())
			i += 1
			if (i == 64):
				parser.set('General', 'ObjectList_' + str(j), '#'.join(objectsInScene))
				i = 0
				j += 1
				objectsInScene = []
		if (i != 0):
				parser.set('General', 'ObjectList_' + str(j), '#'.join(objectsInScene))

		assetsDict = {}
		sceneAttributes = ModulesAccess.get('SceneHandler').getCurrentSceneAttributes()
		sceneMaxY = sceneAttributes.getValue('TilesMaxY') * sceneAttributes.getValue('TilesSize')
		for obj in renderedObjectsList:
			# Needed data
			newSectionName = obj.getName()
			collisionInfo = obj.getCollisionInfo()
			graphicSectionName = newSectionName + "_Graphic"
			bodySectionName = newSectionName + "_Body"

			# Object
			parser.add_section(newSectionName)
			parser.set(newSectionName, 'Graphic', graphicSectionName)
			parser.set(newSectionName, 'Group', obj.getLayer())
			renderedSize = obj.getSize()
			if(obj.getFlipX() == True and obj.getFlipY() == True):
				posAdjust = renderedSize
				scale = (-obj.getScale(), -obj.getScale())
			elif (obj.getFlipX() == True):
				posAdjust = (renderedSize[0], 0)
				scale = (-obj.getScale(), obj.getScale())
			elif (obj.getFlipY() == True):
				posAdjust = (0, renderedSize[1])
				scale = (obj.getScale(), -obj.getScale())
			else:
				posAdjust = (0, 0)
				scale = (obj.getScale(), obj.getScale())

			parser.set(newSectionName, 'Position',
				vector2ToVector3String(self.__convertObjectPosition(obj, sceneMaxY, posAdjust), 1.0))

			if (float(scale[0]) != 1.0 or float(scale[1]) != 1.0):
				parser.set(newSectionName, 'Scale', vector2ToVector3String(scale, 1))

			if (collisionInfo is not None):
				parser.set(newSectionName, 'Body', bodySectionName)

			# Graphic Part
			parser.add_section(graphicSectionName);
			textureName = obj.getPath().split(sep)[-1]
			if (textureName not in assetsDict):
				assetsDict[textureName] = obj.getPath()

			parser.set(graphicSectionName, 'Texture',  textureName)
			if (shouldSmooth == True):
				parser.set(graphicSectionName, 'Smoothing',  boolToStr(True))

			spriteInfo = obj.getSpriteInfo()
			if (spriteInfo is not None):
				coords = spriteInfo.getSpriteCoords()
				size = obj.getBaseSize()
				fullSize = spriteInfo.getSpriteSize()
				corner = convertKivyCoordToOrxCoord((coords[0], coords[1] + size[1]), fullSize[1])
				parser.set(graphicSectionName, 'TextureSize', vector2ToVector3String(size))
				parser.set(graphicSectionName, 'TextureCorner',  vector2ToVector3String(corner))

			# Body Part
			if (collisionInfo is not None):
				parser.add_section(bodySectionName)
				parser.set(newSectionName, 'Body', bodySectionName)
				objPartNames = []
				objParts = collisionInfo.getPartsList()
				for i in range(len(objParts)):
					objPartNames.append(obj.getName() + '_part_' + str(i))

				parser.set(bodySectionName, 'PartList', '#'.join(objPartNames))
				parser.set(bodySectionName, 'Dynamic', boolToStr(collisionInfo.getDynamic()))
				parser.set(bodySectionName, 'FixedRotation', boolToStr(collisionInfo.getFixedRotation()))
				parser.set(bodySectionName, 'HighSpeed', boolToStr(collisionInfo.getHighSpeed()))

				for i in range(len(objParts)):
					partSectionName = objPartNames[i]
					currentPart = objParts[i]
					form = currentPart.getFormType()
					parser.add_section(partSectionName)
					parser.set(partSectionName, 'Solid', boolToStr(currentPart.getSolid()))
					parser.set(partSectionName, 'Type', form)
					checkMask = self.__compileObjListWithName(currentPart.getCheckMask())
					if (checkMask != ''):
						parser.set(partSectionName, 'CheckMask', checkMask)

					selfFlags = self.__compileObjListWithName(currentPart.getSelfFlags())
					if (selfFlags != ''):
						parser.set(partSectionName, 'SelfFlags', selfFlags)

					points = currentPart.getPoints()
					if (points is not None):
						if (form == 'box'):
							topX = max(points[0][0], points[1][0])
							topY = max(points[0][1], points[1][1])
							bottomX = min(points[0][0], points[1][0])
							bottomY = min(points[0][1], points[1][1])
							topLeftVector = convertKivyCoordToOrxCoord((bottomX, topY), obj.getBaseSize()[1])
							bottomRightVector = convertKivyCoordToOrxCoord((topX, bottomY), obj.getBaseSize()[1])
							parser.set(partSectionName, 'TopLeft', vector2ToVector3String(topLeftVector, 1))
							parser.set(partSectionName, 'BottomRight', vector2ToVector3String(bottomRightVector, 1))
						elif (form == 'sphere'):
							center = convertKivyCoordToOrxCoord(points[0], obj.getBaseSize()[1])
							radius = distance(points[0], points[1])
							parser.set(partSectionName, 'Center', vector2ToVector3String(center, 1))
							parser.set(partSectionName, 'Radius', radius)

					if (form == 'mesh'):
						if (points is None):
							sx, sy = obj.getBaseSize()
							points = [(0, 0), (sx, 0), (sx, sy), (0, sy)]

						convertedPointsList = []
						for point in points:
							convertedPoint = convertKivyCoordToOrxCoord(point, obj.getBaseSize()[1])
							convertedPointsList.append(convertedPoint)

						if (isClockWise(convertedPointsList) == False):
							convertedPointsList.reverse()

						strConvertedPointsList = []
						for convertedPoint in convertedPointsList:
							strConvertedPointsList.append(vector2ToVector3String(convertedPoint, 1))

						parser.set(partSectionName, 'VertexList', '#'.join(strConvertedPointsList))


		f = open(filename, 'w')
		parser.write(f)
		f.close()

		for key in assetsDict:
			newFilePath = join(assetsPath, key)
			if (isfile(newFilePath) == False):
				copyfile(assetsDict[key], newFilePath)


