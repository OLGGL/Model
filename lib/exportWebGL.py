__author__ = 'GSN'
# MODIFIED FROM FREECAD

import FreeCAD,Draft,Part,DraftGeomUtils

tab = "        " # the tab size
wireframeStyle = "faceloop" # this can be "faceloop", "multimaterial" or None

# template = """var $ModuleName = {
#     geom : function () {
#         geometry = [];
#         //placeholder object
#         $ObjectsData
#         //placeholder object
#     return [geometry];
#     }
# }
# """

template = """var $ModuleName = {
    geom : function () {
        geometry = [];
        //placeholder object
        $ObjectsDataFaces
        //placeholder object
    return [geometry];
    },
    wireframe : function() {
        wires = [];
        //placeholder object
        $ObjectsDataWires
        //placeholder object
    return [wires]
    }
}
"""


if open.__module__ == '__builtin__':
    pythonopen = open

def export(exportList,filename, param_list):
    "exports the given objects to a .js file"

    html = getHTML(exportList, param_list)
    outfile = pythonopen(filename,"wb")
    outfile.write(html)
    outfile.close()


def getHTML(objectsList, param_list):
    "returns the complete HTML code of a viewer for the given objects"
    m = template.replace("$ModuleName",param_list)
    # get objects data
    objectsDataFaces = ''
    objectsDataWires = ''
    for i, obj in enumerate(objectsList):
        objectsDataFaces += getObjectData(obj,i, FACES=True, WIRES=False)
        objectsDataWires += getObjectData(obj,i, FACES=False, WIRES=True)
    #t = template.replace("$CameraData",getCameraData())
    t = m.replace("$ObjectsDataFaces", objectsDataFaces)
    w = t.replace("$ObjectsDataWires", objectsDataWires)
    return w

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


def getObjectData(obj,index,FACES, WIRES, wireframeMode=wireframeStyle):
    result = ""
    wires = []
    if FACES:
        ### Start UVs coordinates calculation
        x_max = obj.Shape.BoundBox.XMax
        x_min = obj.Shape.BoundBox.XMin
        y_max = obj.Shape.BoundBox.YMax
        y_min = obj.Shape.BoundBox.YMin
        z_max = obj.Shape.BoundBox.ZMax
        z_min = obj.Shape.BoundBox.ZMin

        if obj.isDerivedFrom("Part::Feature"):
            fcmesh = obj.Shape.tessellate(0.1)
            result = "var geom"+str(index)+" = new THREE.Geometry();\n"
            result += tab+"geom"+str(index)+".faceVertexUvs[0] = [];\n"
            # adding vertices data
            for i in range(len(fcmesh[0])):
                v = fcmesh[0][i]
                result += tab+"var v"+str(i)+" = new THREE.Vector3("+str(v.x)+","+str(v.y)+","+str(v.z)+");\n"
            for i in range(len(fcmesh[0])):
                result += tab+"geom"+str(index)+".vertices.push(v"+str(i)+");\n"
            # adding facets data
            for f in fcmesh[1]:
                result += tab+"geom"+str(index)+".faces.push( new THREE.Face3"+str(f)+" );\n"
                ## Setting UVs coordinates ###
                result += tab+"geom"+str(index)+".faceVertexUvs[0].push([ \n"
                tmp = 0
                for vertices in f:
                    uv = ((fcmesh[0][vertices].x -x_min) / (x_max - x_min), (fcmesh[0][vertices].y -y_min) / (y_max - y_min))
                    tmp += 1
                    if tmp == 3:
                        result += tab+"    new THREE.Vector2"+str(uv)+"\n"
                    else:
                        result += tab+"    new THREE.Vector2"+str(uv)+",\n"
                result += tab+"]);\n"
                ## end of UVs coordinates ##
            result += tab+"geometry.push(geom"+str(index)+");\n"

    if WIRES:
        for f in obj.Shape.Faces:
            for w in f.Wires:
                wo = Part.Wire(DraftGeomUtils.sortEdges(w.Edges))
                wires.append(wo.discretize(QuasiDeflection=0.1))

    # Mesh feature
    # elif obj.isDerivedFrom("Mesh::Feature"):
    #     mesh = obj.Mesh
    #     result = "var geom = new THREE.Geometry();\n"
    #     # adding vertices data
    #     for p in mesh.Points:
    #         v = p.Vector
    #         i = p.Index
    #         result += tab+"var v"+str(i)+" = new THREE.Vector3("+str(v.x)+","+str(v.y)+","+str(v.z)+");\n"
    #     result += tab+"console.log(geom.vertices)\n"
    #     for p in mesh.Points:
    #         result += tab+"geom.vertices.push(v"+str(p.Index)+");\n"
    #     # adding facets data
    #     for f in mesh.Facets:
    #         result += tab+"geom.faces.push( new THREE.Face3"+str(f.PointIndices)+" );\n"

    if WIRES:
        if wireframeMode == "faceloop":
            # adding the mesh to the scene with a wireframe copy
            #result += tab+"var linematerial = new THREE.LineBasicMaterial({linewidth: %d, color: 0x000000,});\n" % linewidth
            for i, w in enumerate(wires):
                result += tab+"var wire"+str(index)+str(i)+" = new THREE.Geometry();\n"
                for p in w:
                    result += tab+"wire"+str(index)+str(i)+".vertices.push(new THREE.Vector3("
                    result += str(p.x)+", "+str(p.y)+", "+str(p.z)+"));\n"
                # result += tab+"var line = new THREE.Line(wire, linematerial);\n"
                # result += tab+"scene.add(line);\n"
                result += tab+"wires.push(wire"+str(index)+str(i)+");\n"

    return result

