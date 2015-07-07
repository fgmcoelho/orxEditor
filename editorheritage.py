from kivy.uix.scrollview import ScrollView
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from string import letters, digits
from uisizes import defaultInputSize, defaultSmallButtonSize

class SpaceLimitedObject (object):
	def ajustPositionByLimits(self, x, y, sx, sy, maxX, maxY):
		if (x < 0):
			x = 0
		elif (x + sx > maxX):
			x = maxX - sx

		if (y < 0):
			y = 0
		elif (y + sy > maxY):
			y = maxY - sy

		return (int(x), int(y))

class IgnoreTouch(object):
	def _ignoreTouch(self, *args):
		pass

class LayoutGetter(object):
	def getLayout(self):
		return self._layout

class SeparatorLabel(object):
	def getSeparator(self):
		for separator in self._separatorList:
			if (separator.parent == None):
				return separator

		newSeparator = Label(text = '', size_hint = (1.0, 1.0))
		self._separatorList.append(newSeparator)
		return newSeparator

	def __init__(self):
		super(SeparatorLabel, self).__init__()
		self._separatorList = []

class KeyboardModifiers(object):
	def __init__(self, **kwargs):
		super(KeyboardModifiers, self).__init__()
		self._isShiftPressed = False
		self._isCtrlPressed = False

	def setIsShiftPressed(self, value):
		self._isShiftPressed = value

	def setIsCtrlPressed(self, value):
		self._isCtrlPressed = value

class MouseModifiers(object):
	def __init__(self, **kwargs):
		super(MouseModifiers, self).__init__()
		self._isLeftPressed = False
		self._isRightPressed = False
		self._isMiddlePressed = False

	def __updateMouseStatus(self, touch, status):
		if (touch.button == "left"):
			self._isLeftPressed = status
		elif (touch.button == "right"):
			self._isRightPressed = status
		elif (touch.button == "middle"):
			self._isMiddlePressed = status

	def updateMouseUp(self, touch):
		self.__updateMouseStatus(touch, False)

	def updateMouseDown(self, touch):
		self.__updateMouseStatus(touch, True)

class SpecialScrollControl (KeyboardModifiers):
	def __applyZoom(self, magnitude):
		self._zoom *= magnitude
		for obj in self._zoomList:
			assert(isinstance(obj, Scatter))
			obj.scale = self._zoom

	def _ignoreMoves(self, touch):
		return None

	def specialScroll(self, touch):
		if (self._isCtrlPressed == True):
			if (touch.button == "scrollup" and self._zoom > 0.25):
				self.__applyZoom(0.5)

			elif (touch.button == "scrolldown" and self._zoom < 4):
				self.__applyZoom(2.0)
		else:
			if (self._isShiftPressed == False):
				if (touch.button == "scrollup" and self._scrollView.scroll_y > 0):
					if (self._scrollView.scroll_y - 0.05 < 0.0):
						self._scrollView.scroll_y = 0.0
					else:
						self._scrollView.scroll_y -= 0.05

				elif (touch.button == "scrolldown" and self._scrollView.scroll_y < 1.0):
					if (self._scrollView.scroll_y + 0.05 > 1.0):
						self._scrollView.scroll_y = 1.0
					else:
						self._scrollView.scroll_y += 0.05
			else:
				if (touch.button == "scrolldown" and self._scrollView.scroll_x > 0):
					if (self._scrollView.scroll_x - 0.05 < 0.0):
						self._scrollView.scroll_x = 0.0
					else:
						self._scrollView.scroll_x -= 0.05

				elif (touch.button == "scrollup" and self._scrollView.scroll_x < 1.0):
					if (self._scrollView.scroll_x + 0.05 > 1.0):
						self._scrollView.scroll_x = 1.0
					else:
						self._scrollView.scroll_x += 0.05

	def __init__(self, **kwargs):
		super(SpecialScrollControl, self).__init__(**kwargs)

		if ('scroll_timeout' in kwargs):
			del kwargs['scroll_timeout']

		kwargs['scroll_timeout'] = 0.

		self._scrollView = ScrollView(**kwargs)
		self._scrollView.scroll_x = 0.
		self._scrollView.scroll_y = 0.
		self._scrollView.scroll_y = 1.
		self._zoomList = []
		self._zoom = 1

	def getLayout(self):
		return self._scrollView

class AutoFocusInputUser(object):
	# Overloaded method
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

		elif (keycode[1] in self._validCharacters and self._autoFocusInput.focus == False):
			self._autoFocusInput.insert_text(keycode[1])
			self._autoFocusInput.focus = True

	def __init__(self):
		super(AutoFocusInputUser, self).__init__()
		self._validCharacters = letters + digits
		self._autoFocusInput = TextInput(multiline = False, **defaultInputSize)
		self._addButtonSize = {
			'height' : defaultInputSize['height'],
			'width' : defaultSmallButtonSize['width'],
			'size_hint' : (None, None),
		}

	def _delayedFocus(self, *args):
		self._autoFocusInput.focus = True
