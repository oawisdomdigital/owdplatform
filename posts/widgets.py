# widgets.py
from django.forms.widgets import ClearableFileInput
from django.utils.html import format_html

class CustomFileInput(ClearableFileInput):
    template_name = 'widgets/custom_file_input.html'

    def __init__(self, *args, **kwargs):
        self.href = kwargs.pop('href', None)
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        substitutions = {
            'initial': self.initial_text,
            'input': super().render(name, value, attrs, renderer),
        }
        template = '%(input)s'
        if self.href:
            substitutions['href'] = self.href
            template = '<a href="%(href)s" target="_blank">%(initial)s</a> ' + template
        return format_html(template, **substitutions)


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True
