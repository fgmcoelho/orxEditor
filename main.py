from kivy.app import App
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

class orxEditor(App):
	

    def build_config(self, c):
        Config.set('graphics', 'width', 1280)
        Config.set('graphics', 'height', 1024)
        Config.set('graphics', 'fullscreen', 0)
        #Config.set('graphics', 'width', 320)
        #Config.set('graphics', 'height', 480)
        Config.write()


	def build(self):

		self.root = Button(text = 'x')
		#BoxLayout(orientation='horizontal', padding = 0, spacing = 0, size = (100, 100))
		

		leftMenu = BoxLayout(
			orientation='vertical', 
			padding = 0, 
			spacing = 0,
			size_hint = (0.25, 1)
		)

		

		screenAndBottomMenu = BoxLayoud(
			orientation = 'vertical',
			padding = 0, 
			spacing = 0,
			size_hint = (0.75, 1),
		)

		#leftMenu.add_widget(Button(text = 'x'))

		#self.root.add_widget(leftMenu)
		#self.root.add_widget(screenAndBottomMenu)

		

		#root = ScrollView(size_hint=(None, None), size=(400, 400))
		#root.add_widget(layout)

		return self.root


if __name__ == '__main__':
	orxEditor().run()
