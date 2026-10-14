from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import trimesh

ProgressCallback = Callable[[int, str], None]


def _report(callback: ProgressCallback | None, percent: int, message: str) -> None:
    if callback:
        callback(percent, message)


def _iter_components(mesh: trimesh.Trimesh) -> list[trimesh.Trimesh]:
    components = mesh.split(only_watertight=False)
    return [c for c in components if isinstance(c, trimesh.Trimesh)]


def _unwrap_uv(mesh: trimesh.Trimesh) -> None:
    vertices = np.asarray(mesh.vertices, dtype=np.float32)
    faces = np.asarray(mesh.faces, dtype=np.uint32)

    if len(vertices) == 0 or len(faces) == 0:
        raise ValueError("Mesh component is empty")

    try:
        import xatlas  # type: ignore

        _, _, uvs = xatlas.parametrize(vertices, faces)
        mesh.metadata["uv_map"] = {"method": "xatlas", "count": int(len(uvs))}
        return
    except Exception:
        pass

    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    scale = np.maximum(maxs[:2] - mins[:2], 1e-8)
    uvs = (vertices[:, :2] - mins[:2]) / scale
    mesh.metadata["uv_map"] = {"method": "planar", "count": int(len(uvs))}


def _solidify(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    mesh = mesh.copy()
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()

    if not mesh.is_watertight:
        mesh.fill_holes()

    extents = np.maximum(mesh.extents, 1e-6)
    pitch = max(float(np.min(extents) / 80.0), 0.1)
    voxelized = mesh.voxelized(pitch)
    solid_voxels = voxelized.fill()
    solid_mesh = solid_voxels.marching_cubes
    solid_mesh.remove_unreferenced_vertices()

    if len(solid_mesh.faces) == 0:
        raise ValueError("Solidification produced an empty mesh")

    return solid_mesh


def process_mesh(mesh: trimesh.Trimesh, progress: ProgressCallback | None = None) -> trimesh.Trimesh:
    _report(progress, 10, "Disconnecting mesh islands...")
    components = _iter_components(mesh)

    _report(progress, 25, "Filtering tiny artifacts...")
    filtered = [component for component in components if len(component.faces) >= 4]
    if not filtered:
        raise ValueError("No valid mesh components remain after artifact filtering")

    _report(progress, 45, "Applying UV unwrapping...")
    for component in filtered:
        _unwrap_uv(component)

    _report(progress, 65, "Merging processed components...")
    merged = trimesh.util.concatenate(filtered)

    _report(progress, 80, "Generating solid watertight mesh...")
    solid = _solidify(merged)

    _report(progress, 100, "Processing complete")
    return solid


def process_stl_file(input_path: str | Path, progress: ProgressCallback | None = None) -> trimesh.Trimesh:
    _report(progress, 2, "Loading STL...")
    mesh = trimesh.load_mesh(str(input_path), file_type="stl")

    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(g for g in mesh.geometry.values()))

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Unable to load STL as a mesh")

    return process_mesh(mesh, progress=progress)
