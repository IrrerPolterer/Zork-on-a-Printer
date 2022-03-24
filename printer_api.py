from PIL import Image, ImageFont, ImageDraw
from StarTSPImage import imageToRaster
from socket import create_connection, error as socket_error
from textwrap import fill
from time import sleep


def text_to_image(text, output=None, font_size=50, font_path=None, text_width=None, padding=(3, 3, 3, 3), fg="#000", bg="#FFF"):

    padding_top, padding_right, padding_bottom, padding_left = padding
    font = ImageFont.load_default() if font_path == None else ImageFont.truetype(font_path, font_size)

    if text_width == None:
        lines = text.replace("\r", "").split("\n")
        text_width = max([len(l) for l in lines])
    else:
        lines = fill(text.replace("\r", ""), width=text_width, replace_whitespace=False, drop_whitespace=False).split("\n")
    lines = [l.ljust(text_width) for l in lines]

    l_width = max([font.getsize(l)[0] for l in lines])
    l_height = font.getsize(text)[1]
    img_width = padding_left + l_width + padding_right
    img_height = padding_top + (l_height * len(lines)) + padding_bottom

    image = Image.new("RGBA", (img_width, img_height), bg)
    draw = ImageDraw.Draw(image)

    for i, line in enumerate(lines):
        draw.text((padding_left, padding_top + i * l_height),
                  line,
                  fg,
                  font=font)

    if not output:
        return image

    image.save(output)


def tsp_print(text, cut=True, *args, **kwargs):
    image = text_to_image(text, *args, **kwargs)
    raster = imageToRaster(image, cut=cut)

    while True:
        try:
            con = create_connection(("10.0.0.51", 9100))
            break
        except socket_error:
            pass
    con.sendall(raster)
    con.recv(1000)
    con.close()
    # sleep(.1)
    del con

