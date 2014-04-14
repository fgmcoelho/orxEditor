from singleton import Singleton

from scene import Scene, SceneAttributes
from editorobjects import RenderedObject
from editorutils import vector2ToVector3String
from ConfigParser import ConfigParser

@Singleton
class FilesManager:

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
			if (spriteInfo == None):
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
			if (collisionObject == None):
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
		ConfigObject = TileEditorConfig(filename)
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

	def exportScene(self, filename):
		parser = ConfigParser()
		parser.optionxform = str
		objectListName = 'ObjectList'
		
		renderedObjectsDict = Scene.Instance().getObjectsDict()
		objectsInScene = ''
		for inSceneId in renderedObjectsDict.keys():
			objectsInScene += renderedObjectsDict[inSceneId].getName() + ' # '

		parser.add_section(objectListName)
		parser.set(objectListName, 'ObjectNames', objectsInScene)

		for inSceneId in renderedObjectsDict.keys():
			# Needed data
			newSectionName = renderedObjectsDict[inSceneId].getName() 
			graphicSectionName = newSectionName + "_Graphic"
			bodySectionName = newSectionName + "_Body"
			bodyPartSectionName = newSectionName + "_BodyPart"
			collisionObject = renderedObjectsDict[inSceneId].getCollisionInfo()

			# Object
			parser.add_section(newSectionName)
			
			scale = (renderedObjectsDict[inSceneId].getScale(), renderedObjectsDict[inSceneId].getScale())
			layer = renderedObjectsDict[inSceneId].getLayer() * 0.01
			parser.set(newSectionName, 'Position', vector2ToVector3String(renderedObjectsDict[inSceneId].getPos(), layer))
			if(renderedObjectsDict[inSceneId].getFlipX() == True and renderedObjectsDict[inSceneId].getFlipY() == True):
				parser.set(newSectionName, 'Flip', 'Both')	
			elif (renderedObjectsDict[inSceneId].getFlipX() == True):
				parser.set(newSectionName, 'Flip', 'x')	
			elif (renderedObjectsDict[inSceneId].getFlipY() == True):
				parser.set(newSectionName, 'Flip', 'y')	
			

			parser.set(newSectionName, 'Scale', vector2ToVector3String(scale, 1))
			if (collisionObject != None):
				parser.set(newSectionName, 'Body', bodySectionName)
			
			# Graphic Part		
			parser.add_section(graphicSectionName);
			parser.set(graphicSectionName, 'Texture',  str(renderedObjectsDict[inSceneId].getPath()))
			parser.set(graphicSectionName, 'Smoothing',  'True')
			spriteInfo = renderedObjectsDict[inSceneId].getSpriteInfo()
			if (spriteInfo != None):
				coords = spriteInfo.getSpriteCoords()
				size = renderedObjectsDict[inSceneId].getBaseSize()
				pivot = (size[0]/2, size[1]/2)
				corner = (coords[0] * size[0], coords[1] * size[1])
				parser.set(graphicSectionName, 'TextureSize', vector2ToVector3String(size))
				parser.set(graphicSectionName, 'Pivot', vector2ToVector3String(pivot))
				parser.set(graphicSectionName, 'TextureCorner',  vector2ToVector3String(corner))
			
			# Body Part
			if (collisionObject != None):
				
				parser.add_section(bodySectionName)
				parser.set(bodySectionName, 'Dynamic', str(int(collisionObject.getIsDynamic())))
				parser.set(bodySectionName, 'AllowSleep', str(int(collisionObject.getAllowSleep())))
				parser.set(bodySectionName, 'PartList', bodyPartSectionName)
				
				parser.add_section(bodyPartSectionName)
				parser.set(bodyPartSectionName, 'SelfFlag', str(collisionObject.getSelfFlag()))
				parser.set(bodyPartSectionName, 'CheckMask', str(collisionObject.getCheckMask()))
				parser.set(bodyPartSectionName, 'Solid', str(int(collisionObject.getIsSolid())))
				parser.set(bodyPartSectionName, 'Type', str(collisionObject.getCollisionType()))

		f = open(filename, 'w')
		parser.write(f)
		f.close()

				
	def newScene(self, filename):
		self.resetAllWidgets()

