__author__ = 'GSN'
# MODIFIED FROM FREECAD

import FreeCAD,Draft,Part,DraftGeomUtils
import numpy as np

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
    nbre_face = 0
    for obj in objectsList:
        objectsDataFaces += getObjectData(obj, nbre_face, FACES=True, WIRES=False)
        objectsDataWires += getObjectData(obj, nbre_face, FACES=False, WIRES=True)
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


def get_plan(boundbox):
    x_max = boundbox.XMax
    x_min = boundbox.XMin
    y_max = boundbox.YMax
    y_min = boundbox.YMin
    z_max = boundbox.ZMax
    z_min = boundbox.ZMin
    mini = {"x": x_min, "y": y_min, "z": z_min}
    delta = {"x": x_max - x_min, "y": y_max - y_min, "z": z_max - z_min}
    sorted_delta = sorted(delta, key = lambda x: delta[x], reverse=True)
    Uname = sorted_delta[0]
    Vname = sorted_delta[1]
    Udelta = delta[Uname]
    Vdelta = delta[Vname]
    Umin = mini[Uname]
    Vmin = mini[Vname]
    return Uname, Udelta, Umin, Vname, Vdelta, Vmin


def getObjectData(obj, nbre_face, FACES, WIRES, wireframeMode=wireframeStyle):
    result = ""
    wires = []
    old_nbre_face = nbre_face
    if FACES:
        if obj.isDerivedFrom("Part::Feature"):
            for face in obj.Shape.Faces:
                ### Start UVs coordinates calculation
                x_max = face.BoundBox.XMax
                x_min = face.BoundBox.XMin
                y_max = face.BoundBox.YMax
                y_min = face.BoundBox.YMin
                z_max = face.BoundBox.ZMax
                z_min = face.BoundBox.ZMin

                l = np.sort([x_max - x_min, y_max - y_min, z_max - z_min])
                U_Delta = l[-2]
                V_Delta = l[-1]
                U_min = 0
                V_min = 0
                Umini = None
                if U_Delta == x_max - x_min:
                    U_min = x_min
                    Umini = "x"
                elif U_Delta == y_max - y_min:
                    U_min = y_min
                    Umini = "y"
                elif U_Delta == z_max - z_min:
                    U_min = z_min
                    Umini = "z"

                Vmini = None
                if V_Delta == x_max - x_min:
                    V_min = x_min
                    Vmini = "x"
                elif V_Delta == y_max - y_min:
                    V_min = y_min
                    Vmini = "y"
                elif V_Delta == z_max - z_min:
                    V_min = z_min
                    Vmini = "z"

                Umini, U_Delta, U_min, Vmini, V_Delta, V_min = get_plan(face.BoundBox)

                fcmesh = face.tessellate(0.1)
                result += "var geom"+str(nbre_face)+" = new THREE.Geometry();\n"
                result += tab+"geom"+str(nbre_face)+".faceVertexUvs[0] = [];\n"
                # adding vertices data
                for i in range(len(fcmesh[0])):
                    v = fcmesh[0][i]
                    result += tab+"var v"+str(i)+" = new THREE.Vector3("+str(v.x)+","+str(v.y)+","+str(v.z)+");\n"
                for i in range(len(fcmesh[0])):
                    result += tab+"geom"+str(nbre_face)+".vertices.push(v"+str(i)+");\n"
                # adding facets data
                for f in fcmesh[1]:
                    result += tab+"geom"+str(nbre_face)+".faces.push( new THREE.Face3"+str(f)+" );\n"
                    ## Setting UVs coordinates ###
                    result += tab+"geom"+str(nbre_face)+".faceVertexUvs[0].push([ \n"
                    tmp = 0
                    uv = None
                    for vertices in f:
                        if Vmini == "x" and Umini == "y":
                            uv = ((fcmesh[0][vertices].x -V_min) / V_Delta, (fcmesh[0][vertices].y -U_min) / U_Delta)
                        elif Vmini == "x" and Umini == "z":
                            uv = ((fcmesh[0][vertices].x -V_min) / V_Delta, (fcmesh[0][vertices].z -U_min) / U_Delta)
                        elif Vmini == "y" and Umini == "x":
                            uv = ((fcmesh[0][vertices].y -V_min) / V_Delta, (fcmesh[0][vertices].x -U_min) / U_Delta)
                        elif Vmini == "y" and Umini == "z":
                            uv = ((fcmesh[0][vertices].y -V_min) / V_Delta, (fcmesh[0][vertices].z -U_min) / U_Delta)
                        elif Vmini == "z" and Umini == "x":
                            uv = ((fcmesh[0][vertices].z -V_min) / V_Delta, (fcmesh[0][vertices].x -U_min) / U_Delta)
                        elif Vmini == "z" and Umini == "y":
                            uv = ((fcmesh[0][vertices].z -V_min) / V_Delta, (fcmesh[0][vertices].y -U_min) / U_Delta)
                        tmp += 1
                        if uv is None:
                            raise KeyError("UV has not been created")
                        if tmp == 3:
                            result += tab+"    new THREE.Vector2"+str(uv)+"\n"
                        else:
                            result += tab+"    new THREE.Vector2"+str(uv)+",\n"
                    result += tab+"]);\n"
                    ## end of UVs coordinates ##
                result += tab+"geometry.push(geom"+str(nbre_face)+");\n"
                nbre_face += 1
        nbre_face = old_nbre_face

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

        if wireframeMode == "faceloop":
            # adding the mesh to the scene with a wireframe copy
            #result += tab+"var linematerial = new THREE.LineBasicMaterial({linewidth: %d, color: 0x000000,});\n" % linewidth
            for i, w in enumerate(wires):
                result += tab+"var wire"+str(nbre_face)+str(i)+" = new THREE.Geometry();\n"
                for p in w:
                    result += tab+"wire"+str(nbre_face)+str(i)+".vertices.push(new THREE.Vector3("
                    result += str(p.x)+", "+str(p.y)+", "+str(p.z)+"));\n"
                # result += tab+"var line = new THREE.Line(wire, linematerial);\n"
                # result += tab+"scene.add(line);\n"
                result += tab+"wires.push(wire"+str(nbre_face)+str(i)+");\n"
            nbre_face += 1

    return result

