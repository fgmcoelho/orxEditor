from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.core.window import Window

from ConfigParser import ConfigParser

from os.path import isdir, isfile, join, exists
from os import listdir, walk, stat, chown, getcwd

class RenderedObject:

	def __init__(self, name):
		self.floatObject = name

class Scene:
	
	def __init__(self):
		self.objectList = []
		self.maxX = 0.0
		self.minX = 0.0
		self.maxY = 0.0
		self.minY = 0.0

class SceneHandler:
	def __init__(self, rightScreen, maxWidthProportion = 0.75, maxHeightProportion = 0.667):
		
		self.maxWidthProportion = maxWidthProportion
		self.maxHeightProportion = maxHeightProportion
				
		self.layout = FloatLayout(size=(5000, 5000), size_hint = (None, None))
		self.scrollView = ScrollView(size_hint=(None, None))
		self.scrollView.add_widget(self.layout)
		rightScreen.add_widget(self.scrollView)
		
		self.updateLayoutSizes()

	def updateLayoutSizes(self):
		
		wx, wy = Window.size
		
		xSize = wx * self.maxWidthProportion
		ySize = wy * self.maxHeightProportion
		
		self.scrollView.size = (xSize, ySize)

class ObjectDescriptor:
	def __init__(self, rightScreen, maxWidthProportion = 0.75, maxHeightProportion = 0.333):
		
		self.maxWidthProportion = maxWidthProportion
		self.maxHeightProportion = maxHeightProportion

		self.layout = BoxLayout(orientation = 'vertical', size_hint = (None, None))
		self.pathLabel = Label(text = 'Path: ')
		self.sizeLabel = Label(text = 'Size: ')
		self.collisionLabel = Label(text = 'Collision: ')
		
		self.layout.add_widget(self.pathLabel)
		self.layout.add_widget(self.sizeLabel)
		self.layout.add_widget(self.collisionLabel)

		rightScreen.add_widget(self.layout)

		self.updateLayoutSizes()

	def setObject (self, path, size, collidable):
		self.pathLabel.text = 'Path: ' + str(path)
		self.sizeLabel.text = 'Size: ' + str(size)
		self.collisionLabel.text = 'Collision:' + str(collidable)

	def updateLayoutSizes(self):
		
		wx, wy = Window.size
		
		xSize = wx * self.maxWidthProportion
		ySize = wy * self.maxHeightProportion
		
		self.layout.size = (xSize, ySize)


class LeftMenuHandler:
	
	def __init__(self, leftMenu, objectHandler, maxWidthProportion = 0.25, maxHeightProportion = 1.0):
		self.imageList = []
		self.objectHandlerReference = objectHandler
		self.maxWidthProportion = maxWidthProportion
		self.maxHeightProportion = maxHeightProportion

		l = listdir(join(getcwd(), 'tiles'))
		self.numberOfItems = 0
		for item in l:
			if (item[-4:] == '.png'):
				img = Image(source = join(getcwd(), 'tiles' ,item))
				self.imageList.append(img)
				self.numberOfItems += 1

		

		self.layout = GridLayout(cols=1, rows = self.numberOfItems, size_hint = (None, None))
		for item in self.imageList:
			self.layout.add_widget(item)

		self.scrollView = ScrollView(size_hint = (None, None) )
		self.scrollView.add_widget(self.layout)
		self.scrollView.do_scroll_x = False

		leftMenu.add_widget(self.scrollView)

		self.updateLayoutSizes()

	def updateLayoutSizes(self):
		wx, wy = Window.size
		
		xSize = wx * self.maxWidthProportion
		ySize = wy * self.maxHeightProportion

		scrollViewWidth = 0
		if (self.numberOfItems * xSize < ySize):
			scrollViewWidth = ySize
		else:
			scrollViewWidth = xSize * self.numberOfItems

		self.layout.size = (xSize, scrollViewWidth)
		self.scrollView.size = (xSize, ySize)


	def handleTouch(self, touch):
		for image in self.imageList:
			
			if (touch.is_mouse_scrolling == False and image.collide_point(*touch.pos) == True):
				if (touch.is_double_tap == True):
					self.objectHandlerReference.setObject(image.source, image.texture.size, 1)
				
class TileEditor(App):
	
	resizeList = []

	def dispatchTouch(self, touch):
		if (self.leftMenuBase.collide_point(*touch.pos) == True):
			self.leftMenuHandler.handleTouch(touch)

	def build_config(self, c):
		Config.set('graphics', 'width', 800)
		Config.set('graphics', 'height', 600)
		Config.set('graphics', 'fullscreen', 0)
		Config.write()

	@staticmethod
	def resizeTest(x, y):
		print "resize! "+str((x, y))
		for widget in TileEditor.resizeList:
			widget.updateLayoutSizes()

	def build(self):

		self.root = BoxLayout(orientation='horizontal', padding = 0, spacing = 0)

		self.leftMenuBase = BoxLayout(
			orientation='vertical', 
			padding = 0, 
			spacing = 0,
			size_hint = (0.25, 1.0)
		)

		self.rightScreen = BoxLayout(
			orientation = 'vertical',
			padding = 0, 
			spacing = 0,
			size_hint = (0.75, 1.0),
		)

		self.root.add_widget(self.leftMenuBase)
		self.root.add_widget(self.rightScreen)
		
		self.sceneHandler = SceneHandler(self.rightScreen)
		self.objectHandler = ObjectDescriptor(self.rightScreen)
		self.leftMenuHandler = LeftMenuHandler(self.leftMenuBase, self.objectHandler)
	
		TileEditor.resizeList.append(self.sceneHandler)
		TileEditor.resizeList.append(self.objectHandler)
		TileEditor.resizeList.append(self.leftMenuHandler)

		self.root.on_touch_up = self.dispatchTouch
		Window.on_resize = self.resizeTest

		return self.root


if __name__ == '__main__':
	TileEditor().run()
