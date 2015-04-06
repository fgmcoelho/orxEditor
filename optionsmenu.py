from singleton import Singleton

from kivy.uix.accordion import Accordion, AccordionItem

from filesoptionsmenu import FilesOptionsMenu
from objectdescriptor import MultipleSelectionDescriptor, ObjectDescriptor

@Singleton
class OptionsMenu:
	def __init__(self, rightScreen, maxWidthProportion = 1.0, maxHeightProportion = 0.333):

		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion

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

