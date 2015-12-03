from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from editorutils import EmptyScrollEffect
from editorheritage import LayoutGetter
from modulesaccess import ModulesAccess

class Frame:
	def __init__(self, image):
		self.__duration = None
		self.__image = image

	def getDuration(self):
		return self.__duration

	def setDuration(self, newDuration):
		self.__duration = newDuration

class Animation:
	def __init__(self, name, id):
		self.__name = name
		self.__id = id
		self.__frames = []

class AnimationLink:
	def __init__(self, source, destination, priority = 8, property = None):
		self.__source = source
		self.__destination = destination
		self.__priority = priority
		self.__property = property

class SelectableFrame:
	def __init__(self, base,  pos, size):
		texture = base.texture.get_region(pos[0], pos[1]. size[0], size[1])
		self.__displayImage = Image(texture = texture, size = (190, 190))
		self.__realImage = Image(texture = texture, size = size)

	def getDisplayImage(self):
		return self.__displayImage

	def getRealImage(self):
		return self.__realImage

class FrameEditor(LayoutGetter):
	def __init__(self):
		self._layout = BoxLayout(orientation = 'vertical', width = 200)
		self._scroll = ScrollView(size_hint = (1.0, 1.0), do_scroll = (0, 1), effect_cls = EmptyScrollEffect)
		self._scrollLayout = BoxLayout(orientation = 'vertical', width = 200)
		self._layout.add_widget(self._scroll)
		self._scroll.add_widget(self._scrollLayout)

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
			layoutHeight += 203

		self._scrollLayout.height = layoutHeight

class AnimationEditor:
	def __init__(self):
		self._layout = BoxLayout(orientation = 'horizontal')
		self.__frameEditor = FrameEditor()
		self._layout.add_widget(self.__frameEditor.getLayout())
		self.__popup = Popup(
			title = 'Animation Editor',
			auto_dismiss = False,
			content = self._layout
		)

		ModulesAccess.add('AnimationEditor', self)

	#def open(self


