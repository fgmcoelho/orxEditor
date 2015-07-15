from platform import system, machine
from os import fork, execve, environ, getcwd, chdir, mkdir
from os.path import join, isfile, exists
from modulesaccess import ModulesAccess
from urllib import urlretrieve

class OrxViewer:
	def _filename(self):
		return "viewer_" + self.__system + "_" + self.__arch

	#def _download(self):
	#	if (exists('tmp') == True)

	def launch(self):
		try:
			ModulesAccess.get("FilesManager").exportScene(
				join(getcwd(), "bin", self._filename() + ".ini"),
				join(getcwd(), "tiles"),
				True,
				self.__defaults
			)

			pid = fork()
			if (pid != 0):
				chdir("bin")
				execve(self._filename(), [self._filename()], self.__environ)
		except Exception, e:
			print "Error launching the application: " + str(e)

	def __init__(self):
		ModulesAccess.add("OrxViewer", self)
		arch = machine()
		if (arch.find("64") != -1):
			self.__arch = "64"
		else:
			self.__arch = "32"
		self.__system = system().lower()
		self.__environ = environ.copy()
		print self.__system
		if (self.__system == "linux"):
			if (self.__environ.has_key("LD_LIBRARY_PATH") == True):
				self.__environ['LD_LIBRARY_PATH'] += ":."
			else:
				self.__environ['LD_LIBRARY_PATH'] = "."

		self.__defaults = {
			"Display": {
				"ScreenWidth":  "800",
				"ScreenHeight": "600",
				"Title":        "OrxViewer",
				"RefreshRate":  "60",
				"VSync" :       "true",
			},

			"Viewport": {
				"Camera":          "Camera",
				"BackgroundColor": "(0x00, 0x11, 0x2B)",
			},

			"Resource": {
				"Texture": "../tiles/",
			},

			"Camera": {
				"GroupList":     "@General.GroupList",
				"FrustumWidth":  "@Display.ScreenWidth",
				"FrustumHeight": "@Display.ScreenHeight",
				"FrustumFar":    "2.0",
				"Zoom":          "1.0",
			},

			"Input": {
				"SetList": "MainInput",
			},

			"Physics" : {
				"ShowDebug": "true",
			},

			"MainInput": {
				"KEY_ESCAPE": "Quit",
				"KEY_UP":     "MoveUp",
				"KEY_DOWN":   "MoveDown",
				"KEY_LEFT":   "MoveLeft",
				"KEY_RIGHT":  "MoveRight",
			},
		}
