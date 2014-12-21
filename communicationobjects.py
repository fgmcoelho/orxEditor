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

@Singleton
class CollisionToCollisionForm:
	def __init__(self, previewMethod):
		self.__previewMethod = previewMethod

	def preview(self):
		self.__previewMethod()

@Singleton
class ObjectDescriptorToResourceLoarder:
	def __init__(self, openPopUpMethod):
		self.__openPopupMethod = openPopUpMethod

	def openPopUp(self, path):
		self.__openPopupMethod(path)
	
@Singleton
class ResourceLoaderToObjectDescriptor:
	def __init__(self, reloadResource):
		self.__reloadResourceMethod = reloadResource

	def reloadResource(self, which):
		self.__reloadResourceMethod(which)

@Singleton
class LayerToSceneCommunication:
	def __init__(self, selectionMethod, allObjectsMethod, redrawMethod):
		self.__getSelectionMethod = selectionMethod
		self.__getAllObjectsMethod = allObjectsMethod
		self.__redrawMethod = redrawMethod

	def getSelectedObjects(self):
		return self.__getSelectionMethod()

	def getAllObjects(self):
		return self.__getAllObjectsMethod()

	def redraw(self):
		return self.__redrawMethod()

@Singleton
class FileOptionsMenuToScene:
	def __init__(self, newSceneMethod):
		self.__newSceneMethod = newSceneMethod

	def newScene(self, attributes):
		return self.__newSceneMethod(attributes)

