from singleton import Singleton

@Singleton
class CollisionToSceneCommunication:

	def __init__(self, selectionMethod, allObjectsMethod):
		self.__getSelectionMethod = selectionMethod
		self.__getAllObjectsMethod = allObjectsMethod

	def getSelectedObjects(self):
		return self.__getSelectionMethod()

	def getAllObjects(self):
		return self.__getAllObjectsMethod() 

@Singleton
class CollisionToMainLayoutCommunication:

	def __init__(self, giveBackKeyboardMethod):
		self.__giveBackKeyboardMethod = giveBackKeyboardMethod

	def giveBackKeyboard(self):
		self.__giveBackKeyboardMethod()

@Singleton
class SceneToObjectsMenu:
	def __init__(self, drawMethod):
		self.__drawMethod = drawMethod
		
	def draw(self, obj):
		self.__drawMethod(obj)
		
@Singleton
class SceneToFilesManager:
	def __init__(self, getSceneObjectsMethod):
		self.__getSceneObjectsMethod = getSceneObjectsMethod
		
	def getSceneObjects(self):
		return self.__getSceneObjectsMethod()
		