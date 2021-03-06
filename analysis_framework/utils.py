from analysis_framework.models import Widget, Filter, Exportable
from .widgets.store import widget_store


def update_widget(widget):
    widget_data = widget.properties and widget.properties.get('data')
    widget_module = widget_store.get(widget.widget_id)

    if hasattr(widget_module, 'get_filters'):
        filters = widget_module.get_filters(widget, widget_data or {}) or []
        for filter in filters:
            filter['title'] = filter.get('title', widget.title)
            Filter.objects.update_or_create(
                analysis_framework=widget.analysis_framework,
                widget_key=widget.key,
                key=filter.get('key', widget.key),
                defaults=filter,
            )

    if hasattr(widget_module, 'get_exportable'):
        exportable = widget_module.get_exportable(widget, widget_data or {})
        if exportable:
            Exportable.objects.update_or_create(
                analysis_framework=widget.analysis_framework,
                widget_key=widget.key,
                defaults={
                    'data': exportable,
                },
            )


def update_widgets(widget_id=None):
    if widget_id:
        widgets = Widget.objects.filter(widget_id=widget_id)
    else:
        widgets = Widget.objects.all()

    for widget in widgets:
        update_widget(widget)
