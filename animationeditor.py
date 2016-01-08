from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.clock import Clock
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color

from keyboard import KeyboardAccess, KeyboardGuardian
from editorutils import EmptyScrollEffect, SeparatorLabel, AlignedLabel, CancelableButton
from editorheritage import LayoutGetter
from modulesaccess import ModulesAccess
from splittedimagemap import SpriteSelection, SplittedImageImporter
from uisizes import defaultLabelSize, defaultFontSize, defaultSmallButtonSize, defaultLineSize

class AnimationBaseScroll(object):
	def _touchInside(self, touch):
		return self._layout.collide_point(*touch.pos)

	def _processTouchUp(self, touch):
		if (touch.button == "right"):
			self._defaultTouchUp(touch)
		return False

	def _processTouchMove(self, touch):
		if (touch.button == "right"):
			self._defaultTouchMove(touch)
		return False

	def _processTouchDown(self, touch):
		if (touch.button == "right"):
			self._defaultTouchDown(touch)
		return False

	def __init__(self):
		super(AnimationBaseScroll, self).__init__()
		self._defaultTouchUp = self._layout.on_touch_up
		self._defaultTouchMove = self._layout.on_touch_move
		self._defaultTouchDown = self._layout.on_touch_down
		self._layout.on_touch_up = self._processTouchUp
		self._layout.on_touch_move = self._processTouchMove
		self._layout.on_touch_down = self._processTouchDown

class Frame:
	def __init__(self, sf):
		assert isinstance(sf, SelectableFrame), "Invalid parameter received!"
		self.__duration = None
		self.__image = sf.getRealImage()

	def getDuration(self):
		return self.__duration

	def setDuration(self, newDuration):
		self.__duration = newDuration

	def getImage(self):
		return self.__image

class Animation:
	def __init__(self, name):
		self.__name = name
		self.__frames = []

	def addFrame(self, frame):
		assert isinstance(frame, Frame), "Invalid parameter received!"
		self.__frames.append(frame)

	def getFrames(self):
		return self.__frames

class AnimationLink:
	def __init__(self, source, destination, priority = 8, property = None):
		self.__source = source
		self.__destination = destination
		self.__priority = priority
		self.__property = property

class SelectableFrame:
	def __init__(self, base,  pos, size):
		self.texture = base.texture.get_region(pos[0], pos[1], size[0], size[1])
		self.__size = size
		self.__displayImage = Image(texture = self.texture, size = (64, 64))

	def getDisplayImage(self):
		return self.__displayImage

	def getRealImage(self):
		return Image(texture = self.texture, size = self.__size)

class AnimationNode(TreeViewLabel):
	def __init__(self, name):
		self.__animation = Animation(name)
		super(AnimationNode, self).__init__(text = name)

	def getAnimation(self):
		return self.__animation

class AnimationHandler(LayoutGetter):
	def selectNode(self, node):
		if (isinstance(node, AnimationNode)):
			ModulesAccess.get("AnimationDisplay").setAnimation(node.getAnimation())
			ModulesAccess.get("AnimationFrameDisplay").setAnimation(node.getAnimation())
		else:
			ModulesAccess.get("AnimationDisplay").unsetAnimation()
			ModulesAccess.get("AnimationFrameDisplay").unsetAnimation()

		self.__defaultSelectNode(node)

	def __init__(self):
		self.__defaultName = 'NewAnimation'
		self._layout = ScrollView(do_scroll = (0, 1), effect_cls = EmptyScrollEffect, width = 200,
			size_hint = (None, 1.0))
		self._scrollLayout = TreeView(root_options = { 'text' : 'Animations'})
		self._layout.add_widget(self._scrollLayout)
		self.__defaultSelectNode = self._scrollLayout.select_node
		self._scrollLayout.select_node = self.selectNode

		ModulesAccess.add('AnimationHandler', self)

	def addFrameToCurrentAnimation(self, sf):
		node = self._scrollLayout.selected_node
		if (node is not None and node != self._scrollLayout.root):
			animation = node.getAnimation()
			animation.addFrame(Frame(sf))
			ModulesAccess.get("AnimationDisplay").updateAnimation()
			ModulesAccess.get("AnimationFrameDisplay").updateAnimation()

	def createNewAnimation(self, *args):
		count = 0
		lenToUse = len(self.__defaultName)
		for node in self._scrollLayout.children:
			if (node.text[0:lenToUse] == self.__defaultName and len(node.text) > lenToUse):
				newCount = int(node.text[lenToUse:])
				if (newCount > count):
					count = newCount
		count += 1
		an = AnimationNode(self.__defaultName + str(count))
		self._scrollLayout.add_node(an)
		self._scrollLayout.select_node(an)

class AnimationDisplay(LayoutGetter):
	def __init__(self):
		self._layout = ScrollView(effect_cls = EmptyScrollEffect)
		self._scrollLayout = BoxLayout(orientation = 'horizontal', size_hint = (1, 1))
		self._layout.add_widget(self._scrollLayout)
		self.__currentAnimation = None
		self.__index = None
		ModulesAccess.add('AnimationDisplay', self)

	def __scheduleTick(self):
		duration = self.__currentAnimation.getFrames()[self.__index].getDuration()
		if (duration is None):
			duration = 1.0
		Clock.schedule_once(self.__tickAnimation, duration)

	def __tickAnimation(self, *args):
		self._scrollLayout.clear_widgets()
		frames = self.__currentAnimation.getFrames()
		self.__index = (self.__index + 1) % len(frames)
		self._scrollLayout.add_widget(frames[self.__index].getImage())
		self.__scheduleTick()

	def setAnimation(self, animation):
		assert isinstance(animation, Animation), "Invalid argument received!"
		self.__currentAnimation = animation
		self.__index = None
		self.updateAnimation()

	def unsetAnimation(self):
		Clock.unschedule(self.__tickAnimation)
		self._scrollLayout.clear_widgets()
		self.__index = None
		self.__currentAnimation = None

	def updateAnimation(self):
		assert self.__currentAnimation is not None, "Invalid State!"

		Clock.unschedule(self.__tickAnimation)
		self._scrollLayout.clear_widgets()
		frames = self.__currentAnimation.getFrames()
		if (len(frames) > 0):
			x, y = -1, -1
			for frame in frames:
				size = frame.getImage().size
				if (size[0] > x):
					x = size[0]
				if (size[1] > y):
					y = size[1]
			self._scrollLayout.size = (x, y)

		if (len(frames) >= 1):
			self._scrollLayout.add_widget(frames[0].getImage())
			if (len(frames) > 1):
				self.__index = 0
				self.__scheduleTick()

class FramePreview:
	def __init__(self, frame):
		assert isinstance(frame, Frame), "Invalid argument received."
		self.__frameRef = frame
		self.__image = Image(
			texture = frame.getImage().texture,
			size = (198, 198)
		)
		self.__operation = None

	def getImage(self):
		return self.__image

	def getOriginalFrame(self):
		return self.__frameRef

	def select(self):
		with self.__image.canvas:
			Color(1., 0., 0.)
			sx, sy = self.__image.size
			px, py = self.__image.pos
			self.__operation = Line(points = [
				px + 1, py,
				px + sx, py,
				px + sx, py + sy - 1,
				px, py + sy - 1,
				px + 1, py])

	def unselect(self):
		self.__image.canvas.remove(self.__operation)
		self.__operation = None

class FrameDisplay(AnimationBaseScroll, LayoutGetter):
	def _processTouchDown(self, touch):
		if (self._touchInside(touch) == False):
			return False

		if (touch.button == "right"):
			self._defaultTouchDown(touch)
		elif (touch.button == "left"):
			pos = self._layout.to_local(*touch.pos)
			for fp in self.__framesList:
				if (fp.getImage().collide_point(*pos) == True):
					if (self.__frameSelected is not None):
						self.__frameSelected.unselect()
					fp.select()
					self.__frameSelected = fp
					return False

		return False

	def __init__(self):
		self._layout = ScrollView(size_hint = (1.0, None), do_scroll = (1, 0), effect_cls = EmptyScrollEffect,
			height = 200)
		self._scrollLayout = BoxLayout(orientation = 'horizontal', height = 200, size_hint = (None, None))
		self._layout.add_widget(self._scrollLayout)
		super(FrameDisplay, self).__init__()
		ModulesAccess.add('AnimationFrameDisplay', self)
		self.__currentAnimation = None
		self.__framesList = []
		self.__frameSelected = None

	def setAnimation(self, animation):
		self.__currentAnimation = animation
		self._scrollLayout.clear_widgets()
		self.__framesList = []
		for frame in animation.getFrames():
			fp = FramePreview(frame)
			self.__framesList.append(fp)
			self._scrollLayout.add_widget(fp.getImage())

		self._scrollLayout.width = len(self.__framesList) * 200

	def unsetAnimation(self):
		self._scrollLayout.clear_widgets()
		self._scrollLayout.width = 1
		self.__framesList = []
		self.__currentAnimation = None
		self.__frameSelected = None

	def updateAnimation(self):
		frames =  self.__currentAnimation.getFrames()
		curIndex = len(self.__framesList)
		index = len(frames)
		if (index > curIndex):
			while index > curIndex:
				fp = FramePreview(frames[curIndex])
				self.__framesList.append(fp)
				self._scrollLayout.add_widget(fp.getImage())
				curIndex += 1

		self._scrollLayout.width = len(self.__framesList) * 200

class AnimationAndFrameEditor(LayoutGetter, SeparatorLabel):
	def __init__(self):
		super(AnimationAndFrameEditor, self).__init__()
		self._layout = BoxLayout(orientation = 'vertical', height = 100, size_hint = (1.0, None))
		buttonBox = BoxLayout(orientation = 'horizontal')

		self._durationLabel = AlignedLabel(text = 'Duration: ')
		copyLeftButton = CancelableButton(text = 'Copy left', **defaultSmallButtonSize)
		copyRightButton = CancelableButton(text = 'Copy right', **defaultSmallButtonSize)
		moveLeftButton = CancelableButton(text = 'Move left', **defaultSmallButtonSize)
		moveRightButton = CancelableButton(text = 'Move right', **defaultSmallButtonSize)

		self._layout.add_widget(self._durationLabel)
		self._layout.add_widget(self.getSeparator())
		buttonBox.add_widget(copyLeftButton)
		buttonBox.add_widget(copyRightButton)
		buttonBox.add_widget(moveLeftButton)
		buttonBox.add_widget(moveRightButton)
		self._layout.add_widget(buttonBox)

class FrameEditor(AnimationBaseScroll, LayoutGetter):
	def _processTouchDown(self, touch):
		if (touch.button == "right"):
			self._defaultTouchDown(touch)
		elif (touch.button == "left" and touch.is_double_tap == True):
			pos = self._layout.to_local(*touch.pos)
			for sf in self.__objectsList:
				if (sf.getDisplayImage().collide_point(*pos) == True):
					ModulesAccess.get("AnimationHandler").addFrameToCurrentAnimation(sf)
					return False

		return False

	def __init__(self):
		self._layout = ScrollView(do_scroll = (0, 1), effect_cls = EmptyScrollEffect, width = 200,
			size_hint = (None, 1.0))
		self._scrollLayout = BoxLayout(orientation = 'vertical', size_hint = (None, None), size = (200, 100))

		super(FrameEditor, self).__init__()
		self._layout.add_widget(self._scrollLayout)

	def load(self, resourceInfo):
		self.__objectsList = []
		im = Image(source = resourceInfo.getPath())
		self._scrollLayout.clear_widgets()
		layoutHeight = 0
		for selection in resourceInfo.getSelectionList():
			pos = (selection.getX(), selection.getY())
			size = (selection.getSizeX(), selection.getSizeY())
			sf = SelectableFrame(im, pos, size)
			self.__objectsList.append(sf)
			self._scrollLayout.add_widget(sf.getDisplayImage())
			layoutHeight += 67

		self._scrollLayout.height = layoutHeight

	def addFrame(self, *args):
		for sf in self.__objectsList:
			if (sf.isSelected() == True):
				ModulesAccess.get('AnimationHandler').addFrameToCurrentAnimation(sf)
				return

class AnimationEditor(KeyboardAccess, SeparatorLabel, LayoutGetter):
	def __init__(self):
		super(AnimationEditor, self).__init__()
		self._layout = BoxLayout(orientation = 'horizontal')
		self.__frameEditor = FrameEditor()
		self.__animationDisplay = AnimationDisplay()
		self.__frameDisplay = FrameDisplay()
		self.__animationAndFrame = AnimationAndFrameEditor()
		self.__animationTree = AnimationHandler()

		leftMenu = BoxLayout(orientation = 'vertical', size_hint = (None, 1), width = 200)
		self._cancelButton = CancelableButton(text = 'Cancel', on_release = self.close,
			**defaultLineSize)
		self._doneButton = CancelableButton(text = 'Done', on_release = self.save,
			**defaultLineSize)
		leftMenu.add_widget(AlignedLabel(text = 'Frames:', **defaultLabelSize))
		leftMenu.add_widget(self.__frameEditor.getLayout())
		leftMenu.add_widget(self._doneButton)
		leftMenu.add_widget(self._cancelButton)

		middleBox = BoxLayout(orientation = 'vertical', size_hint = (1, 1))
		middleBox.add_widget(AlignedLabel(text = 'Animation Preview:', **defaultLineSize))
		middleBox.add_widget(self.__animationDisplay.getLayout())
		middleBox.add_widget(AlignedLabel(text = 'Animation Frames:', **defaultLineSize))
		middleBox.add_widget(self.__frameDisplay.getLayout())
		middleBox.add_widget(AlignedLabel(text = 'Frame Data:', **defaultLineSize))
		middleBox.add_widget(self.__animationAndFrame.getLayout())

		rightMenu = BoxLayout(orientation = 'vertical', size_hint = (None, 1), width = 200)
		rightMenu.add_widget(self.__animationTree.getLayout())
		self.__newAnimationButton = CancelableButton(text = 'New animation',
			on_release = self.__animationTree.createNewAnimation, **defaultLineSize)
		rightMenu.add_widget(self.__newAnimationButton)

		self._layout.add_widget(leftMenu)
		self._layout.add_widget(middleBox)
		self._layout.add_widget(rightMenu)

		self.__popup = Popup(
			title = 'Animation Editor',
			auto_dismiss = False,
			content = self._layout
		)

		ModulesAccess.add('AnimationEditor', self)

	def save(self, *args):
		self.close()

	def open(self, path):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__resourceInfo = SplittedImageImporter().load(path)
		self.__frameEditor.load(self.__resourceInfo)
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()
