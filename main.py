
#FREECADPATH_WIN = "C:\Users\GS\Documents\Model\\trunk\FreeCAD_src\\bin"
FREECADPATH_LINUX = "/usr/lib/freecad/lib"
import sys
import os
sys.path.append(FREECADPATH_LINUX)
sys.path.append('./lib')

import FreeCAD
from importPart import importPart
import exportWebGL as wgl

# function to generate interval
def generate_interval(min, max, step):
    x = []
    for i in range(min, max+step, step):
        x.append(i)
    return x

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
print len(L2)*len(L1)*len(LENGTH)*len(HEIGHT)
raw_input("Press Enter to continue")

#Local path to Freecad files
path_CP = os.getcwd()+'/Design/GSN_Stool/CenterPart.FCStd'
path_SP = os.getcwd()+'/Design/GSN_Stool/SidePart.FCStd'
path_LP = os.getcwd()+'/Design/GSN_Stool/LinkPart.FCStd'
path_Leg = os.getcwd()+'/Design/GSN_Stool/LegPart.FCStd'
path_Stool = os.getcwd()+'/Design/GSN_Stool/StoolAssembly.FCStd'
dict_path = {
    'CenterPart': path_CP,
    'SidePart': path_SP,
    'LinkPart': path_LP,
    'LegPart': path_Leg
}
doc_CP = FreeCAD.open(path_CP)
doc_SP = FreeCAD.open(path_SP)
doc_LP = FreeCAD.open(path_LP)
doc_Leg = FreeCAD.open(path_Leg)
doc_Stool = FreeCAD.open(path_Stool)

#Checking paths in assembly doc
def check_path(doc, dict_path):
    for obj in doc.Objects:
        if obj.TypeId == 'Part::FeaturePython' and hasattr(obj,"sourceFile"):
            obj.sourceFile = dict_path[obj.sourceFile.split('/')[-1].split('.')[0]]

check_path(doc_Stool, dict_path)


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
                        importPart(obj.sourceFile, obj.Label) #function importPart from Assembly2 workbench
                doc_Stool.recompute()
                doc_Stool.save()

                export_list = []
                for obj in doc_Stool.Objects:
                    if obj.isDerivedFrom("Part::Feature"):
                        export_list.append(obj)

                wgl.export(export_list, './output/Stool'+str(length)+str(l1)+str(h)+str(l2)+'.js','Stool'+str(length)+str(l1)+str(h)+str(l2))

print "done"
