import os

from PIL import Image


def resize_image(image, resize_factor, out_dir):
    if os.path.exists(out_dir):
        pass
    else:
        os.makedirs(out_dir)
    new_file = os.path.join(out_dir, os.path.basename(image))
    img = Image.open(image)
    new_width = int(img.width * resize_factor)
    new_height = int(img.height * resize_factor)
    img = img.resize((new_width, new_height))
    img.save(new_file)
    img.close()
    return new_file
