""" Captcha.Visual.Pictures

Random collections of images
"""
#
# PyCAPTCHA Package
# Copyright (C) 2004 Micah Dowty <micah@navi.cx>
#

from .. import File

class ImageFactory(File.RandomFileFactory):
    """A factory that generates random images from a list"""
    extensions = [".png", ".jpeg"]
    basePath = "pictures"


abstract = ImageFactory("abstract")
nature = ImageFactory("nature")

### The End ###
