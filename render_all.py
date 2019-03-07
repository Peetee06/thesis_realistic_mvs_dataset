import bpy
from math import radians
from os.path import join
import shutil

# from user rfabbri
# https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera

import bpy_extras
from mathutils import Matrix, Vector

#---------------------------------------------------------------
# 3x4 P matrix from Blender camera
#---------------------------------------------------------------

# Build intrinsic camera parameters from Blender camera data
#
# See notes on this in 
# blender.stackexchange.com/questions/15102/what-is-blenders-camera-projection-matrix-model
def get_calibration_matrix_K_from_blender(camd):
    f_in_mm = camd.lens
    scene = bpy.context.scene
    resolution_x_in_px = scene.render.resolution_x
    resolution_y_in_px = scene.render.resolution_y
    scale = scene.render.resolution_percentage / 100
    sensor_width_in_mm = camd.sensor_width
    sensor_height_in_mm = camd.sensor_height
    pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
    if (camd.sensor_fit == 'VERTICAL'):
        # the sensor height is fixed (sensor fit is horizontal), 
        # the sensor width is effectively changed with the pixel aspect ratio
        s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio 
        s_v = resolution_y_in_px * scale / sensor_height_in_mm
    else: # 'HORIZONTAL' and 'AUTO'
        # the sensor width is fixed (sensor fit is horizontal), 
        # the sensor height is effectively changed with the pixel aspect ratio
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
        s_u = resolution_x_in_px * scale / sensor_width_in_mm
        s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm


    # Parameters of intrinsic calibration matrix K
    alpha_u = f_in_mm * s_u
    alpha_v = f_in_mm * s_v
    u_0 = resolution_x_in_px * scale / 2
    v_0 = resolution_y_in_px * scale / 2
    skew = 0 # only use rectangular pixels

    K = Matrix(
        ((alpha_u, skew,    u_0),
        (    0  , alpha_v, v_0),
        (    0  , 0,        1 )))
    return K

# Returns camera rotation and translation matrices from Blender.
# 
# There are 3 coordinate systems involved:
#    1. The World coordinates: "world"
#       - right-handed
#    2. The Blender camera coordinates: "bcam"
#       - x is horizontal
#       - y is up
#       - right-handed: negative z look-at direction
#    3. The desired computer vision camera coordinates: "cv"
#       - x is horizontal
#       - y is down (to align to the actual pixel coordinates 
#         used in digital images)
#       - right-handed: positive z look-at direction
def get_3x4_RT_matrix_from_blender(cam):
    # bcam stands for blender camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))

    # Transpose since the rotation is object rotation, 
    # and we want coordinate rotation
    # R_world2bcam = cam.rotation_euler.to_matrix().transposed()
    # T_world2bcam = -1*R_world2bcam * location
    #
    # Use matrix_world instead to account for all constraints
    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()

    # Convert camera location to translation vector used in coordinate changes
    # T_world2bcam = -1*R_world2bcam*cam.location
    # Use location from matrix_world to account for constraints:     
    T_world2bcam = -1*R_world2bcam * location

    # Build the coordinate transform matrix from world to computer vision camera
    R_world2cv = R_bcam2cv*R_world2bcam
    T_world2cv = R_bcam2cv*T_world2bcam

    # put into 3x4 matrix
    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
         ))
    return RT

def get_3x4_P_matrix_from_blender(cam):
    K = get_calibration_matrix_K_from_blender(cam.data)
    RT = get_3x4_RT_matrix_from_blender(cam)
    return K*RT, K, RT
    
    
    
# parts of the script are from TLousky on https://blender.stackexchange.com/
# 
#   TODO add Source of shapenet script
#
# and from render_shapenet.py 

def main():
    D = bpy.data
    C = bpy.context
    S = C.scene
    RENDER_DESTINATION = "C:/Users/peter/OneDrive/thesis_realistic_mvs_dataset/renders"
    DEPTH_MAP_FOLDER = "depth_maps"
    CAMERA_PARAMS_FOLDER = "cam_params"
    
    # Set up rendering of depth map:
    S.use_nodes = True
    tree = S.node_tree
    links = tree.links
    # Add passes for additionally dumping albed and normals.
    S.render.layers["RenderLayer"].use_pass_normal = True
    S.render.layers["RenderLayer"].use_pass_color = True
    
    # clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)
    
    # create input render layer node
    rl = tree.nodes.new('CompositorNodeRLayers')
    bgnode = tree.nodes.new('CompositorNodeImage')
    rl_mix = tree.nodes.new('CompositorNodeMixRGB')
    links.new(rl.outputs['Alpha'],rl_mix.inputs['Fac'])
    links.new(bgnode.outputs['Image'],rl_mix.inputs[1])
    links.new(rl.outputs['Image'],rl_mix.inputs[2])

    #map = tree.nodes.new(type="CompositorNodeMapValue")
    # Size is chosen kind of arbitrarily, try out until you're satisfied with resulting depth map.
    #map.offset = [-16.1]
    #map.size = [0.3]
    #map.use_min = True
    #map.min = [0]
    #map.use_max = True
    #map.max = [255]

    #normalize = tree.nodes.new(type="CompositorNodeNormalize")
    #links.new(rl.outputs['Depth'], normalize.inputs[0])
    
    # trying map range instead of map value
    map = tree.nodes.new(type="CompositorNodeMapRange")
    map.inputs[1].default_value = 0.0
    map.inputs[2].default_value = 23.1
    map.inputs[3].default_value = 0.0
    map.inputs[4].default_value = 1.0
    links.new(rl.outputs['Depth'], map.inputs[0])
    
    invert = tree.nodes.new(type="CompositorNodeInvert")
    links.new(map.outputs[0], invert.inputs[1])
    
    # viewer can be used to manually adjust map.offset and map.size in UV/Image Editor in blender
    depthViewer = tree.nodes.new(type="CompositorNodeViewer")
    links.new(invert.outputs[0], depthViewer.inputs[0])
    
    # mixed color output
    colorFileOutput = tree.nodes.new(type="CompositorNodeOutputFile")
    colorFileOutput.label = 'Color Output PNG'
    links.new(rl_mix.outputs['Image'], colorFileOutput.inputs['Image'])
    
    
    # create a file output node and set the path
    depthFileOutputEXR = tree.nodes.new(type="CompositorNodeOutputFile")
    depthFileOutputEXR.label = 'Depth Output EXR'
    depthFileOutputEXR.format.file_format = 'OPEN_EXR_MULTILAYER'
    depthFileOutputEXR.format.color_depth = '32'
    depthFileOutputEXR.format.compression = 0
    links.new(rl.outputs['Depth'], depthFileOutputEXR.inputs[0])
    
    depthFileOutput = tree.nodes.new(type="CompositorNodeOutputFile")
    depthFileOutput.label = 'Depth Output PNG'
    #links.new(normalize.outputs[0], depthFileOutput.inputs[0])
    links.new(invert.outputs[0], depthFileOutput.inputs[0])

    # Make light just directional, disable shadows.
    lamp = D.lamps['Lamp']
    lamp.type = 'SUN'
    lamp.shadow_method = 'NOSHADOW'
    # Possibly disable specular shading:
    lamp.use_specular = False
    lamp.energy = 1.25

    # Add another light source so stuff facing away from light is not completely dark
    if D.objects.find('Sun') < 1:
        bpy.ops.object.lamp_add(type='SUN')
    lamp2 = D.lamps['Sun']
    lamp2.shadow_method = 'NOSHADOW'
    lamp2.use_specular = False
    lamp2.energy = 0.25
    D.objects['Sun'].rotation_euler = D.objects['Lamp'].rotation_euler
    D.objects['Lamp'].rotation_euler[0] += 180
    
    for object in D.objects:
        if object.name in ['Camera','Lamp','Sun', 'Man', 'maybeMan']:
            continue
        object.select = True
        bpy.ops.object.delete()
    
    #cam = S.objects['Camera']
    #cam.data.lens=30
    #cam.data.sensor_width=32
    #cam.data.sensor_height=32
    #cam_constraint = cam.constraints.new(type='TRACK_TO')
    #cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    #cam_constraint.up_axis = 'UP_Y'
    
    origin = (0,0,0)
    empty = D.objects.new("Empty", None)
    empty.location = origin
    cam = S.objects['Camera']
    cam.parent = empty
    
    S.objects.link(empty)
    S.objects.active = empty
    
    n_angles = 10
    rot_angle = 360 / n_angles
    
    S.render.use_file_extension = False
    
    for output_node in [colorFileOutput, depthFileOutput, depthFileOutputEXR]:
        output_node.base_path = ''
    
    for i in range(n_angles):
        angle = i * rot_angle
        empty.rotation_euler[2] = radians(angle) % radians(360)
        
        file_name = "angle_{a}".format(a = angle)
        
        with open(join(RENDER_DESTINATION, CAMERA_PARAMS_FOLDER, file_name), 'w') as params_file:
            params_file.write("K*RT: " + str(get_3x4_P_matrix_from_blender(cam)[0]) + '\n' 
                            + "K: " + str(get_3x4_P_matrix_from_blender(cam)[1]) + '\n'
                            + "RT: " + str(get_3x4_P_matrix_from_blender(cam)[2]))
            
        bgnode.image = D.images.load(RENDER_DESTINATION + "/background.png")
        
        S.render.filepath = join(RENDER_DESTINATION, file_name) + ".png"
        
        depthFileOutputEXR.base_path = join(RENDER_DESTINATION, DEPTH_MAP_FOLDER)
        depthFileOutputEXR.file_slots[0].path = join(RENDER_DESTINATION, DEPTH_MAP_FOLDER, file_name) + ".exr"
        
        depthFileOutput.file_slots[0].path = join(RENDER_DESTINATION, DEPTH_MAP_FOLDER, file_name) + ".png"
        
        colorFileOutput.file_slots[0].path = join(RENDER_DESTINATION, file_name) + ".png"
    
        bpy.ops.render.render(animation=False, write_still = True)
        
        # remove 0001 at end
        shutil.move(join(RENDER_DESTINATION, DEPTH_MAP_FOLDER, file_name) + ".png0001", join(RENDER_DESTINATION, DEPTH_MAP_FOLDER, file_name) + ".png")
        shutil.move(join(RENDER_DESTINATION, file_name) + ".png0001", join(RENDER_DESTINATION, file_name) + ".png")
        shutil.move(join(RENDER_DESTINATION, DEPTH_MAP_FOLDER) + "0001", join(RENDER_DESTINATION, DEPTH_MAP_FOLDER, file_name) + ".exr")
        
main()


# TODO add args to main method and finish following code
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Renders given obj file by rotation a camera around it.')
    parser.add_argument('--views', type=int, default=18,
                        help='number of views to be rendered')
    parser.add_argument('--obj', type=str, default=None,
                        help='Path to the obj file to be rendered. Will be rendered to the Manual subfolder of output_folder. Stops crawling of the ShapeNet path.')
    parser.add_argument('--shapenet_dir',type=str, default='/scratch/sdonne/datasets/ShapeNet/ShapeNetCore.v2',
                        help='ShapeNet path to crawl.')
    parser.add_argument('--output_folder', type=str, default='/scratch/sdonne/datasets/ShapeNet/generated/',
                        help='The path the output will be dumped to.')

    try:
        argv = sys.argv[sys.argv.index("-- ") + 1:]
    except ValueError:
        argv = ""
    args = parser.parse_args(argv)
    
    #check args.obj: if it is set, we render that one to the 'manual' directory -- otherwise we render everything we can find
    if args.obj:
        main("manual",len(glob.glob(args.output_folder+'/manual/*'))+1,args)

