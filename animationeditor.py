from kivy.uix.boxlayout import BoxLayout


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

class AnimationEditor:
	def __init__(self):
		self._layout = BoxLayout(orientation = 'vertical')


