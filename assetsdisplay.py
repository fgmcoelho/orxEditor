from kivy.uix.boxlayout import BoxLayout

class AssetsDisplay:

	def __init__(self, orientation, minSize, pictureSize, path, filterFormats, filterOpeners):
		assert (len(filterFormats) == len(filterOpeners))
		
		self.__contentBox = BoxLayout(orientation = orientation)
		self.__scrollView = ScrollView(size_hint = (None, None))
		self.__assetsList = []

		if (orientation == 'horizontal'):
			self.__scrollView.do_scroll_y = False
		else:
			self.__scrollView.do_scroll_x = False

		l = listdir(path)
		for i in range(filterFormats):
			self.__loadAssets(l, filterFormats[i], filterOpeners[i])

		self.__setSizes(minSize, pictureMaxSize)

		for asset in self.__assetsList:
			self.__contentBox.add_widget(asset.getImage())

		self.__scrollView.add_widget(self.__contentBox)

	def __setSizes(self, mininumSize, pictureSize):
		numberOfItems = len(self.__assetsList)
		x, y = 0, 0
		
		if (numberOfItems * pictureSize[0] > mininumSize[0]):
			x = numberOfItems * pictureSize[0]
		else:
			x = mininumSize[0]

		if (numberOfItems * pictureSize[1] > mininumSize[1]):
			y = numberOfItems * pictureSize[1]
		else:
			y = mininumSize[1]

		self.__contentBox.size = (x, y)

	def __loadAssets(self, filesList, currentFilter, currentOpener):
		
		currentFilterLen = len(currentFilter)
		for currentFile  in filesList:
			if (len (currentFile) >  currentFilterLen and currentFile[-currentFilterLen:] == currentFilter):
				assetsList = currentOpener(currentFile)
				for asset in assetsList:
					self.__assetsList.append(asset)

	def getLayout(self):
		return self.__scrollView

