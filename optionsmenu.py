from singleton import Singleton

from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.boxlayout import BoxLayout

from filesoptionsmenu import FilesOptionsMenu
from objectdescriptor import MultipleSelectionDescriptor, ObjectDescriptor

from modulesaccess import ModulesAccess
from editorheritage import LayoutGetter

@Singleton
class OptionsMenu:
	def __init__(self, rightScreen):

		self.__layout = Accordion(orientation = 'horizontal', size_hint = (1.0, None), height = 200)
		self.__accordionItems = {
			'BaseObject' : AccordionItem(title = 'Base Object'),
			'RenderedObject' : AccordionItem (title = 'Rendered Object'),
			'MultipleSelectionDescriptor' : AccordionItem (title = 'Multiple Selection'),
			'Options' : AccordionItem(title = 'Options'),
		}

		self.__layout.add_widget(self.__accordionItems['BaseObject'])
		self.__layout.add_widget(self.__accordionItems['RenderedObject'])
		self.__layout.add_widget(self.__accordionItems['MultipleSelectionDescriptor'])
		self.__layout.add_widget(self.__accordionItems['Options'])

		FilesOptionsMenu.Instance(self.__accordionItems['Options'])
		MultipleSelectionDescriptor.Instance(self.__accordionItems['MultipleSelectionDescriptor'])
		ObjectDescriptor.Instance(self.__accordionItems['BaseObject'], self.__accordionItems['RenderedObject'])

		rightScreen.add_widget(self.__layout)


class NewOptionMenu(LayoutGetter):
	def __init__(self):
		ModulesAccess.add('BottomMenu', self)
		self._layout = BoxLayout(orientation = 'vertical', height = 200)


