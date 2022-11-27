import PIL.Image
import io
import base64

buffer = io.BytesIO()
img = PIL.Image.open('local-static/hh.jpg')
img.save(buffer, format='PNG')
img.save("local-static/hh.ico", format='ICO')

img_str = base64.b64encode(buffer.getvalue())

with open("gui_icon.py", 'w', encoding='utf-8') as f:
    f.write('B64_IMAGE = ')
    f.write(repr(img_str))
    f.write('\n')
