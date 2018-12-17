# parts of the script are from TLousky on https://blender.stackexchange.com/

import bpy
from math import radians
from os.path import join

D = bpy.data
C = bpy.context
S = C.scene
RENDER_DESTINATION = "C:/Users/peter/OneDrive/thesis_realistic_mvs_dataset/renders"

for object in bpy.data.objects:
    if object.name in ['Camera','Lamp','Sun', 'Man', 'maybeMan']:
        continue
    object.select = True
    bpy.ops.object.delete()

origin = (0,0,0)
empty = D.objects.new("Empty", None)
empty.location = origin
cam = S.objects['Camera']
cam.parent = empty

S.objects.link(empty)
S.objects.active = empty

n_angles = 10
rot_angle = 360 / n_angles

for i in range(n_angles):
    angle = i * rot_angle
    print(angle)
    empty.rotation_euler[2] = radians(angle) % radians(360)
    print(empty.rotation_euler[2] / radians(360) * 360)
    
    file_name = "angle_{a}".format(a = angle)
    file_name += S.render.file_extension
    S.render.filepath = join(RENDER_DESTINATION, file_name)

    bpy.ops.render.render(write_still = True)