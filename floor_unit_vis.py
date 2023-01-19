bl_info = {
    "name": "Quick Floor Unit Viz",
    "description": "",
    "author": "tlp",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "location": "3D View > Tools",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}

import bpy

from mathutils import Vector

from bpy.props import BoolProperty, FloatProperty, IntVectorProperty, FloatVectorProperty, PointerProperty


# ===========================================================

# HELPER FUNCTIONS

# ===========================================================


def rgb_to_rgba(col):
    return (col[0], col[1], col[2], 1.0)

def get_collection(context):    
    # Create new floor square collection if it doesn't yet exist (modified from https://blender.stackexchange.com/questions/153713/removing-all-meshes-from-a-collection-with-python)
    collection_exists = False
    
    for collection in bpy.data.collections:
        if collection.name == "FloorSquareCollection":
            square_collection = collection
            collection_exists = True
            break
    
    if not collection_exists:
        square_collection = bpy.data.collections.new("FloorSquareCollection")
        context.scene.collection.children.link(square_collection)
        
    return square_collection



# Create new floor square material if it doesn't yet exist or if the forced material refresh option is toggled (modified from https://vividfax.github.io/2021/01/14/blender-materials.html)
def create_material(floor_props):
    square_mat = bpy.data.materials.get('FloorSquareMaterial')
    
    if square_mat is None:
        square_mat = bpy.data.materials.new(name='FloorSquareMaterial')
    square_mat.use_nodes = True
    square_mat.node_tree.links.clear()
    square_mat.node_tree.nodes.clear()
    nodes = square_mat.node_tree.nodes
    links = square_mat.node_tree.links
    
    # Geometry Input Node (the normal is the second output)
    geom_node = nodes.new(type="ShaderNodeNewGeometry")
    
    # Color Input Nodes
    color_x_node = nodes.new(type="ShaderNodeRGB")
    color_x_node.name = "XColor"
    color_x_node.outputs[0].default_value = rgb_to_rgba(floor_props.square_color_x)
    color_y_node = nodes.new(type="ShaderNodeRGB")
    color_y_node.name = "YColor"
    color_y_node.outputs[0].default_value = rgb_to_rgba(floor_props.square_color_y)
    color_z_node = nodes.new(type="ShaderNodeRGB")
    color_z_node.name = "ZColor"
    color_z_node.outputs[0].default_value = rgb_to_rgba(floor_props.square_color_z)
    
    # Squares the normal
    square_normal_node = nodes.new(type="ShaderNodeVectorMath")
    square_normal_node.operation = 'MULTIPLY'
    
    # Splits the normal into three separate outputs
    normal_split_node = nodes.new(type="ShaderNodeSeparateXYZ")
    
    # Color Normal Multiplication Nodes
    color_x_mul_normal_node = nodes.new(type="ShaderNodeVectorMath")
    color_x_mul_normal_node.operation = 'MULTIPLY'
    
    color_y_mul_normal_node = nodes.new(type="ShaderNodeVectorMath")
    color_y_mul_normal_node.operation = 'MULTIPLY'
    
    color_z_mul_normal_node = nodes.new(type="ShaderNodeVectorMath")
    color_z_mul_normal_node.operation = 'MULTIPLY'
    
    
    # Add Vector Colors Together
    add_colors_xy_node = nodes.new(type="ShaderNodeVectorMath")
    add_colors_xy_node.operation = 'ADD'
    
    add_colors_xyz_node = nodes.new(type="ShaderNodeVectorMath")
    add_colors_xyz_node.operation = 'ADD'
    
    
    # Diffuse Shader
    shader = nodes.new(type='ShaderNodeBsdfDiffuse')
    nodes["Diffuse BSDF"].inputs[0].default_value = rgb_to_rgba(floor_props.square_color_z)
    
    # Overall Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    
    
    # Set up node links
    links.new(geom_node.outputs[1], square_normal_node.inputs[0])
    links.new(geom_node.outputs[1], square_normal_node.inputs[1])
    
    links.new(square_normal_node.outputs[0], normal_split_node.inputs[0])
    
    links.new(color_x_node.outputs[0], color_x_mul_normal_node.inputs[0])
    links.new(color_y_node.outputs[0], color_y_mul_normal_node.inputs[0])
    links.new(color_z_node.outputs[0], color_z_mul_normal_node.inputs[0])
    links.new(normal_split_node.outputs[0], color_x_mul_normal_node.inputs[1])
    links.new(normal_split_node.outputs[1], color_y_mul_normal_node.inputs[1])
    links.new(normal_split_node.outputs[2], color_z_mul_normal_node.inputs[1])
    
    links.new(color_x_mul_normal_node.outputs[0], add_colors_xy_node.inputs[0])
    links.new(color_y_mul_normal_node.outputs[0], add_colors_xy_node.inputs[1])
    
    links.new(add_colors_xy_node.outputs[0], add_colors_xyz_node.inputs[0])
    links.new(color_z_mul_normal_node.outputs[0], add_colors_xyz_node.inputs[1])
    
    links.new(add_colors_xyz_node.outputs[0], shader.inputs[0])
    
    links.new(shader.outputs[0], output.inputs[0])


def update_material(self, context):
    floor_props = context.scene.floor_props

    square_mat = bpy.data.materials.get('FloorSquareMaterial')
    if square_mat is None or floor_props.refresh_material:
        create_material(floor_props)

    # Update Material Colors
    if square_mat.node_tree:
        nodes = square_mat.node_tree.nodes
        
        nodes["XColor"].outputs[0].default_value = rgb_to_rgba(floor_props.square_color_x)
        nodes["YColor"].outputs[0].default_value = rgb_to_rgba(floor_props.square_color_y)
        nodes["ZColor"].outputs[0].default_value = rgb_to_rgba(floor_props.square_color_z)
    
    
def update_visibility(self, context):
    floor_props = context.scene.floor_props
    
    square_collection = get_collection(context)
    square_layer_collection = context.view_layer.layer_collection.children[square_collection.name]
    square_layer_collection.hide_viewport = not floor_props.show_squares
    
    
    
def print_hit_result(success, hit_location, normal, poly_index, object, matrix):
    print("Success:", success)
    print("Hit Location:", hit_location)
    print("Normal:", normal)
    print("Polygon Index:", poly_index)
    print("Object:", object)
    print("Matrix:", matrix)




# ===========================================================

# CLASSES

# ===========================================================


# Sets up the various properties found in the panel
class FloorViewerProperties(bpy.types.PropertyGroup):
    show_squares : BoolProperty(name='Show Unit Squares', description='Toggles whether or not the unit squares should be displayed', default=True, update=update_visibility)
    grid_scale : FloatProperty(name='Unit Square Size', description='The length of the side of a unit square (in Blender Units)', default=1)
    grid_origin : FloatVectorProperty(name='Sample Grid Center', description='The X,Y center position for the samples taken', size = 2, default=(0,0))
    grid_dims : IntVectorProperty(name='Sample Grid Dimensions', description='The x-width and y-width of the grid respectively', size = 2, min = 1, default=(10,10))
    start_height : FloatProperty(name='Sample Starting Height', description='The height at which the sample rays are cast', default=5000)
    sample_offset_h : FloatProperty(name='Sample Offset Height', description='A height offset applied to the unit squares to avoid z-fighting/clipping between the unit squares and the original surface', default=0.01)
    sample_adjust_s : FloatProperty(name='Sample Scale Adjustment', description='A scaling adjustment used to avoid having ray_cast() intersect the already generated unit squares', min=0, max=1, default=0.99)
    square_color_x : FloatVectorProperty(name='Unit Square Color (X-Projecting Normal)', description='The color assigned to the cubes\' X-Projecting faces', subtype="COLOR", size=3, min=0.0, max=1.0, default=(0.0,1.0,0.5), update=update_material)
    square_color_y : FloatVectorProperty(name='Unit Square Color (Y-Projecting Normal)', description='The color assigned to the cubes\' Y-Projecting faces', subtype="COLOR", size=3, min=0.0, max=1.0, default=(1.0,1.0,0.0), update=update_material)
    square_color_z : FloatVectorProperty(name='Unit Square Color (Z-Projecting Normal)', description='The color assigned to the cubes\' Z-Projecting faces', subtype="COLOR", size=3, min=0.0, max=1.0, default=(0.0,0.5,1.0), update=update_material)
    refresh_material : BoolProperty(name='Refresh Material', description='Forces a rebuild of the material, in case it gets messed up', default=False)
  

# Defines the operator used for generating the squares
class GenerateSquares(bpy.types.Operator):
    bl_label = "Create/Update Squares"
    bl_idname = "wm.generate_squares"
    
                                
    def execute(self, context):
        scene = context.scene
        floor_props = scene.floor_props
        
        
        # Create new floor square collection if it doesn't yet exist (modified from https://blender.stackexchange.com/questions/153713/removing-all-meshes-from-a-collection-with-python)
        square_collection = get_collection(context)   
            
        # Here we get a copy of the current active collection layer and set our custom collection layer to the active collection layer. This is to avoid having the floor squares in both the previously active collection and the custom collection.    
        square_layer_collection = context.view_layer.layer_collection.children[square_collection.name]
        square_layer_collection.hide_viewport = False 
        
        old_active_layer_collection = context.view_layer.active_layer_collection
        context.view_layer.active_layer_collection = square_layer_collection
        
        
        if floor_props.refresh_material or bpy.data.materials.get('FloorSquareMaterial') == None:      
            update_material(self, context)    
        
        square_mat = bpy.data.materials.get('FloorSquareMaterial')
    
        # Delete Old Squares        
        square_collection = bpy.data.collections["FloorSquareCollection"]
        for square in square_collection.objects:
            bpy.data.objects.remove(square, do_unlink=True)
          

        # Generate New Squares (sequential, synthesized from lots of StackOverflow answers)
        x_center, y_center = floor_props.grid_origin
        x_width, y_width = floor_props.grid_dims
        scale = floor_props.grid_scale
        
        # Loop through x,y grid
        for x in range(x_width):
            dx = x - x_width / 2
            for y in range(y_width):
                dy = y - y_width / 2
                
                # Cast a ray along the minimum x,y value for each grid square
                ray_origin = Vector((x_center + dx * scale, y_center + dy * scale, floor_props.start_height))
                ray_direction = Vector((0,0,-1))
                
                success, hit_location, normal, poly_index, object, matrix = scene.ray_cast(context.view_layer.depsgraph, ray_origin, ray_direction)
                
                # If successful, create a unit square, assign it to the collection of floor squares, assign the appropriate material, and set the appropriate visibility.
                if(success):
                    # Cubes in Blender have origins at their center, so here we compute where the center would be based on the grid parameters floor box size of 78 units
                    square_center = hit_location + 0.5 * scale * Vector((1,1,0)) + Vector((0,0, floor_props.sample_offset_h)) - Vector((0,0,78 * scale / 2))
                    
                    # Here we add the cube, with the scale set so that X & Y are slightly less (see scale adjustment) than the grid scale, and Z is 78
                    bpy.ops.mesh.primitive_cube_add(size=scale * floor_props.sample_adjust_s, enter_editmode=False, location=square_center, scale = Vector((1,1,78 / floor_props.sample_adjust_s)))
                    
                    # Here we assign the cube's name, material, and visibility in that order
                    context.active_object.name = 'FloorSquare_' + str(x) + "_" + str(y)
                    context.active_object.data.materials.append(square_mat)

                    
        
        floor_props.show_squares = True           
        
        # Setting the collection layer back to the default
        context.view_layer.active_layer_collection = old_active_layer_collection
        
        return {'FINISHED'}
        

class FloorViewerParent:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Floor Shenanigans'
    bl_options = {'DEFAULT_CLOSED'}
    
        
class FloorViewerMainPanel(FloorViewerParent, bpy.types.Panel):
    bl_idname = "floor_vis"
    bl_label = "Floor Unit Visualizer"
     
    # Sets up the layout of the floor visualization panel 
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        floor_props = scene.floor_props
        layout.prop(floor_props, "show_squares")
        layout.separator()
        layout.prop(floor_props, "square_color_x")
        layout.prop(floor_props, "square_color_y")
        layout.prop(floor_props, "square_color_z")
        layout.separator()
        layout.prop(floor_props, "refresh_material")
        layout.separator()
        layout.separator()        
        layout.prop(floor_props, "grid_origin")
        layout.prop(floor_props, "grid_dims")
        layout.prop(floor_props, "grid_scale")
        layout.separator()
        layout.prop(floor_props, "start_height")
        layout.prop(floor_props, "sample_offset_h")
        layout.prop(floor_props, "sample_adjust_s")
        layout.separator()
        layout.operator("wm.generate_squares")
        
 
 
 
# ===========================================================

# REGISTERING

# =========================================================== 
 
 
classes = (
    FloorViewerProperties,
    GenerateSquares,
    FloorViewerMainPanel
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.floor_props = PointerProperty(type=FloorViewerProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
                
    del bpy.types.Scene.floor_props

            
if __name__ == "__main__":
    register()