from singleton import Singleton

from kivy.uix.accordion import Accordion, AccordionItem

from filesoptionsmenu import FilesOptionsMenu
from objectdescriptor import BaseObjectDescriptor, RenderedObjectDescriptor, ObjectDescriptor

@Singleton
class OptionsMenu:
	def __init__(self, rightScreen, maxWidthProportion = 1.0, maxHeightProportion = 0.333):

		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion

		self.__layout = Accordion(orientation = 'horizontal', size_hint = (maxWidthProportion, maxHeightProportion))
		self.__accordionItems = {
			'BaseObject' : AccordionItem(title = 'Base Objects'),
			'RenderedObject' : AccordionItem (title = 'Rendered Object'),
			'Options' : AccordionItem(title = 'Options'),
		}

		self.__layout.add_widget(self.__accordionItems['BaseObject'])
		self.__layout.add_widget(self.__accordionItems['RenderedObject'])
		self.__layout.add_widget(self.__accordionItems['Options'])
		
		FilesOptionsMenu.Instance(self.__accordionItems['Options'], None, None, None)
		ObjectDescriptor.Instance(self.__accordionItems['BaseObject'], self.__accordionItems['RenderedObject'])

		rightScreen.add_widget(self.__layout)

