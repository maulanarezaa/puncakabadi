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
        formatted_value = f"{float(value):,.2f}"
        # Replace commas with dots
        formatted_value = formatted_value.replace(',', '.')
        return formatted_value
    except (ValueError, TypeError):
        return value

@register.filter
def separator_ribuand00313(value):
    try:
        # Format value with 2 decimal places
        formatted_value = f"{value:,.3f}"
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
def separator_ribuan_versi2(value):
    try:
        # Format value with commas as thousand separators
        formatted_value = f"{value:,.0f}" if value.is_integer() else f"{value:,.2f}"
        # Replace commas with dots
        formatted_value = formatted_value.replace(',', 'X')
        formatted_value = formatted_value.replace('.', ',')
        formatted_value = formatted_value.replace('X', '.')
        return formatted_value
    except :
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
    
@register.filter
def separator_ribuan2desimal(value):
    try:
        # Memformat nilai dengan 2 angka desimal
        formatted_value = f"{value:,.2f}"
        # Ganti koma dengan titik untuk pemisah ribuan
        formatted_value = formatted_value.replace(',', 'X')  # Sementara ganti koma dengan 'X'
        formatted_value = formatted_value.replace('.', ',')  # Ganti titik (desimal) dengan koma
        formatted_value = formatted_value.replace('X', '.')  # Ganti 'X' dengan titik untuk ribuan
        return formatted_value
    except (ValueError, TypeError):
        return value