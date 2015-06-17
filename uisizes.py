mainLayoutSize = {
	'leftMenuWidth' : 200,
	'leftMenuSizeHint' : (None, 1.0),
	'bottomMenuHeight' : 220
}

options_menu_size = {
	'objectSize' : (mainLayoutSize['leftMenuWidth'] * 0.9, mainLayoutSize['leftMenuWidth'] * 0.9),
	'padding' : 3,
}

defaultFontSize = 20

descriptorSize = {'height' : 200 }

descriptorLabelDefault = {
	'height' : defaultFontSize,
	'shorten' : True,
	'shorten_from' : 'left',
	'size_hint' : (1.0, None)
}

descriptorButtonDefault = {
	'height' : defaultFontSize,
	'width' : 80,
	'shorten' : True,
	'shorten_from' : 'left',
	'size_hint' : (None, None)
}
descriptorButtonDoubleSize = {
	'height' : defaultFontSize,
	'width' : 160,
	'shorten' : True,
	'shorten_from' : 'left',
	'size_hint' : (None, None)
}

buttonDefault = {
	'height' : defaultFontSize,
	'size_hint' : (1.0, None)
}

inputDefault = {
	'height' : defaultFontSize + 10,
	'size_hint' :
	(1.0, None),
	'multiline' : False
}

sceneMiniMapSize = {
	'size' : (200, 200),
}

resourceLoderSize = {
	'width' : 120,
}

warningSize = {
	'size' : (400, 200),
	'size_hint' : (None, None),
}
