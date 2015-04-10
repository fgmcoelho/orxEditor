from singleton import Singleton

from os.path import join, relpath, split, sep as pathSeparator
from os import listdir, getcwd

from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.boxlayout import BoxLayout

from editorobjects import BaseObject
from objectdescriptor import ObjectDescriptor
from editorutils import EmptyScrollEffect, createSpriteImage
from communicationobjects import SceneToObjectsMenu
from splittedimagemap import SplittedImageImporter
from modulesaccess import ModulesAccess
from uisizes import mainLayoutSize
from editorheritage import IgnoreTouch, LayoutGetter

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

	def __loadPng(self, item):
		img = Image(source = fullPath)
		self.__menuObjectsList.append(BaseObject(img, self.__baseObjectId))
		self.__baseObjectId += 1

	def __loadResourceInfoList(self, resourceInfo):
		l = []
		mainImage = Image (source = resourceInfo.getPath())
		if (resourceInfo.getKeepOriginal() == True):
			l.append(BaseObject(mainImage, self.__baseObjectId))
			self.__baseObjectId += 1

		spriteSize = tuple(mainImage.texture.size)
		for selection in resourceInfo.getSelectionList():
			x = selection.getX()
			y = selection.getY()
			width = selection.getSizeX()
			height = selection.getSizeY()
			image = createSpriteImage(mainImage, x, y, width, height)
			obj = BaseObject(image, self.__baseObjectId, resourceInfo.getPath(), (x, y), spriteSize)
			l.append(obj)
			self.__baseObjectId += 1

		return l

	def __loadOpf(self, item, pngsToIgnoreList):
		resourceInfo = SplittedImageImporter.load(join(getcwd(), 'tiles',item))
		baseObjectList = self.__loadResourceInfoList(resourceInfo)

		if baseObjectList != []:
			for baseObject in baseObjectList:
				self.__menuObjectsList.append(ObjectMenuItem(baseObject, (64, 64)))
			pngsToIgnoreList.append(item)
			print 'Png to ignore: ', item

	def __loadItems(self):
		l = listdir(join(getcwd(), 'tiles'))
		self.__menuObjectsList = []
		self.__baseObjectId = 0
		pngsToIgnoreList = []
		for item in l:
			if (item[-4:] == '.opf'):
				self.__loadOpf(item, pngsToIgnoreList)

		for item in l:
			if (item[-4:] == '.png' and item not in pngsToIgnoreList):
				self.__loadPng(item)


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
		selectedObject = ObjectDescriptor.Instance().getCurrentObject()
		shortcutObject = self.__shortcutHandler.getShortcut(code)
		if (selectedObject is not None and shortcutObject is not None):
			if (selectedObject == shortcutObject):
				SceneToObjectsMenu.Instance().draw(selectedObject)
			else:
				ObjectDescriptor.Instance().setObject(shortcutObject)
		elif shortcutObject is not None:
			ObjectDescriptor.Instance().setObject(shortcutObject)

class NewBaseObjectDisplay(LayoutGetter):
	def __init__(self):
		ModulesAccess.add('BaseObjectDisplay', self)
		self.__size = (mainLayoutSize['leftMenuWidth'], mainLayoutSize['leftMenuWidth'])
		self.__layout = BoxLayout(orientation = 'horizontal', size = self.__size, size_hint = (1.0, None))
		self.__currentObject = None

	def setDisplay(self, obj):
		assert isinstance(obj, BaseObject), 'Error, object must be a BaseObject.'
		if (self.__currentObject != obj):
			self.__layout.clear_widgets()
			self.__layout.add_widget(
				Image(texture = obj.getBaseImage().texture, size = self.__size, size_hint = (None, None))
			)
			self.__currentObject = obj
			# TODO: Add the descriptor update here!
		else:
			# TODO: Add drawning here!
			pass

class OptionMenuTree(TreeView):
	def __processTouchDown(self, touch):
		if (self.collide_point(*touch.pos) == True and touch.button == 'left'):
			self.__defaultTouchDown(touch)

	def __processTouchUp(self, touch):
		if (self.collide_point(*touch.pos) == True and touch.button == 'left'):
			self.__defaultTouchUp(touch)

	def __processTouchMove(self, touch):
		if (self.collide_point(*touch.pos) == True and touch.button == 'left'):
			self.__defaultTouchMove(touch)

	def __init__(self, **kwargs):
		super(OptionMenuTree, self).__init__(**kwargs)
		self.__defaultTouchDown = self.on_touch_down
		self.__defaultTouchUp = self.on_touch_up
		self.__defaultTouchMove = self.on_touch_move

		self.on_touch_down = self.__processTouchDown
		self.on_touch_up = self.__processTouchUp
		self.on_touch_move = self.__processTouchMove

class OptionMenuLabel(TreeViewLabel, IgnoreTouch):
	def __updateDisplay(self, touch):
		if (self.collide_point(*touch.pos) == True):
			if(touch.is_double_tap == True and touch.button == 'left'):
				ModulesAccess.get('BaseObjectDisplay').setDisplay(self.__baseObject)

	def __init__(self, obj, **kwargs):
		assert isinstance(obj, BaseObject), 'Error, object must be a BaseObject.'
		super(self.__class__, self).__init__(**kwargs)
		self.__baseObject = obj
		self.on_touch_up = self.__updateDisplay
		self.on_touch_down = self._ignoreTouch
		self.on_touch_move = self._ignoreTouch

class NewBaseObjectsMenu(LayoutGetter):
	#def __reloadMenuList(self):
	#	self.__numberOfItems = len(self.__menuObjectsList)
	#	self.__objectListLayout.clear_widgets()
	#	self.__objectListLayout.rows = self.__numberOfItems
	#	self.__objectListLayout.size[1] = (self.__numberOfItems * 67)
	#	for menuObjectItem in self.__menuObjectsList:
	#		self.__objectListLayout.add_widget(menuObjectItem.getDisplayImage())

	def __createTruncateFilename(self, fullname):
		relativePath = relpath(fullname, getcwd())
		dirs, filename = split(relativePath)
		dirParts = []
		for name in dirs.split(pathSeparator):
			dirParts.append(name[0])
		dirParts.append(filename)
		return pathSeparator.join(dirParts)

	def __loadPng(self, item):
		path = join(getcwd(), 'tiles', item)
		img = Image(source = path)
		baseObject = BaseObject(img, self.__baseObjectId)
		self.__baseObjectsList.append(baseObject)
		self.__tree.add_node(OptionMenuLabel(baseObject, text = self.__createTruncateFilename(path)))
		self.__baseObjectId += 1

	def __loadResourceInfoList(self, resourceInfo):
		l = []
		mainImage = Image (source = resourceInfo.getPath())
		l.append(BaseObject(mainImage, self.__baseObjectId))
		self.__baseObjectId += 1

		spriteSize = tuple(mainImage.texture.size)
		for selection in resourceInfo.getSelectionList():
			x = selection.getX()
			y = selection.getY()
			width = selection.getSizeX()
			height = selection.getSizeY()
			image = createSpriteImage(mainImage, x, y, width, height)
			obj = BaseObject(image, self.__baseObjectId, resourceInfo.getPath(), (x, y), spriteSize)
			l.append(obj)
			self.__baseObjectId += 1

		return l

	def __loadOpf(self, item, pngsToIgnoreList):
		resourceInfo = SplittedImageImporter.load(join(getcwd(), 'tiles',item))

		# Main object
		mainImage = Image (source = resourceInfo.getPath())
		mainBaseObject = BaseObject(mainImage, self.__baseObjectId)
		self.__baseObjectId += 1
		self.__baseObjectsList.append(mainBaseObject)
		newNode = self.__tree.add_node(
			OptionMenuLabel(mainBaseObject, text = self.__createTruncateFilename(mainBaseObject.getPath()))
		)

		# Sprites
		spriteSize = tuple(mainImage.texture.size)
		for selection in resourceInfo.getSelectionList():
			x = selection.getX()
			y = selection.getY()
			width = selection.getSizeX()
			height = selection.getSizeY()
			image = createSpriteImage(mainImage, x, y, width, height)
			baseObject = BaseObject(image, self.__baseObjectId, resourceInfo.getPath(), (x, y), spriteSize)
			self.__baseObjectId += 1
			self.__baseObjectsList.append(baseObject)
			finalFilename = 'Pos: (' + str(x) + ', '  + str(y) + ') | Size: (' + str(width) + ', ' + str(height) + ')'
			self.__tree.add_node(OptionMenuLabel(baseObject, text = finalFilename, shorten = True,
				shorten_from = 'left', split_str = '('), newNode)

		pngsToIgnoreList.append(split(resourceInfo.getPath())[1])

	def __loadItems(self):
		l = listdir(join(getcwd(), 'tiles'))
		self.__baseObjectsList = []
		self.__baseObjectId = 0
		pngsToIgnoreList = []
		for item in l:
			if (item[-4:] == '.opf'):
				self.__loadOpf(item, pngsToIgnoreList)

		for item in l:
			if (item[-4:] == '.png' and item not in pngsToIgnoreList):
				self.__loadPng(item)

	def __adjustTreeSize(self, *args):
		self.__layout.size[1] = self.__tree.minimum_height

	def __init__(self):
		ModulesAccess.add('BaseObjectsMenu', self)
		self.__tree = OptionMenuTree(root_options = { 'text' : 'Resources'})
		self.__layout = ScrollView(size_hint = (1.0, 1.0), do_scroll = (0, 1), effect_cls = EmptyScrollEffect)
		self.__loadItems()
		self.__scrollLayout = RelativeLayout(width = mainLayoutSize['leftMenuWidth'], size_hint = (1.0, None))
		self.__scrollLayout.add_widget(self.__tree)
		self.__layout.add_widget(self.__scrollLayout)
		self.__tree.bind(minimum_height=self.__adjustTreeSize)

