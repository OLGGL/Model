import time
from copy import copy

FREECADPATH_WIN = "C:\Users\GS\Documents\Model\\trunk\FreeCAD_src\\bin"
#FREECADPATH_WIN = "FreeCAD_src\\bin"
#FREECADPATH_WIN = "C:\\Users\\Pierre\\Documents\\GitHub\\git_01\\Model\\FreeCAD_src\\bin"
#FREECADPATH_WIN = "C:\\Users\\GS\\Documents\\Model\\trunk\\FreeCAD_src\\bin"


#FREECADPATH_LINUX = "/usr/lib/freecad/lib"

import sys
import os
sys.path.append(FREECADPATH_WIN)
sys.path.append('./lib')

import FreeCAD
from importPart import importPart
import exportWebGL as wgl
import logging as log


# function to generate interval
def generate_interval(min, max, step):
    return list(range(min, max+step, step))


def update_source_file(obj, path):
    name = os.path.basename(obj.sourceFile)
    new_path = os.path.join(path, name)
    new_path = new_path.replace("\\", "/")
    obj.sourceFile = new_path
    return obj


class GroupParameter(object):
    def __init__(self, params):
        self.params = params

    def next_config(self):
        for p in self.params:
            if p.next_state():
                return True
        return False

    def init_state(self):
        for p in self:
            p.current_index = 0

    def get_name(self):
        name = ""
        for p in self:
            name += p.to_str()
        return name

    def __iter__(self):
        for p in self.params:
            yield p

    def __len__(self):
        return len(self.params)


class ParamOneElement(object):
    def __init__(self, param_name, values, piece, sketch_name):
        self.param_name = param_name
        self.values = values
        self.piece = piece
        self.sketch_name = sketch_name

    def apply(self, index):
        sketch = getattr(self.piece, self.sketch_name)
        sketch.setDatum(self.param_name, self.values[index])


class Parameter(object):
    def __init__(self, name, min, max, step):
        self.name = name
        self.min = min
        self.max = max
        self.step = step
        self.base_interval = generate_interval(min, max, step)
        self.current_index = 0
        self.list_param_one_element = []

    def __len__(self):
        return len(self.base_interval)

    def add_piece(self, piece, param_name, sketch_name, func=None):
        if func is None:
            func = lambda x: x
        if not isinstance(sketch_name, str):
            raise TypeError("Sketch name est une string, attention a ne pas avoir mis la fonction directement !")
        values = [func(a) for a in self.base_interval]
        d = ParamOneElement(param_name, values, piece, sketch_name)
        self.list_param_one_element.append(d)

    def apply(self):
        for d in self.list_param_one_element:
            d.apply(self.current_index)

    def to_str(self):
        return str(self.base_interval[self.current_index])

    def next_state(self):
        if self.current_index < len(self) - 1:
            self.current_index += 1
            return True
        else:
            self.current_index = 0
            return False


class Meuble(object):
    def __init__(self):
        self.path = None #TO adapt
        self.path_save = None #TO adapt
        self.base_name = None #TO adapt
        self.objects = None
        self.params = None
        self.group_params = None
        self.assembly = None

    def make_parameters(self):
        raise NotImplementedError() #TO adapt

    def get_objects(self):
        raise NotImplementedError() #TO adapt

    def adapt_parameters(self):
        raise NotImplementedError() #TO adapt

    def set_label_to_last(self):
        for obj in self.objects:
            change = False
            i = len(obj.Objects) - 1
            while not change and i >= 0:
                part = obj.Objects[i]
                if part.__class__.__name__ == "Feature":
                    part.Label = "Last"
                    change = True
                i -= 1
            if i < 0:
                raise TypeError("Problem with {}, cannot find last feature".format(obj.Name))

    def execute(self):
        self.make_parameters()
        nelem = 1
        for p in self.params:
            nelem *= len(p)
        log.warning("Creation of {} elements".format(nelem))
        self.get_objects()
        self.set_label_to_last()
        self.adapt_parameters()
        self.group_params = GroupParameter(self.params)
        if not os.path.isdir(self.path_save):
            os.mkdir(self.path_save)
        self.compute_all_pieces()

    def compute_all_pieces(self):
        self.group_params.init_state()
        ok = True
        while ok:
            self.compute_piece()
            assembly_name = self.group_params.get_name()
            self.export(assembly_name)
            ok = self.group_params.next_config()

    def compute_piece(self):
        for param in self.group_params:
            param.apply()
        for obj in self.objects:
            obj.recompute()
            obj.save()
        for obj in self.assembly.Objects:
            if obj.TypeId == 'Part::FeaturePython' and hasattr(obj, "sourceFile"):
                update_source_file(obj, self.path)
                importPart(obj.sourceFile, obj.Label) #function importPart from Assembly2 workbench
        self.assembly.recompute()
        self.assembly.save()

    def export(self, assembly_name):
        export_list = [obj for obj in self.assembly.Objects if obj.isDerivedFrom("Part::Feature")]
        wgl.export(export_list, self.path_save + "/" + self.base_name + assembly_name + '.js', self.base_name + assembly_name)


class Tabouret(Meuble):
    def __init__(self):
        super(Tabouret, self).__init__()
        self.path = os.getcwd()+"/Design/GSN_Stool/"
        self.base_name = "Stool"
        self.path_save = "./OutputStool"

    def make_parameters(self):
        LENGTH = Parameter("LENGTH", 250, 450, 50)
        L1 = Parameter("L1", 140, 260, 20)
        L2 = Parameter("L2", 115, 115, 1) #width of SidePart
        THICKNESS = Parameter("THICKNESS", 18, 18, 1) #thikness of material
        HEIGHT = Parameter("HEIGHT", 350, 550, 50) #height of stool
        self.params = [LENGTH, L1, L2, THICKNESS, HEIGHT]

    def get_objects(self):
        path_CP = self.path + "CenterPart.FCStd"
        path_SP = self.path + "SidePart.FCStd"
        path_LP = self.path + "LinkPart.FCStd"
        path_Leg = self.path + "LegPart.FCStd"
        path_Stool = self.path + "StoolAssembly.FCStd"
        doc_CP = FreeCAD.open(path_CP)
        doc_SP = FreeCAD.open(path_SP)
        doc_LP = FreeCAD.open(path_LP)
        doc_Leg = FreeCAD.open(path_Leg)
        doc_Stool = FreeCAD.open(path_Stool)
        self.objects = [doc_CP, doc_SP, doc_LP, doc_Leg]
        self.assembly = doc_Stool

    def adapt_parameters(self):
        length, L1, L2, thickness, height = self.params
        doc_CP, doc_SP, doc_LP, doc_Leg = self.objects
        length.add_piece(doc_CP, "Length", "Sketch")
        L1.add_piece(doc_CP, "Width", "Sketch")
        thickness.add_piece(doc_CP, "Thickness", "Sketch001", lambda x: -x,)

        length.add_piece(doc_SP, "Length", "Sketch")
        L2.add_piece(doc_SP, "Width", "Sketch", lambda x: -x)
        thickness.add_piece(doc_SP, "Thickness", "Sketch001")

        L1.add_piece(doc_LP, "Length", "Sketch", lambda x: x*0.5 -30. + 10.)

        height.add_piece(doc_Leg, "Height", "Sketch", lambda x: -x)
        length.add_piece(doc_Leg, "Length", "Sketch", lambda x: x - 110.)

        self.params = [length, L1, L2, thickness, height]


class Banc(Meuble):
    def __init__(self):
        super(Banc, self).__init__()
        self.path = os.getcwd()+"/Design/Banc/"
        self.base_name = "Banc"
        self.path_save = "./OutputBanc2"

    def make_parameters(self):
        # Dimensions in mm
        LENGTH = Parameter("LENGTH", 300, 3000, 300)
        WIDTH = Parameter("WIDTH", 300, 1000, 100)
        HEIGHT = Parameter("HEIGHT", 300, 1000, 100) #width of SidePart
        self.params = [LENGTH, WIDTH, HEIGHT]

    def get_objects(self):
        path_assise = self.path + "assise2_banc.FCStd"
        path_barre = self.path + "barre2_banc.FCStd"
        path_montant = self.path + "montant2_banc.FCStd"
        path_banc = self.path + "banc_untothislast_final.FCStd"
        doc_assise = FreeCAD.open(path_assise)
        doc_barre = FreeCAD.open(path_barre)
        doc_montant = FreeCAD.open(path_montant)
        doc_banc = FreeCAD.open(path_banc)
        self.objects = [doc_assise, doc_barre, doc_montant]
        self.assembly = doc_banc

    def adapt_parameters(self):
        length, width, height = self.params
        doc_assise, doc_barre, doc_montant = self.objects

        length.add_piece(doc_assise, "length", "Sketch")
        width.add_piece(doc_assise, "width", "Sketch")

        length.add_piece(doc_barre, "length", "Sketch")

        height.add_piece(doc_montant, "height", "Sketch")
        width.add_piece(doc_montant, "width", "Sketch", lambda x: -x)
        width.add_piece(doc_montant, "encochesH", "Sketch", lambda x: -x/7.)
        width.add_piece(doc_montant, "encochesB", "Sketch001", lambda x: -x/7.)

        return length, width, height


if __name__ == "__main__":
    t = time.clock()
    meuble = Banc()
    meuble.execute()
    t1 = time.clock()
    log.warning("Done in {}".format(t1 - t))