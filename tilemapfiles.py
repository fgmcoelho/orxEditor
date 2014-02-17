from singleton import Singleton

from scene import Scene, SceneAttributes
from editorobjects import RenderedObject

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

				
	def newScene(self, filename):
		self.resetAllWidgets()

