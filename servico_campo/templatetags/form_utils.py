from django import template

register = template.Library()


@register.filter(name='add_css_class')
def add_css_class(field, class_name):
    css_class = field.field.widget.attrs.get('class', '')
    field.field.widget.attrs['class'] = f'{css_class} {class_name}'.strip()
    if field.errors:
        field.field.widget.attrs['class'] += ' is-invalid'
    return field
