from kivy.uix.scrollview import ScrollView

class SpecialScrollControl (object):

	def setIsShiftPressed(self, value):
		self._isShiftPressed = value
	
	def setIsCtrlPressed(self, value):
		self._isCtrlPressed = value

	def specialScroll(self, touch):
		if (self._isShiftPressed == False):
			if (touch.button == "scrollup" and self._scrollView.scroll_y > 0):
				self._scrollView.scroll_y -= 0.05
			elif (touch.button == "scrolldown" and self._scrollView.scroll_y < 1.0):
				self._scrollView.scroll_y += 0.05
		else:
			if (touch.button == "scrolldown" and self._scrollView.scroll_x > 0):
				self._scrollView.scroll_x -= 0.05
			elif (touch.button == "scrollup" and self._scrollView.scroll_x < 1.0):
				self._scrollView.scroll_x += 0.05
	
	def __init__(self, **kwargs):
		self._isShiftPressed = False
		self._isCtrlPressed = False
		
		if ('scroll_timeout' in kwargs):
			del kwargs['scroll_timeout']
	
		kwargs['scroll_timeout'] = 0.
		
		self._scrollView = ScrollView(**kwargs)
	
	def getLayout(self):
		return self._scrollView

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

