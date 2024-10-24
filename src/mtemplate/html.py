from mtemplate import MTemplateProject
from pathlib import Path


__all__ = ['MTemplateHTMLProject']


class MTemplateHTMLProject(MTemplateProject):

    template_dir = Path(__file__).parent.parent.parent / 'templates/html'
    dist_dir = Path(__file__).parent.parent.parent / 'dist/html'

    module_prefixes = [
        str(template_dir / 'srv/sample')
    ]

    model_prefixes = [
        str(template_dir / 'tests/sample'),
        str(template_dir / 'srv/sample/sample-item')
    ]

    def init_template_vars(self):
        super().init_template_vars()
        self.spec['macro'].update({
        })
