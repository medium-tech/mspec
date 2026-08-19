MIN_LINE_BREAKS = 1
MAX_LINE_BREAKS = 5

MIN_HEADING_LEVEL = 1
MAX_HEADING_LEVEL = 6

PRIMARY_FONT_FAMILY = 'Verdana'

# https://docs.python.org/3/library/tkinter.html#tkinter.Text.tag_configure
HEADING_FONTS = {
	1: {
		'font': {'family': PRIMARY_FONT_FAMILY, 'size': 35},
		'options': {
			'spacing1': 0,
			'spacing2': 0,
			'spacing3': 0,
		}
	},
	2: {
		'font': {'family': PRIMARY_FONT_FAMILY, 'size': 30},
		'options': {
			'spacing1': 0,
			'spacing2': 0,
			'spacing3': 0,
		}
	},
	3: {
		'font': {'family': PRIMARY_FONT_FAMILY, 'size': 25},
		'options': {
			'spacing1': 0,
			'spacing2': 0,
			'spacing3': 0,
		}
	},
	4: {
		'font': {'family': PRIMARY_FONT_FAMILY, 'size': 20},
		'options': {
			'spacing1': 0,
			'spacing2': 0,
			'spacing3': 0,
		}
	},
	5: {
		'font': {'family': PRIMARY_FONT_FAMILY, 'size': 18},
		'options': {
			'spacing1': 0,
			'spacing2': 0,
			'spacing3': 0,
		}
	},
	6: {
		'font': {'family': PRIMARY_FONT_FAMILY, 'size': 16},
		'options': {
			'spacing1': 0,
			'spacing2': 0,
			'spacing3': 0,
		}
	}
}

DEFAULT_TEXT_SIZE = 14

TEXT_FONT = {
	'font': {'family': PRIMARY_FONT_FAMILY, 'size': DEFAULT_TEXT_SIZE},
	'options': {
		'spacing1': 0,
		'spacing2': 0,
		'spacing3': 0,
	}
}

MONOSPACE_FONT = ('Courier New', DEFAULT_TEXT_SIZE)

TABLE_HEADER_FONT = {
	'font': {'family': MONOSPACE_FONT[0], 'size': DEFAULT_TEXT_SIZE, 'weight': 'bold'},
}
TABLE_TEXT_FONT = {
	'font': {'family': MONOSPACE_FONT[0], 'size': DEFAULT_TEXT_SIZE},
}

ERROR_TEXT_FONT = {
	'font': {'family': MONOSPACE_FONT[0], 'size': DEFAULT_TEXT_SIZE, 'weight': 'bold', 'color': 'red'},
}

BUTTON_FONT = {
	'font': {'family': PRIMARY_FONT_FAMILY, 'size': DEFAULT_TEXT_SIZE}
}
BUTTON_BACKGROUND_COLOR = 'white'
BUTTON_TEXT_COLOR = 'black'
BUTTON_PADDING_X = 2
BUTTON_PADDING_Y = 4
BUTTON_MARGIN_X = 5
BUTTON_MARGIN_Y = 6
BUTTON_BORDER_WIDTH = 1
BUTTON_RELIEF = 'raised'						# raised, sunken, flat, ridge, solid, and groove
BUTTON_FOCUS_HIGHLIGHT_THICKNESS = 1
BUTTON_FOCUS_HIGHLIGHT_COLOR = '#5b9dd9'
BUTTON_FOCUS_HIGHLIGHT_BACKGROUND = 'white'
BUTTON_CURSOR = 'hand2'						# https://www.tcl-lang.org/man/tcl8.6/TkCmd/cursors.htm