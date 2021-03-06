from . import (
    date_widget,
    date_range_widget,
    time_widget,
    number_widget,
    scale_widget,
    select_widget,
    multiselect_widget,
    geo_widget,
    organigram_widget,
    matrix1d_widget,
    matrix2d_widget,
    number_matrix_widget,
)


widget_store = {
    'dateWidget': date_widget,
    'dateRangeWidget': date_range_widget,
    'timeWidget': time_widget,
    'numberWidget': number_widget,
    'scaleWidget': scale_widget,
    'selectWidget': select_widget,
    'multiselectWidget': multiselect_widget,
    'geoWidget': geo_widget,
    'organigramWidget': organigram_widget,
    'matrix1dWidget': matrix1d_widget,
    'matrix2dWidget': matrix2d_widget,
    'numberMatrixWidget': number_matrix_widget,
}
