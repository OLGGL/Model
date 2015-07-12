import time
from copy import copy

FREECADPATH_WIN = "C:\Users\GS\Documents\Model\\trunk\FreeCAD_src\\bin"
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


#Checking paths in assembly doc
def check_path(doc, dict_path):
    for obj in doc.Objects:
        if obj.TypeId == 'Part::FeaturePython' and hasattr(obj,"sourceFile"):
            obj.sourceFile = dict_path[obj.sourceFile.split('/')[-1].split('.')[0]]

# check_path(doc_Stool, dict_path)


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
    def __init__(self, param_name, values, piece):
        self.param_name = param_name
        self.values = values
        self.piece = piece

    def apply(self, index):
        #print(self.piece.Name, self.param_name)
        if self.param_name == "Thickness":
            self.piece.Sketch001.setDatum(self.param_name, self.values[index])
        else:
            self.piece.Sketch.setDatum(self.param_name, self.values[index])


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

    def add_piece(self, piece, param_name, func=None):
        if func is None:
            func = lambda x: x
        values = [func(a) for a in self.base_interval]
        d = ParamOneElement(param_name, values, piece)
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


def make_parameters():
     # Dimensions in mm
    LENGTH = generate_interval(250, 450, 50)
    # LENGTH = [400]
    L1 = generate_interval(140, 260, 20) #width of CenterPart
    # L1 = [160]
    L2 = [115] #width of SidePart
    THICKNESS = 18. #thikness of material
    HEIGHT = generate_interval(350, 550, 50) #height of stool
    # HEIGHT = [350]
    GAP = 10. #gap between CenterPart & SidePart
    log.warning(len(L2)*len(L1)*len(LENGTH)*len(HEIGHT))
    #raw_input("Press Enter to continue")
    return LENGTH, L1, L2, THICKNESS, HEIGHT, GAP


def make_parameters_new():
    # Dimensions in mm
    LENGTH = Parameter("LENGTH", 250, 450, 50)
    L1 = Parameter("L1", 140, 260, 20)
    L2 = Parameter("L2", 115, 115, 1) #width of SidePart
    THICKNESS = Parameter("THICKNESS", 18, 18, 1) #thikness of material
    HEIGHT = Parameter("HEIGHT", 350, 550, 50) #height of stool
    res = [LENGTH, L1, L2, THICKNESS, HEIGHT]
    log.warning("Creation of {} elements".format(len(L2)*len(L1)*len(LENGTH)*len(HEIGHT)))
    return res


def get_object():
    #Local path to Freecad files
    path_CP = os.getcwd()+'/Design/GSN_Stool/CenterPart.FCStd'
    path_SP = os.getcwd()+'/Design/GSN_Stool/SidePart.FCStd'
    path_LP = os.getcwd()+'/Design/GSN_Stool/LinkPart.FCStd'
    path_Leg = os.getcwd()+'/Design/GSN_Stool/LegPart.FCStd'
    path_Stool = os.getcwd()+'/Design/GSN_Stool/StoolAssembly.FCStd'
    doc_CP = FreeCAD.open(path_CP)
    doc_SP = FreeCAD.open(path_SP)
    doc_LP = FreeCAD.open(path_LP)
    doc_Leg = FreeCAD.open(path_Leg)
    doc_Stool = FreeCAD.open(path_Stool)
    return doc_CP, doc_SP, doc_LP, doc_Leg, doc_Stool


def adapt_parameters(length, L1, L2, thickness, height, doc_CP, doc_SP, doc_LP, doc_Leg):
    length.add_piece(doc_CP, "Length")
    L1.add_piece(doc_CP, "Width")
    thickness.add_piece(doc_CP, "Thickness", lambda x: -x)

    length.add_piece(doc_SP, "Length")
    L2.add_piece(doc_SP, "Width", lambda x: -x)
    thickness.add_piece(doc_SP, "Thickness")

    L1.add_piece(doc_LP, "Length", lambda x: x*0.5 -30. + 10.)

    height.add_piece(doc_Leg, "Height", lambda x: -x)
    length.add_piece(doc_Leg, "Length", lambda x: x - 110.)

    return length, L1, L2, thickness, height


def compute_all_pieces(group_param, objects, assembly, path):
    group_param.init_state()
    ok = True
    while ok:
        assembly = compute_piece(group_param, objects, assembly)
        assembly_name = group_param.get_name()
        export(assembly, path, assembly_name)
        ok = group_param.next_config()


def compute_piece(group_param, objects, assembly):
    for param in group_param:
        param.apply()
    for obj in objects:
        obj.recompute()
        obj.save()
    for obj in assembly.Objects:
        if obj.TypeId == 'Part::FeaturePython' and hasattr(obj,"sourceFile"):
            importPart(obj.sourceFile, obj.Label) #function importPart from Assembly2 workbench
    assembly.recompute()
    assembly.save()
    return assembly


def export(assembly, path, assembly_name):
    print("EXPORT_FILE_", assembly_name)
    export_list = [obj for obj in assembly.Objects if obj.isDerivedFrom("Part::Feature")]
    wgl.export(export_list, path + assembly_name+'.js','Stool'+assembly_name)


def update_obj_source_file(obj):
    filename = adapt_path(obj.sourceFile)
    obj.sourceFile = filename


def find_parent_directory(path, pattern):
    path_copy = copy(path)
    base_path = "C:\\"
    while not path.endswith(pattern) and path != base_path:
        path = os.path.dirname(path)
    if path == base_path:
        raise OSError("Problem with path to find {} in {}.".format(pattern, path_copy))
    return path


def adapt_path(filename):
    local_path_to_model = os.path.join(find_parent_directory(os.getcwd(), "Model"), "Design")
    path = filename.split("Design")[1]
    local_path = local_path_to_model + path
    local_path = local_path.replace("\\", "/")
    return local_path


def old_main():
    LENGTH, L1, L2, THICKNESS, HEIGHT, GAP = make_parameters()
    doc_CP, doc_SP, doc_LP, doc_Leg, doc_Stool = get_object()

    for length in LENGTH:
        for l1 in L1:
            for h in HEIGHT:
                for l2 in L2:

                    ####### Update parts independently #######
                    # CenterPart #
                    # Set length and width from first Sketch
                    doc_CP.Sketch.setDatum("Length", length)
                    doc_CP.Sketch.setDatum("Width", l1)
                    # Set thickness from second Sketch001 (pocket)
                    doc_CP.Sketch001.setDatum("Thickness", -THICKNESS)
                    doc_CP.recompute()
                    doc_CP.save()

                    # SidePart #
                    # Set length and width from first Sketch (pad)
                    doc_SP.Sketch.setDatum("Length", length)
                    doc_SP.Sketch.setDatum("Width", -l2)
                    # Set thickness from second Sketch001 (pocket)
                    doc_SP.Sketch001.setDatum("Thickness", THICKNESS)
                    doc_SP.recompute()
                    doc_SP.save()

                    # LinkPart #
                    doc_LP.Sketch.setDatum("Length", GAP + l1/2. -30.)
                    doc_LP.recompute()
                    doc_LP.save()

                    # LegPart #
                    doc_Leg.Sketch.setDatum("Height", -h)
                    doc_Leg.Sketch.setDatum("Length", length-110.)
                    #doc.Sketch001.setDatum("Thickness", THICKNESS)
                    doc_Leg.recompute()
                    doc_Leg.save()

                    ######## Update parts in Assembly file and re-run constraint solver #########
                    for obj in doc_Stool.Objects:
                        if obj.TypeId == 'Part::FeaturePython' and hasattr(obj,"sourceFile"):
                            update_obj_source_file(obj)
                            importPart(obj.sourceFile, obj.Label) #function importPart from Assembly2 workbench
                    doc_Stool.recompute()
                    doc_Stool.save()

                    export_list = []
                    for obj in doc_Stool.Objects:
                        if obj.isDerivedFrom("Part::Feature"):
                            export_list.append(obj)
                    wgl.export(export_list, './output/Stool'+str(length)+str(l1)+str(h)+str(l2)+'.js','Stool'+str(length)+str(l1)+str(h)+str(l2))


def new_main():
    params = make_parameters_new()
    length, L1, L2, thickness, height = params
    doc_CP, doc_SP, doc_LP, doc_Leg, doc_Stool = get_object()
    length, L1, L2, thickness, height = adapt_parameters(length, L1, L2, thickness, height, doc_CP, doc_SP, doc_LP, doc_Leg)

    params = [length, L1, L2, thickness, height]
    group_params = GroupParameter(params)
    objects = [doc_CP, doc_SP, doc_LP, doc_Leg]
    assembly = doc_Stool

    path = "./output/Stool"
    compute_all_pieces(group_params, objects, assembly, path)

if __name__ == "__main__":
    t = time.clock()
    old_main()
    t1 = time.clock()
    log.warning("Done in {}".format(t1 - t))