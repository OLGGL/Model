__author__ = 'GSN'
# MODIFIED FROM FREECAD

"""FreeCAD webgl exporter

options: importWebGL.wireframeStyle = "faceloop" (can also be "multimaterial" or None)
importWebGL.template = a complete html file, where $CameraData is a placeholder for the
FreeCAD camera, and $ObjectsData a placeholder for the FreeCAD objects.
importWebGL.linewidth = an integer, specifyig the width of lines in "faceloop" mode"""

FREECAD_PATH = "C:\Program Files (x86)\FreeCAD 0.15\\bin"
import sys
sys.path.append(FREECAD_PATH)

DOC_PATH = "C:\Users\GS\Documents\CAD\trunk\CAD_Stool_v1\TestAssemble.FCStd"


import FreeCAD,Draft,Part,DraftGeomUtils

if FreeCAD.GuiUp:
    import FreeCADGui
    from DraftTools import translate
else:
    FreeCADGui = None
    def translate(ctxt,txt):
        return txt

tab = "                " # the tab size
wireframeStyle = "faceloop" # this can be "faceloop", "multimaterial" or None
cameraPosition = None # set this to a tuple to change, for ex. (0,0,0)
linewidth = 1
template = """var $ModuleName = {
    geom : function (scene) {
        //placeholder object
        $ObjectsData
        //placeholder object
    }
}
"""


if open.__module__ == '__builtin__':
    pythonopen = open

def export(exportList,filename, param_list):
    "exports the given objects to a .html file"

    html = getHTML(exportList, param_list)
    outfile = pythonopen(filename,"wb")
    outfile.write(html)
    outfile.close()
    #FreeCAD.Console.PrintMessage(translate("Arch","successfully written ")+filename+"\n")

def getHTML(objectsList, param_list):
    "returns the complete HTML code of a viewer for the given objects"
    m = template.replace("$ModuleName",param_list)
    # get objects data
    objectsData = ''
    for obj in objectsList:
        objectsData += getObjectData(obj)
    #t = template.replace("$CameraData",getCameraData())
    t = m.replace("$ObjectsData",objectsData)

    return t

def getCameraData():
    "returns the position and direction of the camera as three.js snippet"

    result = ""
    if cameraPosition:
        result += "camera.position.set("+str(cameraPosition[0])+","+str(cameraPosition[1])+","+str(cameraPosition[2])+");\n"
    elif FreeCADGui:
        # getting camera position
        pos = FreeCADGui.ActiveDocument.ActiveView.viewPosition().Base
        result += "camera.position.set( "
        result += str(pos.x) + ", "
        result += str(pos.y) + ", "
        result += str(pos.z) + " );\n"
    else:
        result += "camera.position.set(0,0,1000);\n"
    result += tab+"camera.lookAt( scene.position );\n"+tab
    # print result
    return result

def getObjectData(obj,wireframeMode=wireframeStyle):
    """returns the geometry data of an object as three.js snippet. wireframeMode
    can be multimaterial, faceloop or None"""

    result = ""
    wires = []
    if obj.isDerivedFrom("Part::Feature"):
        fcmesh = obj.Shape.tessellate(0.1)
        result = "var geom = new THREE.Geometry();\n"
        # adding vertices data
        for i in range(len(fcmesh[0])):
            v = fcmesh[0][i]
            result += tab+"var v"+str(i)+" = new THREE.Vector3("+str(v.x)+","+str(v.y)+","+str(v.z)+");\n"
        result += tab+"console.log(geom.vertices)\n"
        for i in range(len(fcmesh[0])):
            result += tab+"geom.vertices.push(v"+str(i)+");\n"
        # adding facets data
        for f in fcmesh[1]:
            result += tab+"geom.faces.push( new THREE.Face3"+str(f)+" );\n"
        for f in obj.Shape.Faces:
            for w in f.Wires:
                wo = Part.Wire(DraftGeomUtils.sortEdges(w.Edges))
                wires.append(wo.discretize(QuasiDeflection=0.1))

    elif obj.isDerivedFrom("Mesh::Feature"):
        mesh = obj.Mesh
        result = "var geom = new THREE.Geometry();\n"
        # adding vertices data
        for p in mesh.Points:
            v = p.Vector
            i = p.Index
            result += tab+"var v"+str(i)+" = new THREE.Vector3("+str(v.x)+","+str(v.y)+","+str(v.z)+");\n"
        result += tab+"console.log(geom.vertices)\n"
        for p in mesh.Points:
            result += tab+"geom.vertices.push(v"+str(p.Index)+");\n"
        # adding facets data
        for f in mesh.Facets:
            result += tab+"geom.faces.push( new THREE.Face3"+str(f.PointIndices)+" );\n"

    if result:
        # adding a base material
        if FreeCADGui:
            col = obj.ViewObject.ShapeColor
            rgb = Draft.getrgb(col,testbw=False)
        else:
            rgb = "#888888" # test color
        result += tab+"var basematerial = new THREE.MeshBasicMaterial( { color: 0x"+str(rgb)[1:]+" } );\n"
        #result += tab+"var basematerial = new THREE.MeshLambertMaterial( { color: 0x"+str(rgb)[1:]+" } );\n"

        if wireframeMode == "faceloop":
            # adding the mesh to the scene with a wireframe copy
            result += tab+"var mesh = new THREE.Mesh( geom, basematerial );\n"
            result += tab+"scene.add( mesh );\n"
            result += tab+"var linematerial = new THREE.LineBasicMaterial({linewidth: %d, color: 0x000000,});\n" % linewidth
            for w in wires:
                result += tab+"var wire = new THREE.Geometry();\n"
                for p in w:
                    result += tab+"wire.vertices.push(new THREE.Vector3("
                    result += str(p.x)+", "+str(p.y)+", "+str(p.z)+"));\n"
                result += tab+"var line = new THREE.Line(wire, linematerial);\n"
                result += tab+"scene.add(line);\n"

        elif wireframeMode == "multimaterial":
            # adding a wireframe material
            result += tab+"var wireframe = new THREE.MeshBasicMaterial( { color: "
            result += "0x000000, wireframe: true, transparent: true } );\n"
            result += tab+"var material = [ basematerial, wireframe ];\n"
            result += tab+"var mesh = new THREE.SceneUtils.createMultiMaterialObject( geom, material );\n"
            result += tab+"scene.add( mesh );\n"+tab

        else:
            # adding the mesh to the scene with simple material
            result += tab+"var mesh = new THREE.Mesh( geom, basematerial );\n"
            result += tab+"scene.add( mesh );\n"+tab

    return result

