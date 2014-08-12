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
		assert (self.__stack[-1] == obj)
		obj.dropKeyboardAccess()
		self.__stack.pop()

	def __init__(self):
		self.__stack = []


class KeyboardAccess (object):

	def _processKeyDown(self, keyboard, keycode):
		pass

	def _processKeyUp(self, keyboard, keycode):
		pass

	def dropKeyboardAccess(self):
		self.__keyboard.unbind(on_key_down=self.__processKeyDown)
		self.__keyboard.unbind(on_key_up=self.__processKeyUp)
	
	def acquireKeyboardAccess(self):
		self.__keyboard = Window.request_keyboard(self.__finishKeyboard, self)
	
		self.__keyboard.bind(on_key_down = self._processKeyDown)
		self.__keyboard.bind(on_key_up = self._processKeyUp)

	
