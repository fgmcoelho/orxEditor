from os.path import join
from os import listdir, getcwd
from splittedimagemap import SplittedImageMap
from editorobjects import BaseObject, RenderedObject, ObjectTypes
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

class ObjectMenuItem:

	def __handle(self, image, touch):
		if (touch.is_mouse_scrolling == False and self.getDisplayImage().collide_point(*touch.pos) == True and 
				touch.is_double_tap == True):
			ObjectDescriptor.Instance.setOrDrawObject(self.getBaseObject())


	def __init__(self, baseObject, size):
		self.__baseObject = baseObject
		self.__displayImage = Image(texture = baseObject.getBaseImage().texture, size = size, size_hint = (None, None),
			on_touch_down = self.__handle)

	def getBaseObject(self):
		return self.__baseObject
	
	def getDisplayImage(self):
		return self.__displayImage

class ObjectsMenu:
	
	def __loadPng(self, item, pngsToIgnoreList):
		fullPath = join(getcwd(), 'tiles', item)
		if (fullPath in pngsToIgnoreList):
			return
		
		img = Image(source = fullPath)
		obj = BaseObject(img, self.__numberOfItems)
		self.__menuObjectsList.append(ObjectMenuItem(obj, (64, 64)))
		self.__numberOfItems += 1

	def __loadOpf(self, item, pngsToIgnoreList):
		opfLoader = SplittedImageMap()
		opfLoader.importFromOpf(join(getcwd(), 'tiles',item))
		imagesList = opfLoader.getImagesList()
		for img in imagesList:
			obj = BaseObject(img, self.__numberOfItems, opfLoader.getBaseImagePath())
			self.__menuObjectsList.append(ObjectMenuItem(obj, (64, 64)))
			self.__numberOfItems += 1

		print ("Adding %s to the ignore list!" % (obj.getPath(), ))
		pngsToIgnoreList.append(obj.getPath())

	def __loadItems(self):
		l = listdir(join(getcwd(), 'tiles'))
		self.__menuObjectsList = []
		self.__numberOfItems = 0
		pngsToIgnoreList = []
		for item in l:
			if (item[-4:] == '.opf'):
				self.__loadOpf(item, pngsToIgnoreList)

		for item in l:
			if (item[-4:] == '.png' and item not in pngsToIgnoreList):
				self.__loadPng(item, pngsToIgnoreList)
		
		if (self.__layout == None):
			self.__layout = GridLayout(cols=1, rows = self.__numberOfItems, size_hint = (1.0, 1.0), spacing = (0, 3))
		else:
			self.__layout.rows = self.__numberOfItems 

		for menuObject in self.__menuObjectsList:
			img = menuObject.getDisplayImage()
			self.__layout.add_widget(img)
		
	def __init__(self, leftMenu, maxWidthProportion = 1.0, maxHeightProportion = 1.0):
		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion
		self.__layout = None

		self.__loadItems()

		self.__scrollView = ScrollView(size_hint = (1.0, 1.0) )
		self.__scrollView.add_widget(self.__layout)
		self.__scrollView.do_scroll_x = False


		leftMenu.add_widget(self.__scrollView)

	def resetAllWidgets(self):
		for menuObject in self.__menuObjectsList:
			self.__layout.remove_widget(menuObject.getDisplayImage())
			menuObject = None

		self.__loadItems()

