from os.path import join, relpath, split, sep as pathSeparator
from os import listdir, getcwd

from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.treeview import TreeView, TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from editorobjects import BaseObject
from editorutils import EmptyScrollEffect, createSpriteImage, AlignedLabel
from splittedimagemap import SplittedImageImporter
from modulesaccess import ModulesAccess
from uisizes import mainLayoutSize, defaultLabelSize
from editorheritage import IgnoreTouch, LayoutGetter
from time import time

class TempScrollView(ScrollView):
	# This is a temporary class that implements the scroll to that is still on
	# the dev version only.
	def scroll_to(self, widget, padding=10, animate=True):
		from kivy.animation import Animation
		from kivy.metrics import sp, dp
		'''Scrolls the viewport to ensure that the given widget is visible,
		optionally with padding and animation. If animate is True (the
		default), then the default animation parameters will be used.
		Otherwise, it should be a dict containing arguments to pass to
		:class:`~kivy.animation.Animation` constructor.
		.. versionadded:: 1.9.1
		'''
		if not self.parent:
			return

		if isinstance(padding, (int, float)):
			padding = (padding, padding)

		pos = self.parent.to_widget(*widget.to_window(*widget.pos))
		cor = self.parent.to_widget(*widget.to_window(widget.right,
													  widget.top))

		dx = dy = 0

		if pos[1] < self.y:
			dy = self.y - pos[1] + dp(padding[1])
		elif cor[1] > self.top:
			dy = self.top - cor[1] - dp(padding[1])

		if pos[0] < self.x:
			dx = self.x - pos[0] + dp(padding[0])
		elif cor[0] > self.right:
			dx = self.right - cor[0] - dp(padding[0])

		dsx, dsy = self.convert_distance_to_scroll(dx, dy)
		sxp = min(1, max(0, self.scroll_x - dsx))
		syp = min(1, max(0, self.scroll_y - dsy))

		if animate:
			if animate is True:
				animate = {'d': 0.2, 't': 'out_quad'}
			Animation.stop_all(self, 'scroll_x', 'scroll_y')
			Animation(scroll_x=sxp, scroll_y=syp, **animate).start(self)
		else:
			self.scroll_x = sxp
			self.scroll_y = syp

	def __init__(self, **kwargs):
		super(TempScrollView, self).__init__(**kwargs)			

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

class NewBaseObjectDisplay(LayoutGetter):
	def __init__(self):
		ModulesAccess.add('BaseObjectDisplay', self)
		self._displaySize = (mainLayoutSize['leftMenuWidth'], mainLayoutSize['leftMenuWidth'])
		totalSize = (self._displaySize[0], self._displaySize[1] + defaultLabelSize['height'])
		self._layout = BoxLayout(orientation = 'vertical', size = totalSize, size_hint = (1.0, None))
		self._nameLabel =  AlignedLabel(text = 'Preview', **defaultLabelSize)
		self._currentObject = None
		self._layout.add_widget(self._nameLabel)
		self._layout.add_widget(Image(size = self._displaySize, color = (0, 0, 0, 0)))

	def setDisplay(self, obj, draw = True):
		assert obj is None or isinstance(obj, BaseObject), 'Error, object must be a BaseObject or None.'
		if (self._currentObject != obj or obj is None):
			self._layout.clear_widgets()
			self._layout.add_widget(self._nameLabel)
			if (obj is None):
				self._layout.add_widget(Image(size = self._displaySize, color = (0, 0, 0, 0)))
			else:
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

class OptionMenuImage(TreeViewNode, Image):
	def setDisplay(self, draw = True):
		ModulesAccess.get('BaseObjectDisplay').setDisplay(self.__baseObject, draw)

	def setResourceInfo(self, newValue):
		self.__resourceInfo = newValue

	def __updateDisplay(self, touch):
		if (self.collide_point(*touch.pos) == True and touch.button == 'left'):
			self.setDisplay()

	def getResourceInfo(self):
		return self.__resourceInfo

	def getBaseObject(self):
		return self.__baseObject

	def getSelection(self):
		return self.__selection

	def isNodeToUpdate(self, resourceInfo):
		if (self.__selection is None and self.__baseObject.getPath()[:-4] == resourceInfo.getPath()[:-4]):
			return True
		else:
			return False

	def __init__(self, obj, resourceInfo = None, selection = None):
		assert isinstance(obj, BaseObject), 'Error, object must be a BaseObject.'
		super(self.__class__, self).__init__(texture = obj.getBaseImage().texture, size = (32, 32))
		self.__baseObject = obj
		self.__resourceInfo = resourceInfo
		self.__selection = selection
		self.on_touch_up = self.__updateDisplay

class NewBaseObjectsMenu(LayoutGetter, IgnoreTouch):
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
		self._tree.add_node(OptionMenuImage(baseObject))
		self._baseObjectId += 1

	def _createAndAddBaseObject(self, newNode, selection, mainImage, spriteSize, path):
		x = selection.getX()
		y = selection.getY()
		width = selection.getSizeX()
		height = selection.getSizeY()
		image = createSpriteImage(mainImage, x, y, width, height)
		baseObject = BaseObject(image, self._baseObjectId, path, (x, y), spriteSize)
		self._baseObjectId += 1
		self._baseObjectsList.append(baseObject)
		self._tree.add_node(OptionMenuImage(baseObject, selection = selection), newNode)

	def _loadSubitems(self, newNode, resourceInfo, mainImage, spriteSize):
		for selection in resourceInfo.getSelectionList():
			self._createAndAddBaseObject(newNode, selection, mainImage, spriteSize, resourceInfo.getPath())

	def _loadOpf(self, item, pngsToIgnoreList):
		resourceInfo = SplittedImageImporter.load(join(getcwd(), 'tiles', item))

		# Main object
		mainImage = Image (source = resourceInfo.getPath())
		mainBaseObject = BaseObject(mainImage, self._baseObjectId)
		self._baseObjectId += 1
		self._baseObjectsList.append(mainBaseObject)
		newNode = self._tree.add_node(OptionMenuImage(mainBaseObject, resourceInfo = resourceInfo))

		# Sprites
		spriteSize = tuple(mainImage.texture.size)
		self._loadSubitems(newNode, resourceInfo, mainImage, spriteSize)

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

	def __scrollUpdate(self, dt):
		self._layout.scroll_to(self._tree.selected_node)

	def _adjustTreeSize(self, *args):
		self._scrollLayout.size[1] = self._tree.minimum_height
		if (self._tree.selected_node is not None):
			Clock.schedule_once(self.__scrollUpdate, 0)

	def __doUpdateResource(self, node, newResourceInfo):
		oldResourceInfo = node.getResourceInfo()
		mainImage = node.getBaseObject().getBaseImage()
		spriteSize = node.getBaseObject().getSize()
		path = newResourceInfo.getPath()
		if (oldResourceInfo is None):
			self._loadSubitems(node, newResourceInfo, mainImage, spriteSize)
		else:
			for childNode in node.nodes[:]:
				if (newResourceInfo.hasSame(childNode.getSelection()) == False):
					self._tree.remove_node(childNode)

			for selection in newResourceInfo.getSelectionList():
				if (oldResourceInfo.hasSame(selection) == False):
					self._createAndAddBaseObject(node, selection, mainImage, spriteSize, path)

		node.setResourceInfo(newResourceInfo)

	def updateResource(self, newResourceInfo):
		for item in self._tree.children:
			if item.isNodeToUpdate(newResourceInfo) == True:
				self.__doUpdateResource(item, newResourceInfo)
				self.__recentlyUpdated = (newResourceInfo.getPath(), time())
				break

	def updateSelectedNode(self, command):
		assert command in ('up', 'down', 'left', 'right', 'leftright')
		if (self._tree.selected_node is None and len(self._tree.children) > 0):
			if (command == 'up'):
				self._tree.select_node(self._tree.children[0])
				self._layout.scroll_to(self._tree.children[0])
			elif (command == 'down'):
				self._tree.select_node(self._tree.children[-1])
				self._layout.scroll_to(self._tree.children[-1])
		else:
			if (command in ('up', 'down')):
				if (command == 'up'):
					op = 1
				else:
					op = -1
				index = (self._tree.children.index(self._tree.selected_node) + op) % len(self._tree.children)
				self._tree.select_node(self._tree.children[index])
				self._layout.scroll_to(self._tree.children[index])
			else:
				if ('right' in command and self._tree.selected_node.is_open == False):
					self._tree.toggle_node(self._tree.selected_node)
					self._layout.scroll_to(self._tree.selected_node)
				elif ('left' in command and self._tree.selected_node.is_open == True):
					self._tree.toggle_node(self._tree.selected_node)
					self._layout.scroll_to(self._tree.selected_node)

		if (isinstance(self._tree.selected_node, OptionMenuImage)):
			self._tree.selected_node.setDisplay(draw = False)

	def __processTouchDown(self, touch):
		if (touch.button != 'scrollup' and touch.button != 'scrolldown'):
			return self.__defaultTouchDown(touch)

	def __processTouchUp(self, touch):
		if (touch.button != 'scrollup' and touch.button != 'scrolldown'):
			return self.__defaultTouchUp(touch)

	def __processTouchMove(self, touch):
		if (touch.button != 'scrollup' and touch.button != 'scrolldown'):
			return self.__defaultTouchMove(touch)

	def __init__(self):
		ModulesAccess.add('BaseObjectsMenu', self)
		self._tree = OptionMenuTree(root_options = { 'text' : 'Resources'})
		self._layout = TempScrollView(size_hint = (1.0, 1.0), do_scroll = (0, 1), effect_cls = EmptyScrollEffect)
		self._loadItems()
		self._scrollLayout = RelativeLayout(width = mainLayoutSize['leftMenuWidth'], size_hint = (1.0, None))
		self._scrollLayout.add_widget(self._tree)
		self._layout.add_widget(self._scrollLayout)
		self._tree.bind(minimum_height=self._adjustTreeSize)

		self.__defaultTouchDown = self._layout.on_touch_down
		self.__defaultTouchUp = self._layout.on_touch_up
		self.__defaultTouchMove = self._layout.on_touch_move
		self._layout.on_touch_down = self.__processTouchDown
		self._layout.on_touch_up = self.__processTouchUp
		self._layout.on_touch_move = self.__processTouchMove

