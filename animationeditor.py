from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color

from os.path import basename

from keyboard import KeyboardAccess, KeyboardGuardian
from editorutils import EmptyScrollEffect, SeparatorLabel, AlignedLabel, CancelableButton, Alert, FloatInput,\
	Dialog, NumberInput, AlignedToggleButton, ChangesConfirm, AlignedToggleButtonLeftOnly
from editorheritage import LayoutGetter
from modulesaccess import ModulesAccess
from splittedimagemap import SplittedImageImporter, SplittedImageExporter
from uisizes import defaultLabelSize, defaultSmallButtonSize, defaultLineSize, defaultInputSize, animationStatsSize,\
	defaultLargeButtonSize, animationFrameDurationSize, defaultFontSize
from string import letters, digits
from spriteinfo import SingleIdentifiedObject, AnimationInfo, FrameInfo, LinkInfo
from editorobjects import resetAnitionOnObjectList

class AnimationBaseScroll(LayoutGetter):
	"""Class that implements the default behavior we want for a ScrollView, which is scrolling with the left button
	only."""
	def _touchInside(self, touch):
		return self._layout.collide_point(*touch.pos)

	def _processTouchUp(self, touch):
		if (touch.button == "right"):
			self._defaultTouchUp(touch)
			return True
		return False

	def _processTouchMove(self, touch):
		if (touch.button == "right"):
			self._defaultTouchMove(touch)
			return True
		return False

	def _processTouchDown(self, touch):
		if (touch.button == "right"):
			self._defaultTouchDown(touch)
			return True
		return False

	def __init__(self, **kwargs):
		super(AnimationBaseScroll, self).__init__()
		self._layout = ScrollView(**kwargs)
		self._defaultTouchUp = self._layout.on_touch_up
		self._defaultTouchMove = self._layout.on_touch_move
		self._defaultTouchDown = self._layout.on_touch_down
		self._layout.on_touch_up = self._processTouchUp
		self._layout.on_touch_move = self._processTouchMove
		self._layout.on_touch_down = self._processTouchDown

class Frame:
	"""Class that holds the information of a frame inside the animation."""
	def __init__(self, sf, duration = None):
		assert isinstance(sf, SelectableFrame), "Invalid parameter received!"
		self.__duration = duration
		self.__image = sf.getRealImage()
		self.__selectableFrameRef = sf
		self.__animationRef = None
		self.__selectionId = sf.getId()

	def hasDuration(self):
		return self.__duration is not None

	def getDuration(self):
		if (self.__duration is None):
			return self.__animationRef.getDuration()

		return self.__duration

	def setDuration(self, newDuration):
		self.__duration = newDuration

	def resetDuration(self):
		self.__duration = None

	def getImage(self):
		return self.__image

	def copy(self):
		return Frame(self.__selectableFrameRef, self.__duration)

	def setAnimation(self, animation):
		assert self.__animationRef is None, "Invalid state reached!"
		assert isinstance(animation, Animation), "Invalid parameter received!"
		self.__animationRef = animation

	def getAnimation(self):
		return self.__animationRef

	def getSelectionId(self):
		return self.__selectionId

class Animation(SingleIdentifiedObject):
	"""Class that holds the information an ORX animation.
	It holds a list of frames that are part of it, in an ORX context each Frame in the list is a KeyData entry in the
	final ini file.
	If a frame doesn't have a duration set, it will use the animation duration instead."""
	validCharacters = digits + letters + '_'
	@staticmethod
	def filterInvalidCharacters(name):
		l = []
		for c in name:
			if (c not in Animation.validCharacters):
				l.append(c)
		return ''.join(l)

	def __init__(self, name, duration = 1.0, identifier = None):
		super(Animation, self).__init__()
		self.__name = name
		self.__duration = duration
		self.__frames = []
		self._id = identifier

	def addFrame(self, frame, index = None, autoSetAnimation = True):
		assert isinstance(frame, Frame), "Invalid parameter received!"
		if (autoSetAnimation == True):
			frame.setAnimation(self)
		if (index is None):
			self.__frames.append(frame)
		else:
			self.__frames.insert(index, frame)

	def getFrames(self):
		return self.__frames

	def getDuration(self):
		return self.__duration

	def getName(self):
		return self.__name

	def setName(self, value):
		ModulesAccess.get('AnimationLinkDisplay').updateName(self.__name, value)
		self.__name = value

	def setDuration(self, value):
		self.__duration = value

	def swapFrames(self, fromIndex, toIndex):
		swap = self.__frames[fromIndex]
		self.__frames[fromIndex] = self.__frames[toIndex]
		self.__frames[toIndex] = swap

	def copyFrame(self, fromIndex, toIndex):
		copy = self.__frames[fromIndex].copy()
		self.addFrame(copy, toIndex)

	def resetFrameDuration(self, index):
		self.__frames[index].resetDuration()

	def setFrameDuration(self, index, duration):
		self.__frames[index].setDuration(duration)

	def getFrameDuration(self, index):
		return self.__frames[index].getDuration()

	def removeFrame(self, index):
		self.__frames.pop(index)

class DurationControl(object):
	def __init__(self, **kwargs):
		super(DurationControl, self).__init__()

	def controlDurationInput(self, key, textInput):
		if (key == 'down' and textInput.focus == True):
			try:
				duration = float(textInput.text)
				if (duration > 1.1):
					duration -= 1.0
				elif (duration > 0.1):
					duration -= 0.1
				textInput.text = str(duration)
			except:
				pass

		elif (key == 'up' and textInput.focus == True):
			try:
				duration = float(textInput.text)
				if (duration >= 1.0):
					duration += 1.0
				else:
					duration += 0.1
				textInput.text = str(duration)
			except:
				pass

class AnimationStatsEditor(SeparatorLabel, KeyboardAccess, ChangesConfirm, DurationControl):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'enter'):
			self.__processOk()

		elif (keycode[1] == 'escape'):
			self.alertExit()

		self.controlDurationInput(keycode[1], self.__durationInput)

	def __processOk(self, *args):
		invalidChars = Animation.filterInvalidCharacters(self.__nameInput.text)
		if (invalidChars != ''):
			Alert(
				title = 'Error',
				text = 'Invalid characters on animation name:\n' + invalidChars,
				closeButtonText = 'Ok'
			).open()
			return
		self.__currentAnimation.setName(self.__nameInput.text)

		try:
			duration = float(self.__durationInput.text)
			assert(duration > 0.0)
			self.__currentAnimation.setDuration(duration)
		except:
			Alert(
				title = 'Error',
				text = 'Duration entered is not valid.',
				closeButtonText = 'Ok'
			).open()
			return

		animations = ModulesAccess.get('AnimationHandler').getAnimations()
		for animation in animations:
			if (animation != self.__currentAnimation and animation.getName() == self.__nameInput.text):
				Alert(
					title = 'Error',
					text = 'Name is already in use.',
					closeButtonText = 'Ok'
				).open()
				return

		self.__okMethod(self.__currentAnimation)
		self.resetChanges()
		self.close()

	def __init__(self):
		super(AnimationStatsEditor, self).__init__()

		self.__popup = Popup(
			title = 'Animation Stats',
			auto_dismiss = False,
			**animationStatsSize
		)

		self._layout = BoxLayout(orientation = 'vertical')

		boxSizes = defaultInputSize.copy()

		nameBox = BoxLayout(orientation = 'horizontal', **boxSizes)
		self.__nameLabel = AlignedLabel(text = 'Name:', **defaultLabelSize)
		self.__nameInput = TextInput(text = '', multiline=False)
		nameBox.add_widget(self.__nameLabel)
		nameBox.add_widget(self.__nameInput)

		durationBox = BoxLayout(orientation = 'horizontal', **boxSizes)
		self.__durationLabel = AlignedLabel(text = 'Duration:', **defaultLabelSize)
		self.__durationInput = FloatInput(multiline = False, **defaultInputSize)
		durationBox.add_widget(self.__durationLabel)
		durationBox.add_widget(self.__durationInput)

		bottomButtonBox = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		okButton = CancelableButton(text = 'Ok', on_release = self.__processOk, **defaultSmallButtonSize)
		cancelButton = CancelableButton(text = 'Cancel', on_release = self.alertExit, **defaultSmallButtonSize)
		bottomButtonBox.add_widget(self.getSeparator())
		bottomButtonBox.add_widget(okButton)
		bottomButtonBox.add_widget(cancelButton)

		self.__nameInput.bind(text=self.registerChanges)
		self.__durationInput.bind(text=self.registerChanges)

		self._layout.add_widget(nameBox)
		self._layout.add_widget(durationBox)
		self._layout.add_widget(self.getSeparator())
		self._layout.add_widget(bottomButtonBox)

		self.__popup.content = self._layout
		self.__currentAnimation = None

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

	def open(self, animation, okMethod):
		assert isinstance(animation, Animation), "Invalid parameter received!"
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__nameInput.text = animation.getName()
		self.__nameInput.cursor = (0, 0)
		self.__durationInput.text = str(animation.getDuration())
		self.__currentAnimation = animation
		self.__okMethod = okMethod

		self.resetChanges()
		self.__popup.open()

class AnimationLink(SingleIdentifiedObject):
	"""Class that controls the animation links (which describes how ORX will go from one animation to the other)."""
	@staticmethod
	def copy(al):
		return AnimationLink(
			al.getSource(),
			al.getDestination(),
			al.getPriority(),
			al.getProperty(),
			al.getActive(),
			al.getId()
		)

	def __init__(self, source, destination, priority = 8, property = '', active = False, identifier = None):
		super(AnimationLink, self).__init__()
		self._source = source
		self._destination = destination
		self._priority = priority
		self._property = property
		self._active = active
		self._id = identifier

	def getSource(self):
		return self._source

	def getDestination(self):
		return self._destination

	def getSourceName(self):
		return self._source.getName()

	def getDestinationName(self):
		return self._destination.getName()

	def getProperty(self):
		return self._property

	def getActive(self):
		return self._active

	def setProperty(self, property):
		self._property = property

	def getPriority(self):
		return self._priority

	def setPriority(self, priority):
		self._priority = priority

	def setActive(self, value):
		self._active = value

class SelectableFrame:
	"""Class that holds the information of the left menu image.
	It holds a smaller version of the frame (used by the left menu) and a copy of the original message, that is used
	in the animation display."""
	def __init__(self, base, pos, size, id):
		# TODO: confirm if this is right
		self.__texture = base.texture.get_region(pos[0], pos[1], size[0] - 1, size[1] - 1)
		self.__size = size
		self.__displayImage = Image(texture = self.__texture, size = (64, 64))
		self.__id = id

	def getDisplayImage(self):
		return self.__displayImage

	def getRealImage(self):
		return Image(texture = self.__texture, size = self.__size)

	def getId(self):
		return self.__id

class AnimationNode(TreeViewLabel):
	"""Class that implements the node for the TreeView of the right menu and holds the animation it refers to."""
	def __init__(self, animation):
		assert isinstance(animation, Animation), "Invalid parameter received!"
		self.__originalName = animation.getName()
		self.__animation = animation
		super(AnimationNode, self).__init__(text = animation.getName())

	def getAnimation(self):
		return self.__animation

	def update(self):
		self.text = self.__animation.getName()

	def getOriginalName(self):
		return self.__originalName

class AnimationHandler(LayoutGetter):
	"""Class that implements the TreeView of the right menu, inside a scrollview. It is also reponsible to control the
	other components of the screen that show information of the animation and update the animations' information."""
	def __init__(self):
		self.__defaultName = 'NewAnimation'
		self._layout = ScrollView(do_scroll = (0, 1), effect_cls = EmptyScrollEffect, width = 200,
			size_hint = (None, 1.0))
		self._scrollLayout = TreeView(root_options = { 'text' : 'Animations'})
		self._layout.add_widget(self._scrollLayout)
		self.__defaultSelectNode = self._scrollLayout.select_node
		self._scrollLayout.select_node = self.selectNode
		self.__errorAlert = Alert("Error", "No animation selected.\nSelect one on the right menu.", "Ok")
		self.__animationStats = AnimationStatsEditor()
		self.__animations = []
		self.__deletedAnimations = []
		ModulesAccess.add('AnimationHandler', self)

	def load(self, resourceInfo):
		self.__deletedAnimations = []
		self.__animations = []
		self.unsetAnimation()
		for node in self._scrollLayout.children:
			self._scrollLayout.remove_node(node)

		for identifier, animationInfo in resourceInfo.getAnimationInfoItems():
			animation = Animation(animationInfo.getName(), animationInfo.getDuration(), animationInfo.getId())
			for frameInfo in animationInfo.getFramesInfo():
				sf = ModulesAccess.get('FrameEditor').getSelectableFrameBySelectionId(frameInfo.getId())
				animation.addFrame(Frame(sf, frameInfo.getDuration()))
			self.insertAnimation(animation)
		self._scrollLayout.select_node(self._scrollLayout.root)

	def updateAnimation(self):
		ModulesAccess.get('AnimationEditor').registerChanges()
		ModulesAccess.get("AnimationDisplay").updateAnimation()
		ModulesAccess.get("AnimationFrameDisplay").updateAnimation()

	def setAnimation(self, animation):
		assert isinstance(animation, Animation), "Invalid argument received!"
		ModulesAccess.get("AnimationDisplay").setAnimation(animation)
		ModulesAccess.get("AnimationFrameDisplay").setAnimation(animation)

	def unsetAnimation(self):
		ModulesAccess.get("AnimationDisplay").unsetAnimation()
		ModulesAccess.get("AnimationFrameDisplay").unsetAnimation()
		ModulesAccess.get("AnimationAndFrameEditor").unsetDuration()

	def selectNode(self, node):
		if (isinstance(node, AnimationNode)):
			self.setAnimation(node.getAnimation())
		else:
			self.unsetAnimation()

		self.__defaultSelectNode(node)

	def addFrameToCurrentAnimation(self, sf):
		node = self._scrollLayout.selected_node
		if (node is not None and node != self._scrollLayout.root):
			animation = node.getAnimation()
			animation.addFrame(Frame(sf))
			self.updateAnimation()
		else:
			self.__errorAlert.open()

	def insertAnimation(self, animation):
		self.__animations.append(animation)
		an = AnimationNode(animation)
		self._scrollLayout.add_node(an)
		self._scrollLayout.select_node(an)
		ModulesAccess.get('AnimationEditor').registerChanges()

	def editAnimation(self, animation):
		node = self._scrollLayout.selected_node
		root = self._scrollLayout.root
		assert node != root and node is not None and node.getAnimation() == animation, "Invalid parameter received!"
		node.update()
		self.updateAnimation()

	def removeAnimation(self):
		animation = self._scrollLayout.selected_node.getAnimation()
		self._scrollLayout.remove_node(self._scrollLayout.selected_node)
		self._scrollLayout.select_node(self._scrollLayout.root)
		self.__animations.remove(animation)
		self.__deletedAnimations.append(animation)
		ModulesAccess.get('AnimationEditor').registerChanges()

	def createNewAnimation(self, *args):
		count = 0
		lenToUse = len(self.__defaultName)
		for node in self._scrollLayout.children:
			if (node.text[0:lenToUse] == self.__defaultName and len(node.text) > lenToUse):
				try:
					newCount = int(node.text[lenToUse:]) # may not be and int
					if (newCount > count):
						count = newCount
				except:
					pass
		count += 1
		tempAnimation = Animation(self.__defaultName + str(count))
		self.__animationStats.open(tempAnimation, self.insertAnimation)

	def editCurrentAnimation(self, *args):
		node = self._scrollLayout.selected_node
		if (node is not None and node != self._scrollLayout.root):
			animation = node.getAnimation()
			self.__animationStats.open(animation, self.editAnimation)
		else:
			self.__errorAlert.open()

	def deleteCurrentAnimation(self, *args):
		node = self._scrollLayout.selected_node
		if (node is not None and node != self._scrollLayout.root):
			message = 'Are you sure that you want to remove\nthe selected animation?\n'
			objList = ModulesAccess.get('SceneHandler').getCurrentSceneObjects()
			name = node.getAnimation().getName()
			objCount = 0
			for obj in objList:
				objAnimation = obj.getAnimation()
				if (objAnimation is not None and objAnimation == name):
					objCount += 1

			if (objCount > 0):
				message += 'It will also reset the animation on %d object%s.\n' % \
					(objCount, 's' if objCount > 1 else '')

			message += 'This operation may not be reverted!'
			Dialog(
				title = 'Confirmation',
				text = message,
				okMethod = self.removeAnimation,
				dialogOkButtonText = 'Ok',
				dialogCancelButtonText = 'Cancel',
			).open()
		else:
			self.__errorAlert.open()

	def getAnimations(self):
		return self.__animations

	def getDeletedAnimations(self):
		return self.__deletedAnimations

	def getChangedNames(self):
		d = {}
		for node in self._scrollLayout.children:
			if (node != self._scrollLayout.root):
				animation = node.getAnimation()
				if (animation.getId() is not None and animation.getName() != node.getOriginalName()):
					d[node.getOriginalName()] = animation.getName()
		return d

class AnimationDisplay(LayoutGetter):
	"""Class that creates a visual display for an animation."""
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
			duration = self.__currentAnimation.getDuration()
		Clock.schedule_once(self.__tickAnimation, duration)

	def __tickAnimation(self, *args):
		self._scrollLayout.clear_widgets()
		frames = self.__currentAnimation.getFrames()
		self.__index = (self.__index + 1) % len(frames)
		self._scrollLayout.add_widget(frames[self.__index].getImage())
		self.__scheduleTick()

	def setAnimation(self, animation):
		assert isinstance(animation, Animation), "Invalid argument received!"
		self.unsetAnimation()
		self.__currentAnimation = animation
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
	"""Class that implements and controls the visual content of the FrameDisplay class."""
	def __init__(self, frame):
		assert isinstance(frame, Frame), "Invalid argument received."
		self.__frameRef = frame
		self.__image = Image(
			texture = frame.getImage().texture,
			size = (200, 200)
		)
		self.__operation = None

	def getImage(self):
		return self.__image

	def getOriginalFrame(self):
		return self.__frameRef

	def select(self, *args):
		with self.__image.canvas:
			Color(1., 0., 0.)
			sx, sy = self.__image.size
			px, py = self.__image.pos
			self.__operation = Line(points = [
				px, py + defaultFontSize,
				px + sx, py + defaultFontSize,
				px + sx, py + sy - 1,
				px, py + sy - 1,
				px, py + defaultFontSize])
		ModulesAccess.get("AnimationAndFrameEditor").setDuration(self.__frameRef.getDuration())

	def unselect(self, *args):
		self.__image.canvas.remove(self.__operation)
		self.__operation = None
		ModulesAccess.get("AnimationAndFrameEditor").unsetDuration()

class FrameDurationPopup(SeparatorLabel, ChangesConfirm, KeyboardAccess, DurationControl):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'enter'):
			self.__confirmDuration()

		if (keycode[1] == 'escape'):
			self.alertExit()

		self.controlDurationInput(keycode[1], self.__durationInput)

	def __init__(self, okMethod):
		super(FrameDurationPopup, self).__init__()

		self.__popup = Popup(
			title = 'Set Frame Duration',
			auto_dismiss = False,
			**animationFrameDurationSize
		)
		self.__okMethod = okMethod
		popupLayout = BoxLayout(orientation = 'vertical')
		lineBox = BoxLayout(orientation = 'horizontal', **defaultInputSize)
		lineBox.add_widget(AlignedLabel(text = 'Duration:', **defaultLineSize))
		self.__durationInput = FloatInput(multiline = False, **defaultInputSize)
		lineBox.add_widget(self.__durationInput)
		popupLayout.add_widget(lineBox)
		popupLayout.add_widget(self.getSeparator())
		bottomButtonBox = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		cancelButton = CancelableButton(text = 'Cancel', on_release = self.alertExit, **defaultSmallButtonSize)
		okButton = CancelableButton(text = 'Ok', on_release = self.__confirmDuration, **defaultSmallButtonSize)
		bottomButtonBox.add_widget(self.getSeparator())
		bottomButtonBox.add_widget(cancelButton)
		bottomButtonBox.add_widget(okButton)
		popupLayout.add_widget(bottomButtonBox)
		self.__popup.content = popupLayout
		self.__durationInput.bind(text=self.registerChanges)

	def __confirmDuration(self, *args):
		try:
			duration = float(self.__durationInput.text)
			assert duration > 0
		except:
			Alert(
				title = 'Error',
				text = 'Duration entered is not valid.',
				closeButtonText = 'Ok'
			).open()
			return

		self.__okMethod(duration)
		self.close()

	def open(self, duration):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__durationInput.text = str(duration)
		self.resetChanges()
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

class FrameDisplay(AnimationBaseScroll, SeparatorLabel):
	"""Class that implements a display to show each frame of the animation and allows the user to select one to be
	edited."""
	def _processTouchDown(self, touch):
		if (self._touchInside(touch) == False):
			return False

		if (touch.button == "right"):
			self._defaultTouchDown(touch)
		elif (touch.button == "left"):
			pos = self._layout.to_local(*touch.pos)
			for fp in self.__framePreviewDict.itervalues():
				if (fp.getImage().collide_point(*pos) == True):
					if (self.__frameSelected is not None):
						self.__frameSelected.unselect()
					fp.select()
					self.__frameSelected = fp
					return False

		return False

	def __findSelectedFrameIndex(self):
		frames = self.__currentAnimation.getFrames()
		index = 0
		for frame in frames:
			if (self.__framePreviewDict[frame] == self.__frameSelected):
				break
			index += 1
		return index

	def __getIndexOfSelectedFrameAndValidate(self, adj = 0, expand = 0):
		if (self.__frameSelected is None or self.__currentAnimation is None or self.__framePreviewDict == {}):
			return -1

		index = self.__findSelectedFrameIndex()
		frames = self.__currentAnimation.getFrames()
		assert index != len(frames), "Invalid state reached!"
		if (index + adj < 0 or index + adj >= len(frames) + expand):
			return -1

		return index

	def __copySelectedFrame(self, adj):
		index = self.__getIndexOfSelectedFrameAndValidate()
		if (adj < 0):
			adj += 1

		self.__currentAnimation.copyFrame(index, index + adj)
		ModulesAccess.get("AnimationHandler").updateAnimation()

	def __moveSelectedFrame(self, adj):
		index = self.__getIndexOfSelectedFrameAndValidate(adj)
		if (index == -1):
			return

		self.__currentAnimation.swapFrames(index, index + adj)
		ModulesAccess.get("AnimationHandler").updateAnimation()

	def __selectNextFrame(self, adj):
		index = self.__getIndexOfSelectedFrameAndValidate(adj)
		if (index == -1):
			return

		frames = self.__currentAnimation.getFrames()
		nextFrame = frames[index + adj]
		oldFrame = self.__frameSelected
		self.__frameSelected = self.__framePreviewDict[nextFrame]
		oldFrame.unselect()
		Clock.schedule_once(self.__frameSelected.select)

	def __confirmDuration(self, duration):
		index = self.__getIndexOfSelectedFrameAndValidate()
		self.__currentAnimation.setFrameDuration(index, duration)
		ModulesAccess.get("AnimationHandler").updateAnimation()

	def __removeFrame(self, *args):
		index = self.__getIndexOfSelectedFrameAndValidate()
		self.__frameSelected.unselect()
		self.__frameSelected = None
		frames = self.__currentAnimation.getFrames()
		del self.__framePreviewDict[frames[index]]
		self.__currentAnimation.removeFrame(index)
		ModulesAccess.get("AnimationHandler").updateAnimation()

	def __init__(self):
		super(FrameDisplay, self).__init__(size_hint = (1.0, None), do_scroll = (1, 0), height = 200,
			effect_cls = EmptyScrollEffect)
		self._scrollLayout = GridLayout(rows = 2, height = 220, size_hint = (None, None))
		self._layout.add_widget(self._scrollLayout)
		ModulesAccess.add('AnimationFrameDisplay', self)
		self.__currentAnimation = None
		self.__framePreviewDict = {}
		self.__frameSelected = None

		#confirming frame removal
		self.__deleteDialog = Dialog(
			title = 'Confirmation',
			text = 'Are you sure that you want to remove\nthe selected frame?\nThis operation may not be reverted!',
			okMethod = self.__removeFrame,
			dialogOkButtonText = 'Ok',
			dialogCancelButtonText = 'Cancel',
		)

		self.__durationPopup = FrameDurationPopup(self.__confirmDuration)

	def setAnimation(self, animation):
		assert isinstance(animation, Animation), "Invalid argument received!"
		self.unsetAnimation()
		self.__currentAnimation = animation
		self._scrollLayout.clear_widgets()
		self.__framePreviewDict = {}
		self.updateAnimation()

	def unsetAnimation(self):
		self._scrollLayout.clear_widgets()
		self._scrollLayout.width = 1
		self.__framePreviewDict = {}
		self.__currentAnimation = None
		if (self.__frameSelected is not None):
			self.__frameSelected.unselect()
		self.__frameSelected = None

	def updateAnimation(self):
		frames = self.__currentAnimation.getFrames()
		if (self.__frameSelected is not None):
			self.__frameSelected.unselect()

		self._scrollLayout.clear_widgets()
		self._scrollLayout.cols = len(frames)
		for frame in frames:
			self._scrollLayout.add_widget(Label(
				text = str(ModulesAccess.get('FrameEditor').getFrameCountById(frame.getSelectionId())),
				width = 200, height = defaultFontSize, size_hint = (None, None)
			))

		for frame in frames:
			if (frame not in self.__framePreviewDict):
				fp = FramePreview(frame)
				self.__framePreviewDict[frame] = fp
			else:
				fp = self.__framePreviewDict[frame]

			self._scrollLayout.add_widget(fp.getImage())
		self._scrollLayout.width = len(self.__framePreviewDict) * 200

		if (self.__frameSelected is not None):
			Clock.schedule_once(self.__frameSelected.select)

	def moveSelectedFrameLeft(self, *args):
		self.__moveSelectedFrame(-1)

	def moveSelectedFrameRight(self, *args):
		self.__moveSelectedFrame(1)

	def changeSelectedFrameLeft(self, *args):
		self.__selectNextFrame(-1)

	def changeSelectedFrameRight(self, *args):
		self.__selectNextFrame(1)

	def copySelectedFrameLeft(self, *args):
		self.__copySelectedFrame(-1)

	def copySelectedFrameRight(self, *args):
		self.__copySelectedFrame(1)

	def resetSelectedFrameDuration(self, *args):
		index = self.__getIndexOfSelectedFrameAndValidate()
		if (index != -1):
			self.__currentAnimation.resetFrameDuration(index)
			ModulesAccess.get("AnimationHandler").updateAnimation()

	def setSelectedFrameDuration(self, *args):
		index = self.__getIndexOfSelectedFrameAndValidate()
		if (index != -1):
			duration = self.__currentAnimation.getFrameDuration(index)
			self.__durationPopup.open(duration)

	def deleteSelectedFrame(self, *args):
		index = self.__getIndexOfSelectedFrameAndValidate()
		if (index != -1):
			self.__deleteDialog.open()

class AnimationAndFrameEditor(LayoutGetter, SeparatorLabel):
	"""Class that implements the bottom menu and allows the user to operate on a frame selected in the FrameDisplay
	class."""
	def __init__(self):
		super(AnimationAndFrameEditor, self).__init__()
		self._layout = BoxLayout(orientation = 'vertical', height = 100, size_hint = (1.0, None))
		copyButtonBox = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		moveButtonBox = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		frameButtonBox = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		bottomButtonBox = BoxLayout(orientation = 'horizontal', **defaultLineSize)

		self._durationBaseStr = 'Duration: '
		self._durationLabel = AlignedLabel(text = self._durationBaseStr, **defaultLineSize)
		copyLeftButton = CancelableButton(text = 'Copy left (c. left)',
			on_release = ModulesAccess.get('AnimationFrameDisplay').copySelectedFrameLeft,
			**defaultLargeButtonSize)
		copyRightButton = CancelableButton(text = 'Copy right (c. right)',
			on_release = ModulesAccess.get('AnimationFrameDisplay').copySelectedFrameRight,
			**defaultLargeButtonSize)
		moveLeftButton = CancelableButton(text = 'Move left (s left)',
			on_release = ModulesAccess.get('AnimationFrameDisplay').moveSelectedFrameLeft,
			**defaultLargeButtonSize)
		moveRightButton = CancelableButton(text = 'Move right (s. right)',
			on_release = ModulesAccess.get('AnimationFrameDisplay').moveSelectedFrameRight,
			**defaultLargeButtonSize)
		setDurationButton = CancelableButton(text = 'Set Duration (s)',
			on_release = ModulesAccess.get('AnimationFrameDisplay').setSelectedFrameDuration,
			**defaultLargeButtonSize)
		resetDurationButton = CancelableButton(text = 'Reset Duration (r)',
			on_release = ModulesAccess.get('AnimationFrameDisplay').resetSelectedFrameDuration,
			**defaultLargeButtonSize)
		deleteButton = CancelableButton(text = 'Delete Frame (del)',
			on_release = ModulesAccess.get('AnimationFrameDisplay').deleteSelectedFrame,
			**defaultLargeButtonSize)

		self._layout.add_widget(self._durationLabel)
		self._layout.add_widget(self.getSeparator())
		copyButtonBox.add_widget(copyLeftButton)
		copyButtonBox.add_widget(copyRightButton)
		moveButtonBox.add_widget(moveLeftButton)
		moveButtonBox.add_widget(moveRightButton)
		frameButtonBox.add_widget(setDurationButton)
		frameButtonBox.add_widget(resetDurationButton)
		bottomButtonBox.add_widget(deleteButton)
		self._layout.add_widget(copyButtonBox)
		self._layout.add_widget(moveButtonBox)
		self._layout.add_widget(frameButtonBox)
		self._layout.add_widget(bottomButtonBox)

		ModulesAccess.add("AnimationAndFrameEditor", self)

	def setDuration(self, duration):
		self._durationLabel.text = self._durationBaseStr + str(duration)

	def unsetDuration(self):
		self._durationLabel.text = self._durationBaseStr

class FrameEditor(AnimationBaseScroll):
	"""Class that implements the list of the available frames (each on is a SelectableFrame) in the left menu."""
	def _processTouchDown(self, touch):
		if (touch.button == "right"):
			self._defaultTouchDown(touch)
		elif (touch.button == "left" and touch.is_double_tap == True):
			pos = self._layout.to_local(*touch.pos)
			for sf in self.__selectableFrameDict.itervalues():
				if (sf.getDisplayImage().collide_point(*pos) == True):
					ModulesAccess.get("AnimationHandler").addFrameToCurrentAnimation(sf)
					return False

			for lbl in self.__labelList:
				if (lbl.collide_point(*pos) == True):
					ModulesAccess.get("AnimationHandler").addFrameToCurrentAnimation(
						self.__selectableFrameDict[int(lbl.id)]
					)
					return False

		return False

	def __init__(self):
		super(FrameEditor, self).__init__(do_scroll = (0, 1), effect_cls = EmptyScrollEffect, width = 200,
			size_hint = (None, 1.0))
		self._scrollLayout = GridLayout(cols = 2, size_hint = (None, None), size = (200, 100))
		self._layout.add_widget(self._scrollLayout)
		self._frameCountToSelectionId = {}
		ModulesAccess.add('FrameEditor', self)

	def load(self, resourceInfo):
		self.__selectableFrameDict = {}
		self.__labelList = []
		im = Image(source = resourceInfo.getPath())
		self._scrollLayout.clear_widgets()
		layoutHeight = 0
		self._scrollLayout.rows = resourceInfo.getNumberOfSelections()
		i = 0
		for identifier, selection in resourceInfo.getSelectionItems():
			pos = (selection.getX(), selection.getY())
			size = (selection.getSizeX(), selection.getSizeY())
			sf = SelectableFrame(im, pos, size, identifier)
			self.__selectableFrameDict[identifier] = sf
			label = AlignedLabel(text = str(i), size = (64, 64), size_hint = (None, None), id = str(identifier))
			self.__labelList.append(label)
			self._scrollLayout.add_widget(label)
			self._scrollLayout.add_widget(sf.getDisplayImage())
			self._frameCountToSelectionId[identifier] = i
			i += 1
			layoutHeight += 64

		self._scrollLayout.height = layoutHeight

	def getSelectableFrameBySelectionId(self, identifier):
		assert identifier in self.__selectableFrameDict
		return self.__selectableFrameDict[identifier]

	def getFrameCountById(self, identifier):
		return self._frameCountToSelectionId[identifier]

class AnimationEditor(KeyboardAccess, SeparatorLabel, LayoutGetter, ChangesConfirm):
	"""Class that implements the popup of the animation editor."""
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.alertExit()

		elif (keycode[1] == 'n'):
			self.__animationHandler.createNewAnimation()

		elif (keycode[1] == 'e'):
			self.__animationHandler.editCurrentAnimation()

		elif (keycode[1] == 'l'):
			ModulesAccess.get('AnimationLinkDisplay').open()

		elif (keycode[1] == 's'):
			ModulesAccess.get('AnimationFrameDisplay').setSelectedFrameDuration()

		elif (keycode[1] == 'r'):
			ModulesAccess.get('AnimationFrameDisplay').resetSelectedFrameDuration()

		elif (keycode[1] == 'left'):
			if (self.__isShiftPressed == self.__isCtrlPressed):
				ModulesAccess.get('AnimationFrameDisplay').changeSelectedFrameLeft()
			elif (self.__isShiftPressed == True):
				ModulesAccess.get('AnimationFrameDisplay').moveSelectedFrameLeft()
			else:
				ModulesAccess.get('AnimationFrameDisplay').copySelectedFrameLeft()

		elif (keycode[1] == 'right'):
			if (self.__isShiftPressed == self.__isCtrlPressed):
				ModulesAccess.get('AnimationFrameDisplay').changeSelectedFrameRight()
			elif (self.__isShiftPressed == True):
				ModulesAccess.get('AnimationFrameDisplay').moveSelectedFrameRight()
			else:
				ModulesAccess.get('AnimationFrameDisplay').copySelectedFrameRight()

		elif (keycode[1] == 'delete'):
			if (self.__isShiftPressed== True):
				self.__animationHandler.deleteCurrentAnimation()
			else:
				ModulesAccess.get('AnimationFrameDisplay').deleteSelectedFrame()

	def _processKeyDown(self, keyboard, keycode, text, modifiers):
		if ('shift' in modifiers):
			self.__isShiftPressed = True
		else:
			self.__isShiftPressed = False

		if ('ctrl' in modifiers):
			self.__isCtrlPressed = True
		else:
			self.__isCtrlPressed = False

	def __init__(self):
		super(AnimationEditor, self).__init__()
		self._layout = BoxLayout(orientation = 'horizontal')
		self.__frameEditor = FrameEditor()
		self.__animationDisplay = AnimationDisplay()
		self.__frameDisplay = FrameDisplay()
		self.__animationAndFrame = AnimationAndFrameEditor()
		self.__animationHandler = AnimationHandler()
		self.__linkDisplay = AnimationLinkDisplay()

		doubleLine = defaultLineSize.copy()
		doubleLine['height'] = defaultLineSize['height'] * 2

		leftMenu = BoxLayout(orientation = 'vertical', size_hint = (None, 1), width = 200)
		self._cancelButton = CancelableButton(text = 'Cancel', on_release = self.alertExit,
			**defaultLineSize)
		self._doneButton = CancelableButton(text = 'Done', on_release = self.save,
			**defaultLineSize)
		leftMenu.add_widget(AlignedLabel(text = 'Frames:', **defaultLabelSize))
		leftMenu.add_widget(self.__frameEditor.getLayout())
		leftMenu.add_widget(AlignedLabel(
			text = 'Double click on the items\nabove to add a new frame.', **doubleLine
		))
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
		self.__newAnimationButton = CancelableButton(text = 'New animation (n)',
			on_release = self.__animationHandler.createNewAnimation, **defaultLineSize)
		self.__editAnimationButton = CancelableButton(text = 'Edit animation (e)',
			on_release = self.__animationHandler.editCurrentAnimation, **defaultLineSize)
		self.__editLinksButton = CancelableButton(text = 'Edit links (l)',
			on_release = self.__linkDisplay.open, **defaultLineSize)
		self.__deleteAnimationButton = CancelableButton(text = 'Delete animation (s. del)',
			on_release = self.__animationHandler.deleteCurrentAnimation, **defaultLineSize)

		rightMenu.add_widget(self.__animationHandler.getLayout())
		rightMenu.add_widget(self.__newAnimationButton)
		rightMenu.add_widget(self.__editAnimationButton)
		rightMenu.add_widget(self.__editLinksButton)
		rightMenu.add_widget(self.__deleteAnimationButton)

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
		animationChanges = ModulesAccess.get('AnimationHandler').getChangedNames()
		deletedAnimations = set(ModulesAccess.get('AnimationHandler').getDeletedAnimations())
		for animation in deletedAnimations:
			identifier = animation.getId()
			if (identifier is not None):
				# Saved animation was removed, links are removed by the method as well.
				self.__resourceInfo.removeAnimationInfoById(identifier)

		animations = ModulesAccess.get('AnimationHandler').getAnimations()

		animationIdToName = {}
		for animation in animations:
			name = animation.getName()
			duration = animation.getDuration()
			identifier = animation.getId()
			animationInfo = AnimationInfo(name, duration, identifier)
			for frame in animation.getFrames():
				selectionId = frame.getSelectionId()
				if (frame.hasDuration() == True):
					duration = frame.getDuration()
				else:
					duration = None
				fi = FrameInfo(selectionId, duration)
				animationInfo.addFrameInfo(fi)
			if (identifier is not None):
				self.__resourceInfo.removeAnimationInfoById(identifier)
				self.__resourceInfo.addAnimationInfo(animationInfo)
			else:
				newId = self.__resourceInfo.addAnimationInfo(animationInfo)
				animation.setId(newId)
			animationIdToName[animation.getId()] = animation.getName()

		# removing links that are no longer used
		linkInfoDict = self.__linkDisplay.getLinksDict()
		for linkInfo in self.__resourceInfo.getLinksList():
			sourceId = linkInfo.getSourceId()
			if (sourceId not in animationIdToName):
				self.__resourceInfo.removeLinkById(linkInfo.getId())
				continue

			destinationId = linkInfo.getDestinationId()
			if (destinationId not in animationIdToName):
				self.__resourceInfo.removeLinkById(linkInfo.getId())
				continue

			sourceName = animationIdToName[sourceId]
			destinationName = animationIdToName[destinationId]
			if sourceName not in linkInfoDict:
				self.__resourceInfo.removeLinkById(linkInfo.getId())
			elif destinationName not in linkInfoDict[sourceName]:
				self.__resourceInfo.removeLinkById(linkInfo.getId())
			elif linkInfoDict[sourceName][destinationName].getActive() == True:
				self.__resourceInfo.removeLinkById(linkInfo.getId())

		for linkList in linkInfoDict.itervalues():
			for animationLink in linkList.itervalues():
				if (animationLink.getActive() == True):
					sourceAnimation = animationLink.getSource()
					destinationAnimation = animationLink.getDestination()
					if (sourceAnimation not in deletedAnimations and destinationAnimation not in deletedAnimations):
						identifier = animationLink.getId()
						li = LinkInfo(
							sourceAnimation.getId(), destinationAnimation.getId(),
							animationLink.getPriority(), animationLink.getProperty(), identifier
						)
						if (identifier is not None):
							self.__resourceInfo.removeLinkById(identifier)
						self.__resourceInfo.addLink(li)

		futureName = basename(self.__resourceInfo.getPath())
		ModulesAccess.get('BaseObjectsMenu').ignoreUpdate(futureName)
		SplittedImageExporter.save(self.__resourceInfo)

		objList = ModulesAccess.get('SceneHandler').getCurrentSceneObjects()
		for obj in objList:
			animationName = obj.getAnimation()
			if (animationName is not None and animationName in animationChanges):
				obj.setAnimation(animationChanges[animationName])

		removedAnimations = set(deletedAnimations)
		resetAnitionOnObjectList(objList, removedAnimations)

		ModulesAccess.get('BaseObjectsMenu').updateResource(self.__resourceInfo)

		self.close()

	def open(self, path):
		self.__isCtrlPressed = False
		self.__isShiftPressed = False
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__resourceInfo = SplittedImageImporter().load(path)
		self.__frameEditor.load(self.__resourceInfo)
		self.__animationHandler.load(self.__resourceInfo)
		self.__linkDisplay.load(self.__resourceInfo)
		self.resetChanges()

		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__animationHandler.unsetAnimation()
		self.__popup.dismiss()

class AnimationLinkButton(BoxLayout, ToggleButton, SingleIdentifiedObject):
	def on_touch_up(self, touch):
		if (touch.button == 'right'):
			return False

		if (self.collide_point(*touch.pos) == True and self._touchUid is not None and touch.uid == self._touchUid):
			if (touch.is_double_tap == False):
				if (self.state == 'normal'):
					self.state = 'down'
					ModulesAccess.get('AnimationLinkDisplay').registerChanges()
					self.getAnimationLink().setActive(True)

				ModulesAccess.get('AnimationLinkEditor').setValues(self.getAnimationLink())
			elif (self.state == 'down'):
				ModulesAccess.get('AnimationLinkEditor').reset()
				self.state = 'normal'
				self.getAnimationLink().setActive(False)
				ModulesAccess.get('AnimationLinkDisplay').registerChanges()

	def on_touch_down(self, touch):
		if (touch.button == 'right'):
			return False

		if (self.collide_point(*touch.pos) == True):
			self._touchUid = touch.uid

	def __init__(self, al, **kwargs):
		assert isinstance(al, AnimationLink)
		self._touchUid = None
		self._animationLink = al
		super(AnimationLinkButton, self).__init__(orientation = 'vertical', **kwargs)
		sourceLine = AlignedLabel(text = 'Source: ' + al.getSourceName(), **defaultLineSize)
		destinationLine = AlignedLabel(text = 'Destination: ' + al.getDestinationName(), **defaultLineSize)
		self.add_widget(sourceLine)
		self.add_widget(destinationLine)
		if (al.getActive() == True):
			self.state = 'down'

	def getAnimationLink(self):
		return self._animationLink

class AnimationLinkDisplay(AnimationBaseScroll, KeyboardAccess, ChangesConfirm):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.alertExit()

	def _processTouchUp(self, touch):
		if (touch.button == "right"):
			self._defaultTouchUp(touch)
			return True

		elif (touch.button == "left"):
			touch.pos = self._layout.to_local(*touch.pos)
			touch.x, touch.y = touch.pos
			for item in self._scrollLayout.children:
				if item.collide_point(*touch.pos):
					item.on_touch_up(touch)
					return True

	def _processTouchDown(self, touch):
		if self._touchInside(touch) == False:
			return

		if (touch.button == "right"):
			self._defaultTouchDown(touch)
			return True
		elif (touch.button == "left"):
			touch.pos = self._layout.to_local(*touch.pos)
			touch.x, touch.y = touch.pos
			for item in self._scrollLayout.children:
				if item.collide_point(*touch.pos):
					item.on_touch_down(touch)
					return True

	def __init__(self):
		self.__popupLayout = BoxLayout(orientation = 'vertical')
		self._scrollLayout = GridLayout(cols = 1, rows = 1, size_hint = (None, None))

		super(AnimationLinkDisplay, self).__init__(size_hint = (1, 1), do_scroll = (1, 1),
			effect_cls = EmptyScrollEffect)

		ModulesAccess.add('AnimationLinkDisplay', self)
		linkEditor = AnimationLinkEditor()
		self._layout.add_widget(self._scrollLayout)

		self.__popupLayout.add_widget(self._layout)
		self.__popupLayout.add_widget(linkEditor.getLayout())

		self.__popup = Popup(
			title = 'Animation links',
			auto_dismiss = False,
			content = self.__popupLayout
		)

		self.__validLinksList = []
		self.__removedLinks = []

	def load(self, resourceInfo):
		self.__linksDict = {}
		animations = ModulesAccess.get('AnimationHandler').getAnimations()
		numberOfAnimations = len(animations)
		idToNameDict = {}
		for animation in animations:
			self.__linksDict[animation.getName()] = {}
			idToNameDict[animation.getId()] = animation.getName()
			for i in range(numberOfAnimations):
				al = AnimationLink(animation, animations[i])
				self.__linksDict[animation.getName()][animations[i].getName()] = al

		for linkInfo in resourceInfo.getLinksList():
			sourceName = idToNameDict[linkInfo.getSourceId()]
			destinationName = idToNameDict[linkInfo.getDestinationId()]
			self.__linksDict[sourceName][destinationName].setPriority(linkInfo.getPriority())
			self.__linksDict[sourceName][destinationName].setProperty(linkInfo.getProperty())
			self.__linksDict[sourceName][destinationName].setId(linkInfo.getId())
			self.__linksDict[sourceName][destinationName].setActive(True)

	def save(self, *args):
		self.__linksDict = self.__copyLinks
		ModulesAccess.get('AnimationLinkEditor').saveCurrentLinkData()
		if (self._hasChanges == True):
			ModulesAccess.get('AnimationEditor').registerChanges()
		self.close()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		ModulesAccess.get('AnimationLinkEditor').reset()
		self.resetChanges()
		animations = ModulesAccess.get('AnimationHandler').getAnimations()
		numberOfAnimations = len(animations)
		self._scrollLayout.clear_widgets()
		self._scrollLayout.cols = numberOfAnimations + 1
		self._scrollLayout.rows = numberOfAnimations + 1
		baseWidth = 300
		baseHeight = defaultLineSize['height'] * 2
		self._scrollLayout.width = (numberOfAnimations + 1) * baseWidth
		self._scrollLayout.height = (numberOfAnimations + 1) * baseHeight
		linksSize = {
			'width': baseWidth,
			'height': baseHeight,
			'size_hint': (None, None)
		}

		self.__copyLinks = {}
		for key, value in self.__linksDict.iteritems():
			self.__copyLinks[key] = {}
			for otherKey, animationLink in value.iteritems():
				self.__copyLinks[key][otherKey] = AnimationLink.copy(animationLink)

		self._scrollLayout.add_widget(AlignedLabel(text = 'Destination ->\nSource \\/', **linksSize))
		for animation in animations:
			self._scrollLayout.add_widget(AlignedLabel(text = animation.getName(), **linksSize))

		for animation in animations:
			for i in range(numberOfAnimations + 1):
				if (i == 0):
					if (animation.getName() not in self.__copyLinks):
						self.__copyLinks[animation.getName()] = {}

					self._scrollLayout.add_widget(AlignedLabel(text = animation.getName(), **linksSize))
				else:
					if (animation.getName() in self.__copyLinks and animations[i-1].getName() in
							self.__copyLinks[animation.getName()]):
						al = self.__copyLinks[animation.getName()][animations[i-1].getName()]
					else:
						al = AnimationLink(animation, animations[i-1])
						self.__copyLinks[animation.getName()][animations[i-1].getName()] = al

					linkButton = AnimationLinkButton(
						al,	width = baseWidth, height = baseHeight, size_hint = (None, None)
					)
					self._scrollLayout.add_widget(linkButton)

		self.__popup.open()

	def getLinksDict(self):
		return self.__linksDict

	def updateName(self, oldName, newName):
		if (oldName in self.__linksDict):
			swap = self.__linksDict[oldName]
			self.__linksDict[newName] = swap
			del self.__linksDict[oldName]

		for key, value in self.__linksDict.iteritems():
			if (oldName in value):
				swap = value[oldName]
				value[newName] = swap
				del value[oldName]

class AnimationLinkEditor(LayoutGetter, SeparatorLabel):
	def __init__(self):
		super(AnimationLinkEditor, self).__init__()
		inputSize = defaultInputSize.copy()
		inputSize['width'] = defaultSmallButtonSize['width']

		self._layout = BoxLayout(orientation = 'vertical', height = 200, size_hint = (1.0, None))
		self.__sourceAnimationLabel = AlignedLabel(text = 'Source: ', **defaultLabelSize)
		self.__destinationAnimationLabel = AlignedLabel(text = 'Destination: ', **defaultLabelSize)

		self._layout.add_widget(self.__sourceAnimationLabel)
		self._layout.add_widget(self.__destinationAnimationLabel)
		self.__priorityLine = BoxLayout(orientation = 'horizontal', **defaultInputSize)
		self.__priorityLine.add_widget(AlignedLabel(text = 'Priority: ', **defaultInputSize))
		self.__priorityInput = NumberInput(multiline = False, **inputSize)
		self.__priorityLine.add_widget(self.__priorityInput)

		propertyLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		self.__noPropertyButton = AlignedToggleButton(text = ' No property', group = 'property',
			allow_no_selection = False, **defaultLineSize)
		self.__immediateButton = AlignedToggleButton(text = ' Immeditate', group = 'property',
			allow_no_selection = False, **defaultLineSize)
		self.__clearTargetButton = AlignedToggleButton(text = ' Clear Target', group = 'property',
			allow_no_selection = False, **defaultLineSize)
		propertyLine.add_widget(self.__noPropertyButton)
		propertyLine.add_widget(self.__immediateButton)
		propertyLine.add_widget(self.__clearTargetButton)

		bottomLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		doneButton = CancelableButton(text = 'Done', on_release = ModulesAccess.get('AnimationLinkDisplay').save,
			**defaultSmallButtonSize)
		cancelButton = CancelableButton(text = 'Cancel',
			on_release = ModulesAccess.get('AnimationLinkDisplay').alertExit, **defaultSmallButtonSize)

		bottomLine.add_widget(self.getSeparator())
		bottomLine.add_widget(doneButton)
		bottomLine.add_widget(cancelButton)

		self.__propertyLabel = AlignedLabel(text = 'Property:', **defaultLabelSize)
		self._layout.add_widget(self.__priorityLine)
		self._layout.add_widget(self.__propertyLabel)
		self._layout.add_widget(propertyLine)
		self._layout.add_widget(self.getSeparator())
		self._layout.add_widget(bottomLine)

		self.__currentLink = None

		ModulesAccess.add('AnimationLinkEditor', self)

	def __registerChanges(self, *args):
		ModulesAccess.get('AnimationLinkDisplay').registerChanges()

	def __disableElements(self, value):
		self.__sourceAnimationLabel.disabled = value
		self.__destinationAnimationLabel.disabled = value
		self.__noPropertyButton.disabled = value
		self.__immediateButton.disabled = value
		self.__clearTargetButton.disabled = value
		self.__priorityLine.disabled = value
		self.__propertyLabel.disabled = value

	def reset(self):
		self.__unbindChanges()
		self.__disableElements(True)
		self.__sourceAnimationLabel.text = 'Source: '
		self.__destinationAnimationLabel.text = 'Destination: '
		self.__noPropertyButton.state = 'normal'
		self.__immediateButton.state = 'normal'
		self.__clearTargetButton.state = 'normal'
		self.__priorityInput.text = ''
		self.__currentLink = None
		self.__bindChanges()

	def __bindChanges(self):
		self.__noPropertyButton.bind(state=self.__registerChanges)
		self.__immediateButton.bind(state=self.__registerChanges)
		self.__clearTargetButton.bind(state=self.__registerChanges)
		self.__priorityInput.bind(text=self.__registerChanges)

	def __unbindChanges(self):
		self.__noPropertyButton.unbind(state=self.__registerChanges)
		self.__immediateButton.unbind(state=self.__registerChanges)
		self.__clearTargetButton.unbind(state=self.__registerChanges)
		self.__priorityInput.unbind(text=self.__registerChanges)

	def saveCurrentLinkData(self):
		if (self.__currentLink is not None):
			try:
				priority = int(self.__priorityInput.text)
				priority = min(priority, 15)
			except:
				priority = 8

			anyChanges = False
			if (self.__currentLink.getPriority() != priority):
				self.__currentLink.setPriority(priority)
				anyChanges = True

			property = self.__currentLink.getProperty()
			if (self.__noPropertyButton.state == 'down' and property != ''):
				self.__currentLink.setProperty('')
				anyChanges = True
			elif (self.__immediateButton.state == 'down' and property != 'immeditate'):
				self.__currentLink.setProperty('immeditate')
				anyChanges = True
			elif (self.__clearTargetButton.state == 'down' and property != 'cleartarget'):
				self.__currentLink.setProperty('cleartarget')
				anyChanges = True

			if (anyChanges == True):
				self.__registerChanges()

	def setValues(self, al):
		assert isinstance(al, AnimationLink)

		self.__unbindChanges()
		self.__disableElements(False)
		self.saveCurrentLinkData()

		self.__sourceAnimationLabel.text = 'Source: ' + al.getSourceName()
		self.__destinationAnimationLabel.text = 'Destination: ' + al.getDestinationName()
		if (al.getProperty() == ''):
			self.__noPropertyButton.state = 'down'
			self.__immediateButton.state = 'normal'
			self.__clearTargetButton.state = 'normal'
		elif (al.getProperty() == 'immeditate'):
			self.__noPropertyButton.state = 'normal'
			self.__immediateButton.state = 'down'
			self.__clearTargetButton.state = 'normal'
		else:
			self.__noPropertyButton.state = 'normal'
			self.__immediateButton.state = 'normal'
			self.__clearTargetButton.state = 'down'

		self.__priorityInput.text = str(al.getPriority())

		self.__currentLink = al
		self.__bindChanges()


class AnimationSelector(AnimationBaseScroll, SeparatorLabel, ChangesConfirm, KeyboardAccess):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.alertExit()

	def _processTouchUp(self, touch):
		if (touch.button == "right"):
			self._defaultTouchUp(touch)
			return True

		elif (touch.button == "left"):
			touch.pos = self._layout.to_local(*touch.pos)
			touch.x, touch.y = touch.pos
			for button in self._scrollLayout.children:
				if (button.collide_point(*touch.pos) == True):
					button.on_touch_up(touch)
					break
		return False

	def _processTouchMove(self, touch):
		if (touch.button == "right"):
			self._defaultTouchMove(touch)
			return True
		return False

	def _processTouchDown(self, touch):
		if (self._touchInside(touch) == False):
			return

		if (touch.button == "right"):
			self._defaultTouchDown(touch)
			return True

		elif (touch.button == "left"):
			touch.pos = self._layout.to_local(*touch.pos)
			touch.x, touch.y = touch.pos
			for button in self._scrollLayout.children:
				if (button.collide_point(*touch.pos) == True):
					button.on_touch_down(touch)
					break
		return False

	def __init__(self):
		self._scrollLayout = GridLayout(cols = 1, rows = 1, size_hint = (None, None))

		super(AnimationSelector, self).__init__(size_hint = (1, 1), do_scroll = (0, 1),
			effect_cls = EmptyScrollEffect)

		self._layout.add_widget(self._scrollLayout)

		self.__popupLayout = BoxLayout(orientation = 'vertical')
		self.__popup = Popup(
			title='Animation Selector',
			content = self.__popupLayout,
			height = 300,
			width = 400,
			size_hint = (None, None),
			auto_dismiss = False
		)

		self.__popupLayout.add_widget(AlignedLabel(text = 'Select an animation:', **defaultLineSize))
		self.__popupLayout.add_widget(self._layout)
		self.__popupLayout.add_widget(AlignedLabel(text = '', **defaultLineSize))
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.alertExit, **defaultSmallButtonSize)
		self.__doneButton = CancelableButton(text = 'Done', on_release = self.save, **defaultSmallButtonSize)
		bottomLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		bottomLine.add_widget(self.getSeparator())
		bottomLine.add_widget(self.__cancelButton)
		bottomLine.add_widget(self.__doneButton)
		self.__popupLayout.add_widget(bottomLine)
		self.__noAnimationButton = AlignedToggleButtonLeftOnly(
			text='No animation',
			group = 'AnimationSelector',
			allow_no_selection = False,
			**defaultLineSize
		)
		self.__noAnimationButton.bind(state=self.registerChanges)
		self.__editingObjects = []

		ModulesAccess.add('AnimationSelector', self)

	def open(self, *args):
		self._scrollLayout.clear_widgets()
		objList = ModulesAccess.get('SceneHandler').getCurrentSelection()
		if not objList:
			Alert(
				title = 'Error',
				text = 'No object selected.',
				closeButtonText = 'Ok'
			).open()
			return

		different = False
		filepath = objList[0].getPath()
		for obj in objList:
			if (filepath != obj.getPath()):
				different = True
				break
		if (different == True):
			Alert(
				title = 'Error',
				text = 'You can only set the animation of multiple objects\n'\
					'if they are created from the same resource.',
				closeButtonText = 'Ok'
			).open()
			return

		resourceInfo = ModulesAccess.get('BaseObjectsMenu').getResourceInfoByFilename(basename(filepath))
		animationsInfo = resourceInfo.getAnimationInfoList() if resourceInfo is not None else None
		if (resourceInfo is None or not animationsInfo):
			Alert(
				title = 'Error',
				text = 'Object doesn\'t have animations.',
				closeButtonText = 'Ok'
			).open()
			return

		numberOfAnimations = len(animationsInfo)
		self._scrollLayout.rows = numberOfAnimations + 1
		self._scrollLayout.height = (numberOfAnimations + 1) * defaultLineSize['height']
		self._scrollLayout.width = 390

		self.__noAnimationButton.state = 'normal'
		allNone = True
		animToSet = objList[0].getAnimation()
		for obj in objList:
			if (obj.getAnimation() is not None):
				allNone = False

			if (animToSet != obj.getAnimation()):
				animToSet = None
				break

		self._scrollLayout.add_widget(self.__noAnimationButton)
		for info in animationsInfo:
			newButton = AlignedToggleButtonLeftOnly(
				text=info.getName(),
				group = 'AnimationSelector',
				allow_no_selection = False,
				**defaultLineSize
			)
			if (allNone == False and animToSet is not None and animToSet == info.getName()):
				newButton.state = 'down'
			newButton.bind(state=self.registerChanges)
			self._scrollLayout.add_widget(newButton)

		if (allNone == True):
			self.__noAnimationButton.state = 'down'

		self.__editingObjects = objList
		self.resetChanges()
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__popup.open()

	def save(self, *args):
		valueToSet = None
		for button in self._scrollLayout.children:
			if (button.state == 'down'):
				if (button != self.__noAnimationButton):
					valueToSet = button.text
				break

		if (valueToSet is None and self.__noAnimationButton.state != 'down'):
			Alert(
				title = 'Error',
				text = 'No value selected.',
				closeButtonText = 'Ok'
			).open()
			return

		for obj in self.__editingObjects:
			obj.setAnimation(valueToSet)
			obj.unsetMarked()
			obj.setMarked()

		ModulesAccess.get('ObjectDescriptor').update()
		self.close()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()
