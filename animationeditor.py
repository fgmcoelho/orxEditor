from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.treeview import TreeView, TreeViewNode, TreeViewLabel

from keyboard import KeyboardAccess, KeyboardGuardian
from editorutils import EmptyScrollEffect, SeparatorLabel, AlignedLabel, CancelableButton
from editorheritage import LayoutGetter
from modulesaccess import ModulesAccess
from splittedimagemap import SpriteSelection, SplittedImageImporter
from uisizes import defaultLabelSize, defaultFontSize, defaultSmallButtonSize, defaultLineSize

class Frame:
	def __init__(self, image):
		self.__duration = None
		self.__image = image

	def getDuration(self):
		return self.__duration

	def setDuration(self, newDuration):
		self.__duration = newDuration

class Animation:
	def __init__(self, name):
		self.__name = name
		self.__frames = []

class AnimationLink:
	def __init__(self, source, destination, priority = 8, property = None):
		self.__source = source
		self.__destination = destination
		self.__priority = priority
		self.__property = property

class SelectableFrame:
	def __init__(self, base,  pos, size):
		self.texture = base.texture.get_region(pos[0], pos[1], size[0], size[1])
		self.__displayImage = Image(texture = self.texture, size = (64, 64))

	def getDisplayImage(self):
		return self.__displayImage

	def getRealImage(self):
		return Image(texture = self.texture, size = (64, 64))

class AnimationNode(TreeViewLabel):
	def __init__(self, name):
		self.__animation = Animation(name)
		super(AnimationNode, self).__init__()

	def getAnimation(self):
		return self.__animation

class AnimationHandler(LayoutGetter):
	def __init__(self):
		self.__defaultName = 'NewAnimation'
		self._layout = ScrollView(do_scroll = (0, 1), effect_cls = EmptyScrollEffect, width = 200,
			size_hint = (None, 1.0))
		self._scrollLayout = TreeView(root_options = { 'text' : 'Animations'})
		self._layout.add_widget(self._scrollLayout)
		self._scrollLayout.add_node(node)

		ModulesAccess.add('AnimationHandler', self)

	def addFrameToCurrentAnimation(self, sf):
		if (self._layout.selected_node != self._layout.root):
			animation = self._layout.selected_node.getAnimation()
			animation.addFrame(sf)

	def createNewAnimation(self):
		count = 0
		for node in self._layout.nodes:
			if node[0:] == self.__defaultName):
				count = int(node[len(self.__defaultName)])

class AnimationDisplay(LayoutGetter):
	def __init__(self):
		self._layout = ScrollView(effect_cls = EmptyScrollEffect)
		self._scrollLayout = BoxLayout(orientation = 'horizontal', size_hint = (1, 1))
		self._layout.add_widget(self._scrollLayout)

class FrameDisplay(LayoutGetter):
	def __init__(self):
		self._layout = ScrollView(size_hint = (1.0, None), do_scroll = (0, 1), effect_cls = EmptyScrollEffect,
			height = 200)
		self._scrollLayout = BoxLayout(orientation = 'vertical', height = 200, size_hint = (1.0, None))
		self._layout.add_widget(self._scrollLayout)

class AnimationAndFrameEditor(LayoutGetter, SeparatorLabel):
	def __init__(self):
		super(AnimationAndFrameEditor, self).__init__()
		self._layout = BoxLayout(orientation = 'vertical', height = 100, size_hint = (1.0, None))
		self._nameLabel = AlignedLabel(text = 'Name: ', **defaultLineSize)
		self._frameTimeLabel = AlignedLabel(text = 'Frame time: ', **defaultLineSize)
		buttonBox = BoxLayout(orientation = 'horizontal')
		self._renameButton = CancelableButton(text = 'Rename', **defaultSmallButtonSize)
		self._cancelButton = CancelableButton(text = 'Cancel', **defaultSmallButtonSize)
		self._doneButton = CancelableButton(text = 'Done', **defaultSmallButtonSize)
		self._layout.add_widget(self._nameLabel)
		self._layout.add_widget(self._frameTimeLabel)
		self._layout.add_widget(self.getSeparator())
		buttonBox.add_widget(self._renameButton)
		buttonBox.add_widget(self._cancelButton)
		buttonBox.add_widget(self._doneButton)
		self._layout.add_widget(buttonBox)

class FrameEditor(LayoutGetter):
	def __init__(self):
		self._layout = ScrollView(do_scroll = (0, 1), effect_cls = EmptyScrollEffect, width = 200,
			size_hint = (None, 1.0))
		self._scrollLayout = BoxLayout(orientation = 'vertical', size_hint = (None, None), size = (200, 100))
		self._layout.add_widget(self._scrollLayout)

	def load(self, resourceInfo):
		self.__objectsList = []
		im = Image(source = resourceInfo.getPath())
		self._scrollLayout.clear_widgets()
		layoutHeight = defaultFontSize
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
		self._addButton = CancelableButton(text = 'Add Frame', on_release = self.__frameEditor.addFrame,
			**defaultLineSize)
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
		middleBox.add_widget(AlignedLabel(text = 'Animation Data:', **defaultLineSize))
		middleBox.add_widget(self.__animationAndFrame.getLayout())

		rightMenu = BoxLayout(orientation = 'vertical', size_hint = (None, 1), width = 200)
		rightMenu.add_widget(self.__animationTree.getLayout())
		#self._

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

