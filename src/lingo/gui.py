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

        self.app = lingo_app(example_spec)

        self.render_document()

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


    def render_heading(self, row:int, element:dict):
        label = ttk.Label(self, text=element['heading'], font=HEADING[element['level']])
        label.grid(row=row, column=0) 

    def render_text(self, row:int, element:dict):
        text = tkinter.Label(self, text=element['text'], font=TEXT)
        text.grid(row=row, column=0, padx=0)

    def render_break(self, row:int, element:dict):
        break_ = tkinter.Label(self, text='', font=TEXT)
        break_.grid(row=row, column=0, padx=0)

    def render_button(self, row:int, element:dict):
        button = ttk.Button(self, text=element['text'], command=lambda: lingo_execute(self.app, element['button']))
        button.grid(row=row, column=0, padx=5)

    def render_input(self, row:int, element:dict):
        self.render_text(row, {'text': '* input place holder *'})

    def render_link(self, row:int, element:dict):
        try:
            display_text = element['text']
        except KeyError:
            display_text = element['link']

        link_label = ttk.Label(self, text=display_text, foreground='blue', cursor='hand2')
        link_label.bind("<Button-1>", lambda e: print(f"Link clicked: {element['link']}"))
        link_label.grid(row=row, column=0, padx=5)


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
