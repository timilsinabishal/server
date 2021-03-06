from datetime import datetime
from .utils import set_filter_data, set_export_data


ONE_DAY = 24 * 60 * 60


def update_attribute(entry, widget, data, widget_data):
    from_value = data.get('from_value')
    to_value = data.get('to_value')

    from_date = from_value and datetime.strptime(from_value, '%Y-%m-%d')
    to_date = to_value and datetime.strptime(to_value, '%Y-%m-%d')

    from_number = from_date and int(from_date.timestamp() / ONE_DAY)
    to_number = to_date and int(to_date.timestamp() / ONE_DAY)
    set_filter_data(
        entry,
        widget,
        from_number=from_number,
        to_number=to_number,
    )

    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'values': [
                    from_date and from_date.strftime('%d-%m-%Y'),
                    to_date and to_date.strftime('%d-%m-%Y'),
                ],
            },
        },
    )
