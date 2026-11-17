"""Renders the debris art from the game's art camera, grey and lit by the
game's sun, at 8 times game size. Piles also get an id pass, each chunk's
number as a grey level.

Usage: blender -b --python render_assets.py -- <output folder> [groups]
Groups, comma separated: rocks, puffs, craters, piles, materials (default all).
"""

import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Euler, Vector

SCALE = 8
DIRECTION = Vector((0, math.cos(math.radians(30)), -math.sin(math.radians(30))))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = False
    scene.cycles.device = "CPU"
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "16"
    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    scene.world = world
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(4)
    sun.rotation_euler = (math.radians(52), 0, math.radians(125))
    scene.collection.objects.link(sun)
    return scene


def camera(scene, target, width, height):
    cam = bpy.data.objects.new("art", bpy.data.cameras.new("art"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(width, height)
    cam.location = Vector(target) - DIRECTION * 1000
    cam.rotation_euler = (math.radians(60), 0, 0)
    cam.data.clip_end = 5000
    if width >= height:
        cam.data.sensor_fit = "HORIZONTAL"
    else:
        cam.data.sensor_fit = "VERTICAL"
    scene.render.resolution_x = width * SCALE
    scene.render.resolution_y = height * SCALE
    return cam


def material(name, color=(0.8, 0.8, 0.8), emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    if emission is not None:
        nodes.remove(bsdf)
        out = nodes["Material Output"]
        node = nodes.new("ShaderNodeEmission")
        node.inputs["Color"].default_value = (*emission, 1)
        node.inputs["Strength"].default_value = 1.0
        mat.node_tree.links.new(node.outputs[0], out.inputs[0])
    return mat


def rock_mesh(name, size, seed, flat=0.75):
    rng = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for vertex in bm.verts:
        vertex.co *= rng.uniform(0.72, 1.18)
    bmesh.ops.scale(bm, vec=(size * rng.uniform(0.9, 1.25), size * rng.uniform(0.75, 1.0), size * flat), verts=bm.verts)
    # A few cuts make it look broken off.
    for _ in range(2):
        normal = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
        result = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=normal * size * 0.55, plane_no=normal, clear_outer=True)
        edges = [e for e in result["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            bmesh.ops.edgeloop_fill(bm, edges=edges)
    bm.to_mesh(mesh)
    bm.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = False
    return mesh


def plank_mesh(name, length, width, thick, seed):
    """A board snapped at both ends into splinters."""
    rng = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(length, width, thick), verts=bm.verts)
    edges = [e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > length * 0.5]
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=6, use_grid_fill=True)
    for vertex in bm.verts:
        end = abs(vertex.co.x) / (length / 2)
        if end > 0.99:
            # Splintered ends: some fibers stick out further than others.
            vertex.co.x *= 1 + rng.uniform(-0.35, 0.12)
        vertex.co.y += rng.uniform(-0.06, 0.06) * width
        vertex.co.z += rng.uniform(-0.08, 0.08) * thick
    bm.to_mesh(mesh)
    bm.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = False
    return mesh


def sheet_mesh(name, radius, seed, bend, wave, thick=0.35):
    """A torn sheet: a ragged outline, bent (metal) or rippled (cloth)."""
    rng = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    corners = rng.randint(6, 9)
    angles = sorted(rng.uniform(0, math.tau) for _ in range(corners))
    verts = []
    for angle in angles:
        r = radius * rng.uniform(0.45, 1.0)
        verts.append(bm.verts.new((math.cos(angle) * r * 1.3, math.sin(angle) * r * 0.8, 0)))
    face = bm.faces.new(verts)
    bmesh.ops.triangulate(bm, faces=[face])
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
    phase = rng.uniform(0, math.tau)
    for vertex in bm.verts:
        x, y = vertex.co.x, vertex.co.y
        vertex.co.z = bend * (x / radius) ** 2 * radius + wave * radius * math.sin(x / radius * 4 + phase) * math.cos(y / radius * 3 - phase)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    bm.to_mesh(mesh)
    bm.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = wave > 0
    return mesh


def chunk_mesh(kind, name, size, seed):
    rng = random.Random(seed)
    if kind == "plank":
        return plank_mesh(name, size * rng.uniform(1.8, 2.6), size * rng.uniform(0.6, 0.75), size * rng.uniform(0.3, 0.38), seed)
    if kind == "shard":
        return sheet_mesh(name, size, seed, rng.uniform(0.15, 0.45), 0.0, 0.25)
    if kind == "scrap":
        return sheet_mesh(name, size, seed, 0.0, rng.uniform(0.12, 0.2), 0.2)
    return rock_mesh(name, size, seed, flat=rng.uniform(0.45, 0.8))


def chunk_material(kind):
    if kind == "shard":
        mat = material("metal", color=(0.75, 0.75, 0.75))
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Metallic"].default_value = 0.6
        bsdf.inputs["Roughness"].default_value = 0.45
        return mat
    return material("grey")


def render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def rocks(out):
    for variant in range(4):
        scene = reset()
        size = [4.2, 5.0, 3.6, 4.6][variant]
        obj = bpy.data.objects.new("rock", rock_mesh("rock", size, 100 + variant))
        scene.collection.objects.link(obj)
        obj.data.materials.append(material("grey"))
        camera(scene, (0, 0, 0), 16, 16)
        axis = Vector((random.Random(variant).uniform(-1, 1), 0.6, 1.0)).normalized()
        for frame in range(8):
            obj.rotation_mode = "AXIS_ANGLE"
            obj.rotation_axis_angle = (frame * math.pi / 4, *axis)
            render(scene, os.path.join(out, f"rock{variant}_{frame}.png"))


def flat(out, name, width, height):
    """A flat ground plane: what the floor's light looks like."""
    scene = reset()
    bpy.ops.mesh.primitive_plane_add(size=max(width, height) * 4)
    plane = bpy.context.active_object
    plane.data.materials.append(material("grey"))
    camera(scene, (0, 0, 0), width, height)
    render(scene, os.path.join(out, name))


def crater(out, name, width, height, radius, seed):
    rng = random.Random(seed)
    scene = reset()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=220, y_subdivisions=220, size=radius * 3.4)
    ground = bpy.context.active_object
    bowl = radius * 0.72
    depth = radius * 0.34
    rim = radius * 0.13
    bumps = [(rng.uniform(-1.4, 1.4) * radius, rng.uniform(-1.4, 1.4) * radius, rng.uniform(0.04, 0.12) * radius, rng.uniform(0.06, 0.16) * radius) for _ in range(70)]
    for vertex in ground.data.vertices:
        x, y = vertex.co.x, vertex.co.y
        r = math.hypot(x, y)
        angle = math.atan2(y, x)
        # Irregular outline; none at the middle, where the angle means nothing.
        wobble = 1 + (0.08 * math.sin(angle * 5 + seed) + 0.05 * math.sin(angle * 11 + seed * 3)) * min(1.0, r / bowl)
        rr = r / wobble
        z = 0.0
        if rr < bowl:
            z -= depth * (1 - (rr / bowl) ** 2)
        z += rim * math.exp(-((rr - bowl) / (radius * 0.2)) ** 2)
        # Thrown out earth, thinning outward.
        z += rim * 0.35 * math.exp(-((rr - bowl * 1.35) / (radius * 0.3)) ** 2) * (0.6 + 0.4 * math.sin(angle * 7 + seed))
        for bx, by, bh, bw in bumps:
            d = math.hypot(x - bx, y - by)
            if d < bw * 2.5 and r > bowl * 0.6:
                z += bh * math.exp(-(d / bw) ** 2)
        vertex.co.z = z
    for polygon in ground.data.polygons:
        polygon.use_smooth = True
    ground.data.materials.append(material("grey"))
    # Clods around the rim.
    for index in range(int(radius * 0.9)):
        angle = rng.uniform(0, math.tau)
        distance = bowl * rng.uniform(0.95, 1.7)
        size = rng.uniform(0.9, 2.2)
        clod = bpy.data.objects.new("clod", rock_mesh("clod", size, seed * 1000 + index, flat=0.6))
        clod.location = (math.cos(angle) * distance, math.sin(angle) * distance, rim * 0.5)
        clod.rotation_euler = Euler((rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3)))
        clod.data.materials.append(bpy.data.materials["grey"])
        scene.collection.objects.link(clod)
    camera(scene, (0, 0, 0), width, height)
    render(scene, os.path.join(out, name))


def tumbling(out, kind, sizes, canvas):
    for variant, size in enumerate(sizes):
        scene = reset()
        obj = bpy.data.objects.new(kind, chunk_mesh(kind, kind, size, 700 + variant * 13 + len(kind)))
        scene.collection.objects.link(obj)
        obj.data.materials.append(chunk_material(kind))
        camera(scene, (0, 0, 0), canvas, canvas)
        axis = Vector((random.Random(variant + 50).uniform(-1, 1), 0.6, 1.0)).normalized()
        for frame in range(8):
            obj.rotation_mode = "AXIS_ANGLE"
            obj.rotation_axis_angle = (frame * math.pi / 4, *axis)
            render(scene, os.path.join(out, f"{kind}{variant}_{frame}.png"))


def pile(out, name, width, height, radius, count, seed, kind="rock"):
    rng = random.Random(seed)
    # Boards and sheets lie flat and spread wider than a heap of stones.
    flat_kind = kind != "rock"
    for pass_name in ("shade", "id"):
        scene = reset()
        grey = chunk_material(kind)
        for index in range(count):
            size = rng.uniform(0.18, 0.34) * radius
            angle = rng.uniform(0, math.tau)
            distance = radius * math.sqrt(rng.uniform(0, 1)) * 0.8
            height_above = (1 - distance / radius) * radius * (0.18 if flat_kind else 0.35) + size * 0.4
            mesh = chunk_mesh(kind, f"chunk{index}", size, seed * 1000 + index)
            chunk = bpy.data.objects.new(f"chunk{index}", mesh)
            chunk.location = (math.cos(angle) * distance, math.sin(angle) * distance, height_above)
            if flat_kind:
                chunk.rotation_euler = Euler((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(0, math.tau)))
            else:
                chunk.rotation_euler = Euler((rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3)))
            if pass_name == "shade":
                chunk.data.materials.append(grey)
            else:
                value = (index % 8) / 8.0 + 1 / 16.0
                chunk.data.materials.append(material(f"id{index}", emission=(value, value, value)))
            scene.collection.objects.link(chunk)
        rng = random.Random(seed)
        camera(scene, (0, 0, radius * 0.15), width, height)
        if pass_name == "id":
            scene.cycles.samples = 1
            scene.cycles.filter_width = 0.01
            scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
            for obj in scene.objects:
                if obj.type == "LIGHT":
                    obj.data.energy = 0
        render(scene, os.path.join(out, f"{name}_{pass_name}.png"))


def puff(out, name, size, seed):
    rng = random.Random(seed)
    scene = reset()
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.1
    ball = bpy.data.metaballs.new("puff")
    ball.resolution = 0.6
    obj = bpy.data.objects.new("puff", ball)
    scene.collection.objects.link(obj)
    # A cauliflower: a few big lumps with small ones on their surface.
    lumps = []
    for index in range(rng.randint(4, 6)):
        center = Vector((rng.uniform(-1, 1) * size * 0.16, rng.uniform(-1, 1) * size * 0.1, rng.uniform(-0.6, 1) * size * 0.14))
        radius = size * rng.uniform(0.14, 0.2)
        lumps.append((center, radius))
    for center, radius in list(lumps):
        for _ in range(rng.randint(4, 7)):
            direction = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 1))).normalized()
            lumps.append((center + direction * radius * 0.85, radius * rng.uniform(0.35, 0.6)))
    for center, radius in lumps:
        element = ball.elements.new()
        element.radius = radius
        element.co = center
    obj.data.materials.append(material("grey", color=(0.9, 0.9, 0.9)))
    camera(scene, (0, 0, 0), size, size)
    render(scene, os.path.join(out, name))


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    out = arguments[0]
    groups = arguments[1].split(",") if len(arguments) > 1 else ["rocks", "puffs", "craters", "piles", "materials"]
    os.makedirs(out, exist_ok=True)
    if "rocks" in groups:
        rocks(out)
        flat(out, "rock_flat.png", 16, 16)
    if "puffs" in groups:
        for variant in range(4):
            puff(out, f"puff{variant}.png", 48, 200 + variant)
    if "craters" in groups:
        for size, (width, height, radius) in {"s": (60, 34, 19), "m": (84, 46, 27), "l": (120, 64, 39)}.items():
            flat(out, f"crater{size}_flat.png", width, height)
            for variant in range(2):
                crater(out, f"crater{size}{variant}.png", width, height, radius, 300 + variant * 10 + len(size) + ord(size))
    if "piles" in groups:
        for size, (width, height, radius, count) in {"s": (36, 26, 11, 9), "l": (58, 40, 18, 17)}.items():
            for variant in range(3):
                pile(out, f"pile{size}{variant}", width, height, radius, count, 500 + variant * 7 + ord(size))
    if "materials" in groups:
        tumbling(out, "plank", [4.6, 5.4, 3.6, 4.2], 20)
        tumbling(out, "shard", [4.2, 5.0, 3.4, 4.6], 18)
        tumbling(out, "scrap", [4.8, 5.6, 4.0, 5.2], 20)
        # Wood, metal and cloth heaps; stone keeps the rock piles.
        for prefix, kind in {"w": "plank", "m": "shard", "c": "scrap"}.items():
            for size, (width, height, radius, count) in {"s": (36, 26, 11, 9 if kind == "shard" else 12), "l": (58, 40, 18, 16 if kind == "shard" else 22)}.items():
                for variant in range(2):
                    pile(out, f"pile{prefix}{size}{variant}", width, height, radius, count, 900 + variant * 7 + ord(size) + ord(prefix), kind)


main()
