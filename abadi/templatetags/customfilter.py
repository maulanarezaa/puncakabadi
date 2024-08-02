from django import template

register = template.Library()

@register.filter
def custom_thousands_separator(value):
    try:
        # Format value with 2 decimal places
        formatted_value = f"{value:,.2f}"
        # Replace ',' with 'X' temporarily
        formatted_value = formatted_value.replace(',', 'X')
        # Replace '.' with ','
        formatted_value = formatted_value.replace('.', ',')
        # Replace 'X' with '.'
        formatted_value = formatted_value.replace('X', '.')
        return formatted_value
    except (ValueError, TypeError):
        return value

@register.filter
def separator_ribuan(value):
    try:
        # Format value with commas as thousand separators
        formatted_value = f"{value:,}"
        # Replace commas with dots
        formatted_value = formatted_value.replace(',', '.')
        return formatted_value
    except (ValueError, TypeError):
        return value

@register.filter
def separator_desimal(value):
    try:
        # Convert the float value to a string with the appropriate format
        formatted_value = f"{value:.2f}"
        print(formatted_value)
        # Replace dot with comma for decimal separator
        formatted_value = formatted_value.replace('.', ',')
        return formatted_value
    except (ValueError,TypeError):
        return value
    
@register.filter
def separator_desimal5angka(value):
    try:
        # Convert the float value to a string with the appropriate format
        formatted_value = f"{value:.5f}"
        print(formatted_value)
        # Replace dot with comma for decimal separator
        formatted_value = formatted_value.replace('.', ',')
        return formatted_value
    except (ValueError,TypeError):
        return value
    
