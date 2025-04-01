import tkinter
from tkinter import ttk
from lingo.expressions import lingo_app, example_spec, render_document, lingo_execute

HEADING = {
    1: ('Verdana', 35),
    2: ('Verdana', 30),
    3: ('Verdana', 25),
    4: ('Verdana', 20),
    5: ('Verdana', 18),
    6: ('Verdana', 16),
}

TEXT = ('Verdana', 12)
  
#
#
#

def gui_main(start_frame='LingoPage'):
    app = LingoGUIApp(start_frame)
    app.mainloop()
    
class LingoPage(tkinter.Frame):
     
    def __init__(self, parent): 
        super().__init__(parent)

        self._text_buffer_open = False
        self._text_buffer = None
        self._text_first_row = -1
        self._text_row_count = 0

        self.app = lingo_app(example_spec)
        self.render_document()

    def _render_line_buffer(self):
        self._text_buffer.grid(row=self._line_buffer_row, column=0, padx=0)
        self._text_buffer.tag_configure('link', foreground='blue', underline=1)
        self._text_buffer.config(state=tkinter.DISABLED)

    def _open_line_buffer(self, row:int):
        if not self._text_buffer_open:
            self._text_buffer_open = True
            self._text_buffer = tkinter.Text(self, font=TEXT, wrap='word', height=10, width=100, highlightthickness=0)
            self._line_buffer_row = row
        else:
            self._text_row_count += 1

    def _close_line_buffer(self):
        if self._text_buffer_open:
            self._render_line_buffer()
            self._text_buffer_open = False
            self._text_first_row = -1
            self._text_row_count = 0

    def render_document(self):
        doc = render_document(self.app)

        for n, element in enumerate(doc):
            if 'heading' in element:
                self.render_heading(n, element)
            elif 'link' in element:
                self.render_link(n, element)
            elif 'button' in element:
                self.render_button(n, element)
            elif 'break' in element:
                self.render_break(n, element)
            elif 'input' in element:
                self.render_input(n, element)
            elif 'text' in element:
                self.render_text(n, element)
            else:
                raise ValueError('Unknown element type')
        
        self._close_line_buffer()

    def render_heading(self, row:int, element:dict):
        self._close_line_buffer()
        label = ttk.Label(self, text=element['heading'], font=HEADING[element['level']])
        label.grid(row=row, column=0) 

    def render_text(self, row:int, element:dict):
        self._open_line_buffer(row)
        self._text_buffer.insert(tkinter.END, element['text'])

    def render_break(self, row:int, element:dict):
        self._open_line_buffer(row)
        self._text_buffer.insert(tkinter.END, '\n' * element['break'])

    def render_button(self, row:int, element:dict):
        self._close_line_buffer()
        button = ttk.Button(self, text=element['text'], command=lambda: lingo_execute(self.app, element['button']))
        button.grid(row=row, column=0, padx=5)

    def render_input(self, row:int, element:dict):
        self._close_line_buffer()
        self.render_text(row, {'text': '* input place holder *'})

    def render_link(self, row:int, element:dict):
        try:
            display_text = element['text']
        except KeyError:
            display_text = element['link']

        self._open_line_buffer(row)
        self._text_buffer.insert(tkinter.END, display_text, ('link',))



class LingoGUIApp(tkinter.Tk):

    frame_classes = (
        LingoPage,
    )

    def __init__(self, start_frame='LingoPage'):
        super().__init__()
        self.title('lingo')
        self.geometry('1000x800')
        
        container = tkinter.Frame(self)
        container.grid(column=0, row=0, sticky='nsew')
  
        self.frames = {}
        self.current_frame = None
  
        for frame_class in self.frame_classes:
            self.frames[frame_class] = frame_class(container)
            self.frames[frame_class].grid(row=0, column=0, sticky='nsew')
            self.frames[frame_class].forget()
  
        self.show_frame_str(start_frame)
  
    def show_frame(self, frame_class, **kwargs):
        frame = self.frames[frame_class]
        frame.grid(row=0, column=0, sticky='nsew')
        frame.tkraise()

        try:
            self.current_frame.forget()
        except AttributeError:
            """self.current_frame is None"""

        try:
            frame.on_show_frame(**kwargs)
        except AttributeError:
            pass

        self.current_frame = frame

    def show_frame_str(self, frame_class_str, **kwargs):
        frame_class = globals()[frame_class_str]
        self.show_frame(frame_class, **kwargs)

if __name__ == '__main__':
    gui_main()
