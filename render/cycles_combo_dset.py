import bpy
import random
import math
import time
import numpy as np
import json
import mathutils as mu
import os
from math import degrees
import colorsys


runs = 800
classes = ["Wing","Pole","Brick","Engine","Slope"]

def getClass(name):
    for c in classes:
        if c in name:
            return c



print("Begining.....\n\n\n")

millis = lambda: int(round(time.time() * 1000))
timestart = millis()
random.seed()


mode = "test"
num = 0
write_path = "/home/will/projects/legoproj/data/{}_normalsdset_{}/".format(mode,num)
while os.path.exists(write_path):
    num += 1
    write_path = "/home/will/projects/legoproj/data/{}_normalsdset_{}/".format(mode,num)
#os.mkdir(write_path)


bpy.context.scene.render.engine = 'CYCLES'




scene = bpy.context.scene
scene_objs = bpy.data.objects
camera = bpy.data.objects['Camera']



imgsdir = "/Users/will/projects/legotrain/surface_images/"
imgpaths = os.listdir(imgsdir)
imgs = []

for img in bpy.data.images:
    bpy.data.images.remove(img)
for path in imgpaths:
    img = bpy.data.images.load(filepath=imgsdir+path)
    imgs.append(img)

tablemat = bpy.data.materials["Table"]
nodes = tablemat.node_tree.nodes
imgnode = nodes.get("Image Texture")

def changeTable():
    imgnode.image = imgs[random.randint(0,80)]

#table = scene_objs["Table"]

gray = [.5,.5,.5,1.0]
lgray = [.8,.8,.8,1.0]
red = [1.0,1.0,1.0,1.0]
blue = [.1,.1,1.0,1.0]
black = [.2,.2,.2,1.0]
dirty = [.2,.3,.2,1.0]
dark=[0.0,0.0,0.0,1.0]

matnames = ["gray","lgray","red","blue","black","dirty","dark"]
matcolors = [gray, lgray, red, blue, black, dirty, dark]
mats = []

for i in range(0,len(matnames)):
    matname = matnames[i]
    if matname not in bpy.data.materials:
        mat = bpy.data.materials["Gray"].copy()
        mat.name = matname
    else:
        mat = bpy.data.materials[matname]

    color = matcolors[i]
    mat.use_nodes = True
    mat.node_tree.nodes["Diffuse BSDF"].inputs["Color"].default_value = color

    mats.append(mat)


normalmat = bpy.data.materials["Normz"]


objmasks = {}
objs = []

for obj in bpy.context.selected_objects:
    if obj.name !="Table":
        objs.append(obj)


scenedata = {}
scenedata["objects"] = {}
scenedata["dataroot"] = write_path

for obj in objs:
    objdata = {}
    objdata["modelmat"] = str(obj.matrix_world)
    scenedata["objects"][obj.name] = objdata

    
bpy.context.scene.update()


#incs = list(map(lambda x: round(x,1), list(np.arange(.2,1.2,.2))))
incs0 = [0.0, .6, .3, 1.0]
incs1 = [.3, .8, .5, 0.1]
incs2 = [1.0, .0, .5, 0.4]
endlist = len(objs)




for i,obj in enumerate(objs):

    obj.active_material_index = 0
    hue = (i/endlist)

    if obj.name not in bpy.data.materials:
        objmat = bpy.data.materials["WhiteShadeless"].copy()
    else:
        objmat = bpy.data.materials[obj.name]

    objmat.use_nodes = True
    objmat.name = obj.name

    if objmat.name not in obj.data.materials:
        obj.data.materials.append(objmat)

    color = colorsys.hsv_to_rgb(hue,.8,.8)
    color = [color[0],color[1],color[2],1.0]

    objmat.node_tree.nodes["Emission"].inputs["Color"].default_value = color

    objmasks[obj.name] = objmat
    scenedata["objects"][obj.name]["maskhue"] = hue
    scenedata["objects"][obj.name]["class"] = getClass(obj.name)


scenedata["renders"] = []



black_shadeless = bpy.data.materials["BlackShadeless"]
bck = bpy.data.objects['Background']
bck.data.materials[0] = black_shadeless
bck.active_material_index = 0



scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

bpy.context.scene.update()
projection_matrix = camera.calc_matrix_camera(
        bpy.context.scene.render.resolution_x,
        bpy.context.scene.render.resolution_y)
bpy.context.scene.update()
scenedata["projection"] = str(projection_matrix)


#Masking 
def shadeMasks(objects, path):               

    bck.hide_render = False
    bck.hide = False

    for obj in objects:
        obj.data.materials[0] = objmasks[obj.name]

    bpy.context.scene.update()
            
    scene.render.image_settings.file_format = 'PNG'        
    scene.render.filepath = path
    bpy.ops.render.render(write_still = 1)


#Normals
def shadeNormals(objects,path):

    for obj in objects:
        obj.data.materials[0] = normalmat

    bpy.context.scene.update()
            
    scene.render.filepath = path
    bpy.ops.render.render(write_still = 1)


#Main render
def shade(x,subset):

    changeTable()

    renderfile = "{}_a.png".format(x)
    maskfile = "mask_{}.png".format(x)
    normalsfile = "normals_{}.png".format(x)

    render_path = write_path + renderfile
    mask_path = write_path + maskfile
    normalspath = write_path + normalsfile

    scenedata["renders"].append({"x":x, "r":renderfile, "m":maskfile, "n":normalsfile, "c": str(camera.matrix_world.copy().inverted())})

    bck.hide_render = True
    bck.hide = True

    bpy.context.scene.update()

    scene.render.filepath = render_path
    bpy.ops.render.render(write_still = 1)

    shadeMasks(subset,mask_path)
    shadeNormals(subset,normalspath)



def assignMats(objslice,matslice):

    choices = len(matslice)

    for obj in objslice:
        obj.data.materials[0] = matslice[random.randint(0,choices)] 
        obj.hide_render = False




world = bpy.data.worlds["World.001"]
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
renderer = bpy.data.scenes["LegoTest"].cycles


for obj in objs:
    hide_render = True


for x in range(1):

    renderer.samples = random.randint(5,10)

    strength = random.randint(2,8)*.2
    bg.inputs[1].default_value = strength

    objslice = random.sample(objs, random.randint(1,floor(len(objs)/2))) 
    matslice = random.sample(mats, random.randint(1,len(mats)))

    assignMats(objslice,matslice)

    camera.location = (random.randint(6,10) * -1 if random.randint(0,1) < 1 else 1, random.randint(6,10) * -1 if random.randint(0,1) < 1 else 1, random.randint(5,8))

    bpy.context.scene.update()
    shade(x,objectz)

    for obj in objslice:
        obj.hide_render = True



with open(write_path + "data.json", 'w') as fp:
    json.dump(scenedata,fp)

print("Generated " + str(runs) + " images in " + str(float(millis() - timestart)/1000.0) + " seconds")

for obj in objs:
    obj.hide = False
    obj.hide_render = False