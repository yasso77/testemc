import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from django.shortcuts import render

def generate_barcode(request, code):
    # Get the barcode class (Code128 is a widely used barcode format)
    barcode_format = barcode.get_barcode_class('code128')
    
    # Generate barcode
    barcode_instance = barcode_format(code, writer=ImageWriter())

    # Save the barcode image to an in-memory buffer
    buffer = BytesIO()
    barcode_instance.write(buffer)

    # Convert the image buffer to a base64 string
    barcode_data = base64.b64encode(buffer.getvalue()).decode()

    # Pass barcode data to the template
    return  barcode_data
