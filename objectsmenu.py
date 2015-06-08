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
from editorutils import EmptyScrollEffect, createSpriteImage, AlignedLabel
from communicationobjects import SceneToObjectsMenu
from splittedimagemap import SplittedImageImporter
from modulesaccess import ModulesAccess
from uisizes import mainLayoutSize, descriptorLabelDefault
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
		self._displaySize = (mainLayoutSize['leftMenuWidth'], mainLayoutSize['leftMenuWidth'])
		totalSize = (self._displaySize[0], self._displaySize[1] + descriptorLabelDefault['height'])
		self._layout = BoxLayout(orientation = 'vertical', size = totalSize, size_hint = (1.0, None))
		self._nameLabel =  AlignedLabel(text = 'Preview', **descriptorLabelDefault)
		self._currentObject = None
		self._layout.add_widget(self._nameLabel)
		self._layout.add_widget(Image(size = self._displaySize))

	def setDisplay(self, obj, draw = True):
		assert isinstance(obj, BaseObject), 'Error, object must be a BaseObject.'
		if (self._currentObject != obj):
			self._layout.clear_widgets()
			self._layout.add_widget(self._nameLabel)
			self._layout.add_widget(
				Image(texture = obj.getBaseImage().texture, size = self._displaySize, size_hint = (None, None))
			)
			self._currentObject = obj
			ModulesAccess.get('ObjectDescriptor').set(obj)
		elif (draw == True):
			ModulesAccess.get('SceneHandler').draw(self._currentObject)

class OptionMenuTree(TreeView):
	def __processTouchDown(self, touch):
		if (touch.button == 'left'):
			self.__defaultTouchDown(touch)

	def __processTouchUp(self, touch):
		if (touch.button == 'left'):
			self.__defaultTouchUp(touch)

	def __processTouchMove(self, touch):
		if (touch.button == 'left'):
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
	def setDisplay(self, draw = True):
		ModulesAccess.get('BaseObjectDisplay').setDisplay(self.__baseObject, draw)

	def __updateDisplay(self, touch):
		if (self.collide_point(*touch.pos) == True and touch.button == 'left'):
			self.setDisplay()

	def __init__(self, obj, **kwargs):
		assert isinstance(obj, BaseObject), 'Error, object must be a BaseObject.'
		super(self.__class__, self).__init__(**kwargs)
		self.__baseObject = obj
		self.on_touch_up = self.__updateDisplay

class NewBaseObjectsMenu(LayoutGetter):
	#def __reloadMenuList(self):
	#	self.__numberOfItems = len(self.__menuObjectsList)
	#	self.__objectListLayout.clear_widgets()
	#	self.__objectListLayout.rows = self.__numberOfItems
	#	self.__objectListLayout.size[1] = (self.__numberOfItems * 67)
	#	for menuObjectItem in self.__menuObjectsList:
	#		self.__objectListLayout.add_widget(menuObjectItem.getDisplayImage())

	def _createTruncateFilename(self, fullname):
		relativePath = relpath(fullname, getcwd())
		dirs, filename = split(relativePath)
		dirParts = []
		for name in dirs.split(pathSeparator):
			dirParts.append(name[0])
		dirParts.append(filename)
		return pathSeparator.join(dirParts)

	def _loadPng(self, item):
		path = join(getcwd(), 'tiles', item)
		img = Image(source = path)
		baseObject = BaseObject(img, self._baseObjectId)
		self._baseObjectsList.append(baseObject)
		self._tree.add_node(OptionMenuLabel(baseObject, text = self._createTruncateFilename(path)))
		self._baseObjectId += 1

	def _loadResourceInfoList(self, resourceInfo):
		l = []
		mainImage = Image (source = resourceInfo.getPath())
		l.append(BaseObject(mainImage, self._baseObjectId))
		self._baseObjectId += 1

		spriteSize = tuple(mainImage.texture.size)
		for selection in resourceInfo.getSelectionList():
			x = selection.getX()
			y = selection.getY()
			width = selection.getSizeX()
			height = selection.getSizeY()
			image = createSpriteImage(mainImage, x, y, width, height)
			obj = BaseObject(image, self._baseObjectId, resourceInfo.getPath(), (x, y), spriteSize)
			l.append(obj)
			self._baseObjectId += 1

		return l

	def _loadOpf(self, item, pngsToIgnoreList):
		resourceInfo = SplittedImageImporter.load(join(getcwd(), 'tiles',item))

		# Main object
		mainImage = Image (source = resourceInfo.getPath())
		mainBaseObject = BaseObject(mainImage, self._baseObjectId)
		self._baseObjectId += 1
		self._baseObjectsList.append(mainBaseObject)
		newNode = self._tree.add_node(
			OptionMenuLabel(mainBaseObject, text = self._createTruncateFilename(mainBaseObject.getPath()))
		)

		# Sprites
		spriteSize = tuple(mainImage.texture.size)
		for selection in resourceInfo.getSelectionList():
			x = selection.getX()
			y = selection.getY()
			width = selection.getSizeX()
			height = selection.getSizeY()
			image = createSpriteImage(mainImage, x, y, width, height)
			baseObject = BaseObject(image, self._baseObjectId, resourceInfo.getPath(), (x, y), spriteSize)
			self._baseObjectId += 1
			self._baseObjectsList.append(baseObject)
			finalFilename = 'Pos: (' + str(x) + ', '  + str(y) + ') | Size: (' + str(width) + ', ' + str(height) + ')'
			self._tree.add_node(OptionMenuLabel(baseObject, text = finalFilename, shorten = True,
				shorten_from = 'left', split_str = '('), newNode)

		pngsToIgnoreList.append(split(resourceInfo.getPath())[1])

	def _loadItems(self):
		l = listdir(join(getcwd(), 'tiles'))
		self._baseObjectsList = []
		self._baseObjectId = 0
		pngsToIgnoreList = []
		for item in l:
			if (item[-4:] == '.opf'):
				self._loadOpf(item, pngsToIgnoreList)

		for item in l:
			if (item[-4:] == '.png' and item not in pngsToIgnoreList):
				self._loadPng(item)

	def _adjustTreeSize(self, *args):
		self._scrollLayout.size[1] = self._tree.minimum_height

	def updateSelection(self, command):
		assert command in ('up', 'down', 'left', 'right', 'leftright')
		if (self._tree.selected_node is None and len(self._tree.children) > 0):
			if (command == 'up'):
				self._tree.select_node(self._tree.children[0])
			elif (command == 'down'):
				self._tree.select_node(self._tree.children[-1])
		else:
			if (command in ('up', 'down')):
				if (command == 'up'):
					op = 1
				else:
					op = -1
				index = (self._tree.children.index(self._tree.selected_node) + op) % len(self._tree.children)
				self._tree.select_node(self._tree.children[index])
			else:
				if ('right' in command and self._tree.selected_node.is_open == False):
					self._tree.toggle_node(self._tree.selected_node)
				elif ('left' in command and self._tree.selected_node.is_open == True):
					self._tree.toggle_node(self._tree.selected_node)

		if (isinstance(self._tree.selected_node, OptionMenuLabel)):
			self._tree.selected_node.setDisplay(draw = False)

	def __init__(self):
		ModulesAccess.add('BaseObjectsMenu', self)
		self._tree = OptionMenuTree(root_options = { 'text' : 'Resources'})
		self._layout = ScrollView(size_hint = (1.0, 1.0), do_scroll = (0, 1), effect_cls = EmptyScrollEffect)
		self._loadItems()
		self._scrollLayout = RelativeLayout(width = mainLayoutSize['leftMenuWidth'], size_hint = (1.0, None))
		self._scrollLayout.add_widget(self._tree)
		self._layout.add_widget(self._scrollLayout)
		self._tree.bind(minimum_height=self._adjustTreeSize)

