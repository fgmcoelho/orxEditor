from singleton import Singleton

from os.path import join
from os import listdir, getcwd

from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

from editorobjects import BaseObject
from objectdescriptor import ObjectDescriptor
from editorutils import EmptyScrollEffect, createSpriteImage
from communicationobjects import SceneToObjectsMenu
from splittedimagemap import SplittedImageImporter

class ObjectMenuItem:

	def __handle(self, image, touch):
		if (touch.is_mouse_scrolling == False and self.getDisplayImage().collide_point(*touch.pos) == True and
				touch.is_double_tap == True):
			if (ObjectDescriptor.Instance().getCurrentObject() == self.getBaseObject()):
				SceneToObjectsMenu.Instance().draw(self.getBaseObject())
			else:
				ObjectDescriptor.Instance().setObject(self.getBaseObject())

	def __init__(self, baseObject, size):
		self.__baseObject = baseObject
		self.__displayImage = Image(texture = baseObject.getBaseImage().texture, size = size, size_hint = (None, None),
			on_touch_down = self.__handle)

	def getBaseObject(self):
		return self.__baseObject

	def getDisplayImage(self):
		return self.__displayImage

class ShortcutHandler:
	def __init__(self):
		self.__shortcuts = {}
		for i in range(10):
			self.__shortcuts[str(i)] = None
	
	def setShortcut(self, obj, code):
		assert code in '0123456789', 'Invalid code for shortcut: ' + str(code) + '.'
		assert isinstance(obj, BaseObject) == True, 'Invalid object type for a shortcut, must be BaseObject.'
		self.__shortcuts[code] = obj

	def getShortcut(self, code):
		assert code in '0123456789', 'Invalid code for shortcut: ' + str(code) + '.'
		return self.__shortcuts[code]

@Singleton
class ObjectsMenu:
	def __reloadMenuList(self):
		self.__numberOfItems = len(self.__menuObjectsList)
		self.__objectListLayout.clear_widgets()
		self.__objectListLayout.rows = self.__numberOfItems
		self.__objectListLayout.size[1] = (self.__numberOfItems * 67)
		for menuObjectItem in self.__menuObjectsList:
			self.__objectListLayout.add_widget(menuObjectItem.getDisplayImage())

	def __loadPng(self, item, pngsToIgnoreList):
		fullPath = join(getcwd(), 'tiles', item)
		if (fullPath in pngsToIgnoreList):
			return

		img = Image(source = fullPath)
		obj = BaseObject(img, self.__baseObjectId)
		self.__menuObjectsList.append(ObjectMenuItem(obj, (64, 64)))
		self.__numberOfItems += 1
		self.__baseObjectId += 1

	def __loadResourceInfoList(self, resourceInfo):
		l = []
		mainImage = Image (source = resourceInfo.getPath())
		if (resourceInfo.getKeepOriginal() == True):
			l.append(BaseObject(mainImage, self.__baseObjectId))
			self.__baseObjectId += 1

		for selection in resourceInfo.getSelectionList():
			x = selection.getX()
			y = selection.getY()
			width = selection.getSizeX()
			height = selection.getSizeY()
			image = createSpriteImage(mainImage, x, y, width, height)
			obj = BaseObject(image, self.__baseObjectId, resourceInfo.getPath(), (x, y))
			l.append(obj)
			self.__baseObjectId += 1

		return l

	def __loadOpf(self, item, pngsToIgnoreList):
		resourceInfo = SplittedImageImporter.load(join(getcwd(), 'tiles',item))

		baseObjectList = self.__loadResourceInfoList(resourceInfo)
		if baseObjectList != []:
			for baseObject in baseObjectList:
				self.__menuObjectsList.append(ObjectMenuItem(baseObject, (64, 64)))
				self.__numberOfItems += 1
			pngsToIgnoreList.append(baseObject.getPath())

	def __loadItems(self):
		l = listdir(join(getcwd(), 'tiles'))
		self.__menuObjectsList = []
		self.__numberOfItems = 0
		self.__baseObjectId = 0
		pngsToIgnoreList = []
		for item in l:
			if (item[-4:] == '.opf'):
				self.__loadOpf(item, pngsToIgnoreList)

		for item in l:
			if (item[-4:] == '.png' and item not in pngsToIgnoreList):
				self.__loadPng(item, pngsToIgnoreList)

		if (self.__objectListLayout is None):
			self.__objectListLayout = GridLayout(cols=1, rows = self.__numberOfItems, size_hint = (None, None),
				spacing = (0, 3))
		else:
			self.__objectListLayout.rows = self.__numberOfItems

		for menuObject in self.__menuObjectsList:
			img = menuObject.getDisplayImage()
			self.__objectListLayout.add_widget(img)

		self.__objectListLayout.size = (100, self.__numberOfItems * 67)

	def __init__(self):
		self.__shortcutHandler = ShortcutHandler()
		self.__objectListLayout = None
		self.__loadItems()
		self.__scrollView = ScrollView(size_hint = (1.0, 1.0), do_scroll = (0, 1), effect_cls = EmptyScrollEffect)
		self.__scrollView.add_widget(self.__objectListLayout)

	def reloadResource(self, resourceInfo):
		pathToCheck = resourceInfo.getPath()
		startIndex = None
		finalIndex = None
		i = 0
		for menuObject in self.__menuObjectsList:
			if (menuObject.getBaseObject().getPath() == pathToCheck):
				if (startIndex is None):
					startIndex = i
			else:
				if (startIndex is not None):
					finalIndex = i
					break
			
			i += 1

		newObjectMenuItemList = []
		for baseObject in self.__loadResourceInfoList(resourceInfo):
			newObjectMenuItemList.append(ObjectMenuItem(baseObject, (64, 64)))
			
		if (startIndex is not None):
			if (finalIndex is not None):
				self.__menuObjectsList = self.__menuObjectsList[0:startIndex] + newObjectMenuItemList + \
					self.__menuObjectsList[finalIndex:]
			else:
				self.__menuObjectsList = newObjectMenuItemList
		else:
			self.__menuObjectsList.extend(newObjectMenuItemList)

		self.__reloadMenuList()
		
	def getLayout(self):
		return self.__scrollView

	def resetAllWidgets(self):
		for menuObject in self.__menuObjectsList:
			self.__scrollView.remove_widget(menuObject.getDisplayImage())
			menuObject = None

		self.__loadItems()

	def setShortcut(self, code):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		if (isinstance(obj, BaseObject) == True):
			self.__shortcutHandler.setShortcut(obj, code)

	def processShortcut(self, code):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		print obj
		if (obj is not None):
			print obj.getIdentifier()
			print self.__shortcutHandler.getShortcut(code).getIdentifier()
			if (obj == self.__shortcutHandler.getShortcut(code)):
				SceneToObjectsMenu.Instance().draw(obj)
			else:
				ObjectDescriptor.Instance().setObject(obj)

