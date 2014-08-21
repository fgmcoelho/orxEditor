from singleton import Singleton
from kivy.core.window import Window

@Singleton
class KeyboardGuardian:

	def acquireKeyboard(self, obj):
		assert (isinstance(obj, KeyboardAccess))
		if (self.__stack != []):
			self.__stack[-1].dropKeyboardAccess()
		
		self.__stack.append(obj)
		obj.acquireKeyboardAccess()
		
	def dropKeyboard(self, obj):
		assert (isinstance(obj, KeyboardAccess))
		assert (self.__stack != [])
		
		# There are some times where you can press a button
		# twice too fast, which would cause the function to
		# be called twice.
		if(self.__stack[-1] != obj):
			return
		
		obj.dropKeyboardAccess()
		self.__stack.pop()
		if (self.__stack != []):
			self.__stack[-1].acquireKeyboardAccess()

	def __init__(self):
		self.__stack = []

class KeyboardAccess (object):

	def _processKeyDown(self, keyboard, keycode, text, modifiers):
		pass

	def _processKeyUp(self, keyboard, keycode):
		pass

	def dropKeyboardAccess(self):
		self._keyboard.unbind(on_key_down=self._processKeyDown)
		self._keyboard.unbind(on_key_up=self._processKeyUp)
	
	def acquireKeyboardAccess(self):
		self._keyboard = Window.request_keyboard(None, None)
	
		self._keyboard.bind(on_key_down = self._processKeyDown)
		self._keyboard.bind(on_key_up = self._processKeyUp)

	
