import tkinter
from tkinter import ttk
from core.client import create_client_context
# for :: {% for module in modules.values() %} :: {"template_module": "module.name.snake_case", "TemplateModule": "module.name.pascal_case"}
from core.types import Fonts
from template_module.gui import TemplateModuleIndexPage
# end for :: rstrip
# for :: {% for item in all_models %} :: {"template_module": "item.module.name.snake_case", "single_model": "item.model.name.snake_case", "SingleModel": "item.model.name.pascal_case"}
from template_module.single_model.gui import SingleModelIndexPage, SingleModelInstancePage
# end for :: rstrip
# ignore ::
from template_module.multi_model.gui import MultiModelIndexPage, MultiModelInstancePage
# end ignore ::

def gui_main(start_frame='MSpecIndexPage'):
    app = MSpecGUIApp(start_frame)
    app.mainloop()
    
class MSpecIndexPage(tkinter.Frame):
     
    def __init__(self, parent, controller:'MSpecGUIApp'): 
        super().__init__(parent)

        label = ttk.Label(self, text='mspec', font=Fonts.heading1)
        label.grid(row=0, column=0)

        # for :: {% for module in modules.values() %} :: {"TemplateModule": "module.name.pascal_case", "template module": "module.name.lower_case", "1": "loop.index"}
        button1 = ttk.Button(self, text='template module', command=lambda: controller.show_frame(TemplateModuleIndexPage))
        button1.grid(row=1, column=0)
        # end for ::

class MSpecGUIApp(tkinter.Tk):

    frame_classes = (
        MSpecIndexPage, 
        # for :: {% for module in modules.values() %} :: {"TemplateModule": "module.name.pascal_case"}
        TemplateModuleIndexPage,
        # end for ::
        # for :: {% for item in all_models %} :: {"SingleModel": "item.model.name.pascal_case"}
        SingleModelIndexPage,
        SingleModelInstancePage,
        # end for ::
        # ignore ::
        MultiModelIndexPage,
        MultiModelInstancePage
        # end ignore ::
    )

    def __init__(self, start_frame='MSpecIndexPage'):
        super().__init__()
        self.title('mspec')
        self.geometry('1000x800')

        self.ctx = create_client_context()
        
        container = tkinter.Frame(self)
        container.grid(column=0, row=0, sticky='nsew')
  
        self.frames = {}
        self.current_frame = None
  
        for frame_class in self.frame_classes:
            self.frames[frame_class] = frame_class(container, self)
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

        on_show_frame = getattr(frame, 'on_show_frame', None)
        if on_show_frame:
            on_show_frame(**kwargs)
        else:
            print(f"Frame {frame_class} has no on_show_frame method")

        self.current_frame = frame

    def show_frame_str(self, frame_class_str, **kwargs):
        frame_class = globals()[frame_class_str]
        self.show_frame(frame_class, **kwargs)

    def show_index_frame(self, **kwargs):
        self.show_frame(MSpecIndexPage, **kwargs)

if __name__ == '__main__':

    import argparse

    _default_start_frame = 'MSpecIndexPage'
    parser = argparse.ArgumentParser(description='Run the gui')
    parser.add_argument('--start-frame', help=f'start frame for gui, default: {_default_start_frame}', default=_default_start_frame)
    args = parser.parse_args()

    gui_main(args.start_frame)
