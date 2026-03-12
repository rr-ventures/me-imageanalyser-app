"""
Metadata model for photo analysis results.

Defines the structure of metadata extracted from each photo.
This is the simplified 6-field set that Gemini returns.
"""
from dataclasses import dataclass


@dataclass
class PhotoMetadata:
    """
    The 6 metadata fields extracted from a dating/profile photo.

    Each field maps directly to what Gemini returns.
    """
    scene_type: str      # outdoor / indoor / urban / nightlife / unknown
    lighting: str        # natural_warm / natural_cool / golden_hour / artificial / mixed / unknown
    photo_quality: int   # 0-10
    face_visible: str    # yes / partial / no
    expression: str      # warm / neutral / serious / unknown
    color_quality: str   # good / flat / bad_mix / unknown

    @classmethod
    def from_dict(cls, data: dict) -> "PhotoMetadata":
        return cls(
            scene_type=data.get("scene_type", "unknown"),
            lighting=data.get("lighting", "unknown"),
            photo_quality=data.get("photo_quality", 5),
            face_visible=data.get("face_visible", "unknown"),
            expression=data.get("expression", "unknown"),
            color_quality=data.get("color_quality", "unknown"),
        )

    def to_dict(self) -> dict:
        return {
            "scene_type": self.scene_type,
            "lighting": self.lighting,
            "photo_quality": self.photo_quality,
            "face_visible": self.face_visible,
            "expression": self.expression,
            "color_quality": self.color_quality,
        }


@dataclass
class StyleResult:
    """The result of running the style selector on a photo's metadata."""
    primary_style: str
    secondary_style: str
    selection_reason: str
    primary_plans: dict
    secondary_plans: dict

    def to_dict(self) -> dict:
        return {
            "primary_style": self.primary_style,
            "secondary_style": self.secondary_style,
            "selection_reason": self.selection_reason,
            "primary_lightroom_plan": self.primary_plans.get("lightroom", {}),
            "secondary_lightroom_plan": self.secondary_plans.get("lightroom", {}),
        }
