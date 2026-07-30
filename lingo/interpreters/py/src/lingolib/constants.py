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

TEXT_FONT = {
	'font': {'family': PRIMARY_FONT_FAMILY, 'size': 12},
	'options': {
		'spacing1': 0,
		'spacing2': 0,
		'spacing3': 0,
	}
}

MONOSPACE_FONT = ('Courier New', 12)

TABLE_HEADER_FONT = {
	'font': {'family': MONOSPACE_FONT[0], 'size': 12, 'weight': 'bold'},
}
TABLE_TEXT_FONT = {
	'font': {'family': MONOSPACE_FONT[0], 'size': 12},
}