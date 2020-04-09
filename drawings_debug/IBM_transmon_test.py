# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 09:07:00 2020

@author: wcs
"""

from scripts.hfss import get_active_project, release
from scripts.designer import Circuit, KeyElt

'''
testing script for consolidation of junction functions in designer

changes:
    -
'''

project = get_active_project()
design = project.get_active_design()
modeler = design.modeler
modeler.set_units('mm')
modeler.delete_all_objects()

c = Circuit(design, modeler)

KeyElt.is_litho = False
KeyElt.is_hfss = False

# Drawing

c.set_variable('xx', '100um')  # vertical spacing
c.set_variable('yy', '50um')  # horizontal spacing


def pos(i, j):
    return [(i + 0.5)*c.xx, (j + 0.5)*c.yy]

# Finger junctions


cutout_size = ['200um', '100um']
pad_spacing = '20um'
pad_size = ['50um', '50um']
Jwidth = '1um'
track = '1um'
gap = '1um'
Jinduc = '1nH'

c.key_elt('temp', pos(0, 0), [0, 1])
c.temp.draw_IBM_tansmon(cutout_size=cutout_size,
                        pad_spacing=pad_spacing,
                        pad_size=pad_size,
                        Jwidth=Jwidth,
                        track=track,
                        gap=gap,
                        Jinduc=Jinduc,
                        nport=2, fillet='2um')
release()
