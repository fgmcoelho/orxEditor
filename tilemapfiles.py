from singleton import Singleton

from scene import SceneAttributes
from editorutils import vector2ToVector3String, strToDoubleFloatTuple, boolToStr, convertKivyCoordToOrxCoord, distance, isClockWise
from communicationobjects import SceneToFilesManager
from ConfigParser import ConfigParser
from collisioninfo import CollisionGuardian, CollisionInformation

@Singleton
class FilesManager:

	def __compileFlagsNames(self, listToCompile):
		l = []
		for flag in listToCompile:
			l.append(flag.getName())
		return '#'.join(l)

	def __init__(self):
		pass

	def saveScene(self, filename):

		parser = ConfigParser()
		tileEditorSectionName = 'TileEditor'
		assetsSectionName = 'Assets'
		objectListName = 'ObjectList'

		parser.add_section(tileEditorSectionName)
		parser.set(tileEditorSectionName, 'maxX', SceneAttributes.Instance().getValue('TilesMaxX'))
		parser.set(tileEditorSectionName, 'maxY', SceneAttributes.Instance().getValue('TilesMaxY'))
		parser.set(tileEditorSectionName, 'size', SceneAttributes.Instance().getValue('TilesSize'))
		parser.set(tileEditorSectionName, 'alignToGrid', 1)

		parser.add_section(assetsSectionName)
		parser.set(assetsSectionName, 'path', 'tiles')

		renderedObjectsDict = Scene.Instance().getObjectsDict()
		objectsInScene = ''
		for inSceneId in renderedObjectsDict.keys():
			objectsInScene += renderedObjectsDict[inSceneId].getName() + ' # '

		parser.add_section(objectListName)
		parser.set(objectListName, 'ObjectNames', objectsInScene)

		for inSceneId in renderedObjectsDict.keys():
			newSectionName = renderedObjectsDict[inSceneId].getName()
			parser.add_section(newSectionName)
			spriteInfo = renderedObjectsDict[inSceneId].getSpriteInfo()
			if (spriteInfo is None):
				parser.set(newSectionName, 'issprite', '0')
				parser.set(newSectionName, 'path', str(renderedObjectsDict[inSceneId].getPath()))
			else:
				parser.set(newSectionName, 'issprite', '1')
				parser.set(newSectionName, 'path', spriteInfo.getVirtualPath())
				parser.set(newSectionName, 'spritecoords', spriteInfo.getSpriteCoords())

			parser.set(newSectionName, 'pos', str(renderedObjectsDict[inSceneId].getPos()))
			parser.set(newSectionName, 'flipX', str(int(renderedObjectsDict[inSceneId].getFlipX())))
			parser.set(newSectionName, 'flipY', str(int(renderedObjectsDict[inSceneId].getFlipY())))
			parser.set(newSectionName, 'scale', str(renderedObjectsDict[inSceneId].getScale()))
			parser.set(newSectionName, 'layer', str(renderedObjectsDict[inSceneId].getLayer()))
			parser.set(newSectionName, 'size', str(renderedObjectsDict[inSceneId].getBaseSize()))

			collisionObject = renderedObjectsDict[inSceneId].getCollisionInfo()
			if (collisionObject is None):
				parser.set(newSectionName, 'hascollisioninfo', '0')
			else:
				parser.set(newSectionName, 'hascollisioninfo', '1')
				collisionInfoSectionName = newSectionName + '_collision_info'
				parser.add_section(collisionInfoSectionName)
				parser.set(collisionInfoSectionName, 'selfFlag', str(collisionObject.getSelfFlag()))
				parser.set(collisionInfoSectionName, 'checkMask', str(collisionObject.getCheckMask()))
				parser.set(collisionInfoSectionName, 'Solid', str(int(collisionObject.getIsSolid())))
				parser.set(collisionInfoSectionName, 'dynamic', str(int(collisionObject.getIsDynamic())))
				parser.set(collisionInfoSectionName, 'allowSleep', str(int(collisionObject.getAllowSleep())))
				parser.set(collisionInfoSectionName, 'type', str(collisionObject.getCollisionType()))

		f = open(filename, 'w')
		parser.write(f)
		f.close()

	def loadScene(self, filename):
		self.resetAllWidgets()

		parser = ConfigParser()
		parser.read(filename)
		objectList = parser.get('ObjectList', 'objectnames').split('#')
		for name in objectList:
			name = name.strip()
			if (name == ''):
				continue
			path = str(parser.get(name, 'path'))
			pos = strToDoubleFloatTuple(parser.get(name, 'pos'))
			flipX = bool(int(parser.get(name, 'flipX')))
			flipY = bool(int(parser.get(name, 'flipY')))
			scale = float(parser.get(name, 'scale'))
			layer = float(parser.get(name, 'layer'))
			size = strToDoubleFloatTuple(parser.get(name, 'size'))
			hasCollisionInfo = bool(int(parser.get(name, 'hascollisioninfo')))
			newCollisionInfo = None
			if (hasCollisionInfo == True):
				collisionInfoSectionName = name + '_collision_info'
				selfFlag = parser.get(collisionInfoSectionName, 'selfFlag')
				checkMask = parser.get(collisionInfoSectionName, 'checkMask')
				solid = bool(int(parser.get(collisionInfoSectionName, 'Solid')))
				dynamic = bool(int(parser.get(collisionInfoSectionName, 'dynamic')))
				allowSleep = bool(int(parser.get(collisionInfoSectionName, 'allowSleep')))
				collisionType = parser.get(collisionInfoSectionName, 'type')
				newCollisionInfo = CollisionInformation(selfFlag, checkMask, solid, dynamic, allowSleep, collisionType)

			self.scene.addObjectFullInfo(path, size, pos, scale, layer, flipX, flipY, newCollisionInfo)

	def __convertObjectPosition(self, obj, sceneMaxY):
		x, y = obj.getPos()
		sx, sy = obj.getBaseSize()
		return convertKivyCoordToOrxCoord((x, y + sy), sceneMaxY)


	def exportScene(self, filename):
		parser = ConfigParser()
		parser.optionxform = str
		objectListName = 'ObjectList'

		parser.add_section('Physics')
		parser.set('Physics', 'CollisionFlagList', self.__compileFlagsNames(CollisionGuardian.Instance().getFlags()))

		renderedObjectsList = SceneToFilesManager.Instance().getSceneObjects()
		objectsInSceneList = []
		for obj in renderedObjectsList:
			objectsInSceneList.append(obj.getName())

		objectsInScene = '#'.join(objectsInSceneList)

		parser.add_section(objectListName)
		parser.set(objectListName, 'ObjectNames', objectsInScene)
		sceneMaxY = SceneAttributes.Instance().getValue('TilesMaxY') * SceneAttributes.Instance().getValue('TilesSize')

		for obj in renderedObjectsList:
			# Needed data
			newSectionName = obj.getName()
			collisionInfo = obj.getCollisionInfo()
			graphicSectionName = newSectionName + "_Graphic"
			bodySectionName = newSectionName + "_Body"

			# Object
			parser.add_section(newSectionName)

			scale = (obj.getScale(), obj.getScale())
			layer = obj.getLayer() * 0.01
			parser.set(newSectionName, 'Graphic', graphicSectionName)
			parser.set(newSectionName, 'Position', vector2ToVector3String(self.__convertObjectPosition(obj, sceneMaxY), layer))
			if(obj.getFlipX() == True and obj.getFlipY() == True):
				parser.set(newSectionName, 'Flip', 'both')
			elif (obj.getFlipX() == True):
				parser.set(newSectionName, 'Flip', 'x')
			elif (obj.getFlipY() == True):
				parser.set(newSectionName, 'Flip', 'y')

			if (float(scale[0]) != 1.0 or float(scale[1]) != 1.0):
				parser.set(newSectionName, 'Scale', vector2ToVector3String(scale, 1))


			if (collisionInfo is not None):
				parser.set(newSectionName, 'Body', bodySectionName)

			# Graphic Part
			parser.add_section(graphicSectionName);
			parser.set(graphicSectionName, 'Texture',  str(obj.getPath()))
			parser.set(graphicSectionName, 'Smoothing',  'true')
			spriteInfo = obj.getSpriteInfo()
			if (spriteInfo is not None):
				coords = spriteInfo.getSpriteCoords()
				size = obj.getBaseSize()
				corner = (coords[0] * size[0], coords[1] * size[1])
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
					checkMask = self.__compileFlagsNames(currentPart.getCheckMask())
					if (checkMask != ''):
						parser.set(partSectionName, 'CheckMask', checkMask)

					selfFlags = self.__compileFlagsNames(currentPart.getSelfFlags())
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


	def newScene(self, filename):
		self.resetAllWidgets()

