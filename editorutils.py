from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.effects.scroll import ScrollEffect

from keyboard import KeyboardAccess, KeyboardGuardian

from os.path import sep as pathSeparator
from os import getcwd
from math import sqrt

class NumberInput(TextInput):
	modulesDict = {}
	@staticmethod
	def selectInputByFocus(module, reverse = False):
		i = 0
		for numberInput in NumberInput.modulesDict[module]:
			if (numberInput.focus == True):
				if (reverse == True):
					return numberInput.selectPreviousInput(module, i)
				else:
					return numberInput.selectNextInput(module, i)
			i += 1

		numberInput.selectInput(module, 0)

	@staticmethod
	def selectInput(module, index):
		NumberInput.modulesDict[module][index].focus = True

	@staticmethod
	def selectNextInput(module, index):
		nextIndex = (index + 1) % len(NumberInput.modulesDict[module])
		NumberInput.selectInput(module, nextIndex)

	@staticmethod
	def selectPreviousInput(module, index):
		nextIndex = (index - 1) % len(NumberInput.modulesDict[module])
		NumberInput.selectInput(module, nextIndex)

	def insert_text(self, substring, from_undo = False):
		if (substring in "0123456789"):
			super(NumberInput, self).insert_text(substring, from_undo = from_undo)
			if (len(self.text) > 1 and self.text[0] == '0'):
				self.text = self.text[1:]

	def __init__(self, **kwargs):
		super(NumberInput, self).__init__(**kwargs)
		if ('module' in kwargs and kwargs['module']):
			self.__module = kwargs['module']
			if (self.__module not in NumberInput.modulesDict):
				NumberInput.modulesDict[self.__module] = [self]
			else:
				NumberInput.modulesDict[self.__module].append(self)
		else:
			self.__module = None

class CancelableButton (Button):
	def __getActionByEntry(self, key, dictToLook):
		if (key in dictToLook):
			self.__action = dictToLook[key]
			del dictToLook[key]
			return True

		else:
			return False

	def __processAction(self, touch):
		if (self.collide_point(*touch.pos) == True and self.__lastUid != touch.uid and touch.uid == self.__touchUpUid):
			self.__lastUid = touch.uid
			self.__action(self, touch)

		self.__default_on_touch_up(touch)

	def __startButtonSelection(self, touch):
		if (self.collide_point(*touch.pos) == True):
			self.__touchUpUid = touch.uid

		self.__default_on_touch_down(touch)

	def __init__(self, **kwargs):
		assert (not ('on_release' in kwargs and 'on_touch_up' in kwargs))

		if (self.__getActionByEntry('on_release', kwargs) == False and self.__getActionByEntry('on_touch_up', kwargs) == False):
			self.__action = None

		super(CancelableButton, self).__init__(**kwargs)
		if (self.__action is not None):
			self.__lastUid = None
			self.__touchUpUid = None
			self.__default_on_touch_up = self.on_touch_up
			self.on_touch_up = self.__processAction
			self.__default_on_touch_down = self.on_touch_down
			self.on_touch_down = self.__startButtonSelection

class EmptyScrollEffect(ScrollEffect):
	pass

class AlignedLabel(Label):
	def __set_on_size(self, obj, new_texture_size):
		if (obj.width != 100 and obj.height != 100):
			obj.text_size = obj.size
		#print obj.size
		#print new_texture_size
		#print obj.texture_size
		#print obj.text_size

	def __init__(self, **kwargs):
		super(AlignedLabel, self).__init__(**kwargs)
		self.bind(size = self.__set_on_size)


class BaseWarnMethods(KeyboardAccess):
	def open(self):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.mainPopUp.open()

	def setTitle(self, value):
		self.mainPopUp.title = value

	def setText(self, value):
		self.mainPopUpText.text = value

class Dialog(BaseWarnMethods):
	def __doNothing(self, notUsed = None):
		return None

	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.__processCancel()

	def __processCancel(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.mainPopUp.dismiss()
		if (self.__afterCancelAction is not None):
			self.__afterCancelAction()

	def __processOk(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.mainPopUp.dismiss()
		self.__okMethod()
		if (self.__afterOkAction is not None):
			self.__afterOkAction()

	def __init__(self, okMethod = None, dialogTitle = '', dialogText = '', dialogOkButtonText = '',
			dialogCancelButtonText = '', afterOkAction = None, afterCancelAction = None):

		self.mainPopUp = Popup(title = dialogTitle, auto_dismiss = False, size_hint = (0.7, 0.5))
		self.mainPopUpText = Label(text = dialogText)
		popUpLayout = BoxLayout(orientation = 'vertical')
		yesNoLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.3))

		if (okMethod is None):
			self.__okMethod = self.__doNothing
		else:
			self.__okMethod = okMethod

		self.__afterOkAction = afterOkAction
		self.__afterCancelAction = afterCancelAction

		self.__dialogOkButton = CancelableButton(text = dialogOkButtonText, on_release = self.__processOk)
		popUpLayout.add_widget(self.mainPopUpText)
		yesNoLayout.add_widget(self.__dialogOkButton)
		yesNoLayout.add_widget(CancelableButton(text = dialogCancelButtonText, on_release = self.__processCancel))
		popUpLayout.add_widget(yesNoLayout)
		self.mainPopUp.content = popUpLayout

class AlertPopUp (BaseWarnMethods):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.__processClose()

	def __processClose(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.mainPopUp.dismiss()
		if (self.__processCloseAction is not None):
			self.__processCloseAction()

	def __init__(self, alertTitle = '', alertText = '', closeButtonText = '', processCloseAction = None):
		self.mainPopUp = Popup(
			title = alertTitle,
			auto_dismiss = False,
			size_hint = (0.5, 0.5)
		)
		self.__processCloseAction = processCloseAction
		mainPopUpBox = BoxLayout(orientation = 'vertical')
		self.mainPopUpText = Label(
			text = alertText, size_hint = (1.0, 0.7)
		)
		mainPopUpBox.add_widget(self.mainPopUpText)
		mainPopUpBox.add_widget(CancelableButton(text = closeButtonText, size_hint = (1.0, 0.3),
			on_release = self.__processClose))
		self.mainPopUp.content = mainPopUpBox

class FileSelectionPopup:
	def __setFilenameWithoutTheFullPath(self, entry, notUsed = None):
		sepIndex = entry[0].rfind(pathSeparator)
		if (sepIndex != -1):
			self.__chosenFileInput.text = entry[0][sepIndex+1:]
		else:
			self.__chosenFileInput.text = entry[0]

	def __init__(self, title = '', filters = ['*'], cancelButtonText = 'Cancel', size = (1.0, 1.0)):
		self.__contentPopup = Popup(title = title, auto_dismiss = False, size = size)
		self.__chosenFileInput = TextInput (text = '', multiline = False)
		self.__fileChooser = FileChooserIconView(path = getcwd(), filters = filters)
		self.__fileChooser.on_submit = self.__setFilenameWithoutTheFullPath
		self.__cancelButton = CancelableButton(text = cancelButtonText, on_release = self.__contentPopup.dismiss)

	def getFileChooser (self):
		return self.__fileChooser

	def getTextInput (self):
		return self.__chosenFileInput

	def getCancelButton(self):
		return self.__cancelButton

	def setContent(self, value):
		self.__contentPopup.content = value

	def open(self, *args):
		self.__contentPopup.open()

	def dismiss(self, *args):
		self.__contentPopup.dismiss()


class AutoReloadTexture:
	def _reloadTexture(self, textureToReload):
		textureToReload.blit_buffer(self._pixels, colorfmt='rgba', bufferfmt='ubyte')
		textureToReload.flip_vertical()

	def __init__(self, sizeToUse, imageToUse):
		self._size = sizeToUse
		self._texture = Texture.create(size = self._size)
		self._pixels = imageToUse.texture.pixels[:]
		self._texture.blit_buffer(self._pixels, colorfmt='rgba', bufferfmt='ubyte')
		self._texture.flip_vertical()
		self._texture.add_reload_observer(self._reloadTexture)

	def getTexture(self):
		return self._texture

def convertKivyCoordToOrxCoord(v, maxY):
	assert len(v) == 2 or len(v) == 3
	if (len(v) == 2):
		return (v[0], maxY - v[1])
	else:
		return (v[0], maxY - v[1], v[2])

def strToDoubleFloatTuple(s):
	assert(type(s) is str)
	splitted = s.split(',')
	assert(len(splitted) == 2)
	x = float(splitted[0].replace('(', ''))
	y = float(splitted[1].replace(')', ''))
	return (x, y)

def strToDoubleIntTuple(s):
	assert(type(s) is str)
	splitted = s.split(',')
	assert(len(splitted) == 2)
	x = int(splitted[0].replace('(', ''))
	y = int(splitted[1].replace(')', ''))
	return (x, y)

def vector2ToVector3String(v, default = 0):
	return '(' + str(v[0]) + ', ' + str(v[1]) + ', ' + str (default) + ')'

def vector2Multiply(v, x):
	assert(type(v) is tuple or type(v) is list)
	assert(len(v) == 2)
	if (type(v) is tuple):
		return (v[0] * x, v[1] * x)
	else:
		return [v[0] * x, v[1] * x]

def boolToStr(b):
	if (b == True):
		return 'true'
	else:
		return 'false'

def strToBool(s):
	assert(s in ['true', 'false'])
	if (s == 'true'):
		return True
	else:
		return False

def isClockWise(points):
	assert type(points) is list or type(points) is tuple, 'Type is not supported.'
	assert len(points) > 2, 'At least three points are needed.'
	numberOfPoints = len(points)
	total = 0
	for i in range(numberOfPoints):
		if (i == (numberOfPoints - 1)):
			total += ((points[0][0] - points[i][0]) * (points[0][1] + points[i][1]))
		else:
			total += ((points[i+1][0] - points[i][0]) * (points[i+1][1] + points[i][1]))

	if (total < 0):
		return True
	else:
		return False


def copyTexture(sizeToUse, imageToUse):
	newTexture = Texture.create(size = sizeToUse)
	pixels = imageToUse.texture.pixels[:]
	newTexture.blit_buffer(pixels, colorfmt='rgba', bufferfmt='ubyte')
	newTexture.flip_vertical()

	return newTexture

def distance(pos1, pos2):
	fx, fy = pos1
	sx, sy = pos2
	return sqrt((fx - sx) * (fx - sx) + (fy - sy) * (fy - sy))

def createSpriteImage(baseImage, x, y, width, height):
	newTexture = baseImage.texture.get_region(x, y, width, height)
	return Image(texture = newTexture, size = (width, height), size_hint = (None, None))

def isConvexPolygon(points):
	assert type(points) is list or type(points) is tuple, 'Type is not supported.'
	assert len(points) > 2, 'At least three points are needed.'
	allPositive = True
	allNegative = True
	for i in range(len(points)):
		dx1 = points[i-1][0] - points[i-2][0]
		dy1 = points[i-1][1] - points[i-2][1]
		dx2 = points[i][0] - points[i-1][0]
		dy2 = points[i][1] - points[i-1][1]
		product = dx1 * dy2 - dy1 * dx2
		if (product > 0):
			allNegative = False
		if (product < 0):
			allPositive = False

	if (allNegative == True or allPositive == True):
		return True
	else:
		return False

