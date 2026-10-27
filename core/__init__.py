"""
Wan-ViTPose Actor Replacement Core Module
"""
from .masking import generate_expanded_hair_mask, create_inverted_face_oval_mask
from .harmonize import harmonize_and_composite
from .comfy_client import ComfyClient
from .timeline import assemble_timeline
from .master_keyframe import create_facial_geometry_anchor, build_master_keyframe_prompt

__all__ = [
    "generate_expanded_hair_mask",
    "create_inverted_face_oval_mask",
    "harmonize_and_composite",
    "ComfyClient",
    "assemble_timeline",
    "create_facial_geometry_anchor",
    "build_master_keyframe_prompt",
]
