
FREECADPATH_WIN = "C:\Users\GS\Documents\CAD\\trunk\FreeCAD 0.15\\bin"
import sys
sys.path.append(FREECADPATH_WIN)

import FreeCAD
from importPart import importPart
import time

def generate_interval(min, max, step):
    x = []
    for i in range(min, max+step, step):
        x.append(i)
    return x

# Dimensions in mm
# LENGTH = [300, 320, 340, 360, 380, 400] #length of CenterPart & SideParts
LENGTH = generate_interval(250, 450, 50)
#L1 = [140, 160, 180, 200] #width of CenterPart
L1 = generate_interval(140, 260, 20)
L2 = [115] #width of SidePart
THICKNESS = 18. #thikness of material
HEIGHT = generate_interval(350, 550, 50) #height of stool
GAP = 10. #free gap between CenterPart & SidePart
print len(L2)*len(L1)*len(LENGTH)*len(HEIGHT)
raw_input()

doc_CP = FreeCAD.open("C:\Users\GS\Documents\CAD\\trunk\CAD_Stool_v1\CenterPart.FCStd")
doc_SP = FreeCAD.open("C:\Users\GS\Documents\CAD\\trunk\CAD_Stool_v1\SidePart.FCStd")
doc_LP = FreeCAD.open("C:\Users\GS\Documents\CAD\\trunk\CAD_Stool_v1\LinkPart.FCStd")
doc_Leg = FreeCAD.open("C:\Users\GS\Documents\CAD\\trunk\CAD_Stool_v1\LegPart.FCStd")
doc_Stool = FreeCAD.open("C:\Users\GS\Documents\CAD\\trunk\CAD_Stool_v1\TestAssemble.FCStd")

for length in LENGTH:
    for l1 in L1:
        for h in HEIGHT:
            for l2 in L2:
                # CenterPart #
                # Set length and width from first Sketch (pad)


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

                update_part = {}
                for obj in doc_Stool.Objects:
                    if obj.TypeId == 'Part::FeaturePython' and hasattr(obj,"sourceFile"):
                        importPart(obj.sourceFile, obj.Label)
                doc_Stool.recompute()
                doc_Stool.save()

                sys.path.append('./WebGL')
                export_list = []
                import exportWebGL as wgl
                for obj in doc_Stool.Objects:
                    if obj.isDerivedFrom("Part::Feature"):
                        export_list.append(obj)

                wgl.export(export_list, './output/Stool'+str(length)+str(l1)+str(h)+str(l2)+'.js','Stool'+str(length)+str(l1)+str(h)+str(l2))

print "done"
