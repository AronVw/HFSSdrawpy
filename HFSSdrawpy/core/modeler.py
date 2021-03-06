 # -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 14:14:51 2019

@author: antho
"""

from pint import UnitRegistry
import numpy as np
import os
from inspect import currentframe, getfile

from .entity import Entity
from ..utils import VariableString, parse_entry, val

ureg = UnitRegistry()
Q = ureg.Quantity

class Modeler():
    """
    Modeler which defines basic operations and methods to perform on Entity and on the chosen interface.
    To create a new interface, one needs to copy an existing one in a new file, and adapt all methods to the formalism of the new interface.

    The Modeler class is called at the beginning of a script but then it is the body that is always used.
    The syntax is the following:
        # TODO

    Inputs:
    -------
    mode: string in "gds" or "hfss"
    """
    is_overdev = False
    is_litho = False
    is_mask = False
    gap_mask = parse_entry('20um')
    overdev = parse_entry('0um')

    def __init__(self, mode):
        """
        Creates a Modeler object based on the chosen interface.
        For now the interface cannot be changed during an execution, only at the beginning
        """
        self.mode = mode
        if mode == "hfss":
            from ..interfaces.hfss_modeler import get_active_project
            project = get_active_project()
            design = project.get_active_design()
            self.design = design
            self.modeler = design.modeler
            self.modeler.set_units('mm')
            self.modeler.delete_all_objects()
            self.interface = self.modeler
        elif mode=="gds":
            from ..interfaces import gds_modeler
            self.interface = gds_modeler.GdsModeler()
        else:
            print('Mode should be either hfss or gds')
        
        #The list of bodies pointing to the current Modeler
        self.bodies = []

    ### Utils methods

    def delete_all_objects(self, entities):
        for entity in entities:
            entity.delete()

    def set_variable(self, value, name=None):
        """
        name (str): name of the variable in HFSS e.g. 'chip_length'
        value (str, VarStr, float): value of the variable
                                    if str will try to analyse the unit
        """
        if name is None:
            # this auto-parsing is clearly a hack and not robust
            # but I find it convenient
            f = currentframe().f_back#.f_back
            filename = getfile(f)
            code_line = open(filename).readlines()[f.f_lineno - 1]
            name = code_line.split("=")[0].strip()

        if self.mode == 'hfss':
            self.design.set_variable(name, value)  # for HFSS
        if not name in VariableString.variables.keys():
            return VariableString(name, value=value)
        else:
            VariableString.store_variable(name, value)
            print('%s is redefined to %s'%(name, value))
            return VariableString.instances[name]

    def update_variable(self, value, name):
        """
        name (str): name of the variable in HFSS e.g. 'chip_length'
        value (str, VarStr, float): value of the variable
                                    if str will try to analyse the unit
        """
        if self.mode == 'hfss':
            self.design.set_variable(name, value)  # for HFSS
        VariableString.store_variable(name, value)
        return VariableString.instances[name]

    def generate_gds(self, folder, filename):
        file = os.path.join(folder, filename)
        if self.mode=='gds':
            self.interface.generate_gds(file)

    def make_material(self, material_params, name):
        raise NotImplementedError()

    ### Methods acting on list of entities

    def intersect(self, entities, keep_originals = False):
        raise NotImplementedError()

    def unite(self, entities, main=None, keep_originals=False, new_name=None):
        # main: name or entity that should be returned/preserved/final union
        # if new_name (str) is provided, the original entities are kept and
        # the union is named new_name
        if not isinstance(entities, list):
            entities = [entities]
        entities = entities.copy()

        # if new_name is None:
        #     keep_originals = False
        # else:
        #     keep_originals = True

        if main is not None:
            if isinstance(main, str):
                main = Entity.dict_instances[main]
            if main in entities:
                entities.remove(main)
            entities = [main] + entities

        if len(entities)!=1:
            if not all([entity.dimension == entities[0].dimension
                                                    for entity in entities]):
                raise TypeError('All united elements should have the \
                                same dimension')
            else:
                if keep_originals:
                    entities[0] = entities[0].copy()

                union_entity = self.interface.unite(entities, keep_originals=keep_originals)
                union_entity.is_boolean = True
                list_fillet = [entity.is_fillet for entity in entities]
                union_entity.is_fillet = union_entity.is_fillet or any(list_fillet)

                if not keep_originals:
                    for ii in range(len(entities)):
                        entities[ii].delete()
        else:
            union_entity = entities[0]

        if keep_originals:
            union_entity.rename(new_name)

        return union_entity

    def rotate(self, entities, angle=0):
        if isinstance(angle, (list, np.ndarray)):
            if len(angle)==2:
                angle = np.math.atan2(np.linalg.det([[1,0],angle]),np.dot([1,0],angle))
                angle = angle/np.pi*180
            else:
                raise Exception("angle should be either a float or a 2-dim array")
        elif not isinstance(angle, (float, int, VariableString)):
            raise Exception("angle should be either a float or a 2-dim array")
        if self.mode == 'gds':
            angle = val(angle)
        self.interface.rotate(entities, angle)  # angle in degrees

    def translate(self, entities, vector=[0, 0, 0]):
        vector = parse_entry(vector)
        if self.mode == 'gds':
            vector = val(vector)
        self.interface.translate(entities, vector)
