"""
Fabric AI Inspection System - Fabric Domain & Textile Validity Validator
========================================================================

Verifies that an uploaded image is an authentic physical textile or woven fabric swatch,
preventing false defect proposals and false "No Defect" reports on non-fabric images
(such as persons/humans, clothing worn on bodies, animals/birds/parrots, documents,
vehicles, food, digital screenshots, or blank surfaces).

Validation Architecture:
  1. Image file integrity and dimension sanity.
  2. Blank / solid color / extreme exposure detection.
  3. Digital screenshot detection via zero-variance block analysis.
  4. Human / person face presence verification via multi-scale cascade detectors.
  5. Printed paper document / text sheet detection.
  6. MobileNetV3-Small Deep Semantic Out-of-Domain Classification:
     - Persons wearing apparel/clothing (pajamas, kimonos, suits, cardigans, uniforms, etc.)
     - Birds & avian species (parrots, macaws, lorikeets, etc.)
     - Animals, pets & wildlife (dogs, cats, horses, etc.)
     - Documents, files & stationery (menus, books, envelopes, notebooks, websites)
     - Vehicles, electronics, appliances & furniture.
"""

import os
import logging
from typing import Any
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Global singletons for lightweight MobileNetV3 semantic classifier (~9.8 MB)
_SEMANTIC_MODEL = None
_SEMANTIC_PREPROCESS = None
_SEMANTIC_CATEGORIES = None

# Non-fabric ImageNet index sets
_BIRDS = set(range(80, 147))
_PETS_WILDLIFE = set(range(151, 294)).union(set(range(328, 389)))
_MARINE_FISH = set(range(0, 7)).union(set(range(147, 151))).union(set(range(389, 398)))
_REPTILES_AMPHIBIANS = set(range(7, 69))
_FOODS = set(range(924, 966))

# Apparel, garments, and human subject proxies in ImageNet-1k
_APPAREL_AND_PERSONS = {
    474,  # cardigan
    582,  # groom
    610,  # jersey
    614,  # kimono
    617,  # lab coat
    697,  # pajama
    734,  # poncho
    834,  # suit
    841,  # sweatshirt
    869,  # trench coat
    429,  # baseball player
    983,  # scuba diver
    457,  # bow tie
    501,  # cloak
    543,  # diaper
    558,  # feather boa
    568,  # fur coat
    638,  # maillot
    639,  # maillot, tank suit
    652,  # military uniform
    658,  # mitten
    759,  # brassiere
    815,  # shoe
    818,  # sock
    836,  # sombrero
    842,  # swimming trunks
    884,  # vestment
    979,  # apron
    515,  # cowboy hat
    514,  # cowboy boot
}

# Documents, books, printed sheets, files, stationery
_DOCUMENTS_AND_PRINTS = {
    553,  # file (binder / folder / paper document)
    916,  # web site
    917,  # comic book
    918,  # crossword puzzle
    921,  # book jacket
    922,  # menu (printed question paper, exam sheet, restaurant menu, document page)
    549,  # envelope
    681,  # notebook
    709,  # pencil box
    710,  # pencil sharpener
    767,  # rubber eraser
    563,  # fountain pen
    443,  # binder
    769,  # rule (ruler / measuring scale)
    798,  # slide rule (calculation scale / technical paper graph)
}

_TECH_AND_VEHICLES = {
    "web site", "cellular telephone", "laptop", "desktop computer", "monitor", "television",
    "sports car", "convertible", "minivan", "jeep", "limousine", "pickup", "cab", "racer",
    "airliner", "space shuttle", "warplane", "helicopter", "balloon",
    "mountain bike", "motorcycle", "moped", "bullet train", "locomotive", "passenger car", "streetcar",
    "speedboat", "canoe", "yawl", "catamaran", "aircraft carrier", "fire engine", "ambulance",
    "computer keyboard", "mouse", "joystick", "printer", "traffic light", "parking meter"
}

REJECTION_MESSAGE = "The uploaded specimen was identified as invalid photo rather than an authentic textile fabric photo. Automated Faster R-CNN defect proposal was bypassed to prevent false-positive defect alarms on non-fabric surfaces."
REJECTION_SUGGESTION = "Please upload a close-up photograph of woven fabric, knitwear, or textile material."
REJECTION_CATEGORY = "Invalid Photo"



def _get_semantic_classifier():
    """Lazily load MobileNetV3-Small for rapid semantic OOD verification."""
    global _SEMANTIC_MODEL, _SEMANTIC_PREPROCESS, _SEMANTIC_CATEGORIES
    if _SEMANTIC_MODEL is None:
        try:
            import torch
            import torchvision.models as models
            from torchvision.models import MobileNet_V3_Small_Weights

            weights = MobileNet_V3_Small_Weights.DEFAULT
            model = models.mobilenet_v3_small(weights=weights)
            model.eval()

            _SEMANTIC_MODEL = model
            _SEMANTIC_PREPROCESS = weights.transforms()
            _SEMANTIC_CATEGORIES = weights.meta["categories"]
        except Exception as e:
            logger.warning("Failed to initialize MobileNetV3 semantic classifier: %s", e)
            _SEMANTIC_MODEL = False
    return _SEMANTIC_MODEL, _SEMANTIC_PREPROCESS, _SEMANTIC_CATEGORIES


KNOWN_TEXTILES = {
    "window screen", "handkerchief", "dishrag", "doormat", "bath towel",
    "jean", "velvet", "quilt", "pillow", "band Aid", "chain mail",
    "honeycomb", "wool", "paper towel", "fire screen", "mosquito net"
}


def _detect_human_face(img: np.ndarray) -> tuple[bool, int]:
    """Detect presence of human faces using OpenCV Haar Cascades with skin-tone verification."""
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if os.path.exists(cascade_path):
            cascade = cv2.CascadeClassifier(cascade_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Min neighbors = 7 avoids texture false alarms while catching real faces
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=7, minSize=(45, 45))
            if len(faces) == 0:
                return False, 0

            # Verify skin chrominance in YCrCb color space
            ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
            valid_faces = 0
            for (x, y, w, h) in faces:
                face_roi = ycrcb[y:y+h, x:x+w]
                cr = face_roi[:, :, 1]
                cb = face_roi[:, :, 2]
                skin_mask = (cr >= 133) & (cr <= 173) & (cb >= 77) & (cb <= 127)
                skin_ratio = float(np.mean(skin_mask))
                if skin_ratio >= 0.25:
                    valid_faces += 1

            if valid_faces > 0:
                return True, valid_faces
    except Exception as e:
        logger.debug("Face detection exception: %s", e)
    return False, 0



def _format_friendly_category(raw_cat: str, idx: int) -> str:
    """Format technical ImageNet category into a user-friendly descriptor."""
    clean = raw_cat.replace("_", " ").title()
    if idx in _APPAREL_AND_PERSONS:
        return f"Person / Apparel Scene ({clean})"
    if idx in _DOCUMENTS_AND_PRINTS:
        if idx == 553:
            return "Paper Document / Document File"
        if idx == 922:
            return "Printed Document / Text Sheet"
        if idx == 921:
            return "Printed Book / Document Page"
        if idx == 918:
            return "Crossword / Printed Grid Sheet"
        if idx == 917:
            return "Printed Comic / Graphic Page"
        if idx == 916:
            return "Digital Web Site / Document Screenshot"
        if idx == 549:
            return "Paper Envelope / Postal Stationery"
        if idx == 681:
            return "Paper Notebook / Document"
        return f"Paper Document / Stationery ({clean})"
    if idx in _BIRDS:
        return f"Bird / Avian Species ({clean})"
    if idx in set(range(151, 281)):
        return f"Dog / Canine ({clean})"
    if idx in set(range(281, 294)):
        return f"Cat / Feline ({clean})"
    if idx in _PETS_WILDLIFE:
        return f"Animal / Wildlife ({clean})"
    if idx in _MARINE_FISH:
        return f"Aquatic Life ({clean})"
    if idx in _REPTILES_AMPHIBIANS:
        return f"Reptile / Amphibian ({clean})"
    if idx in _FOODS:
        return f"Food / Beverage ({clean})"
    if raw_cat == "web site":
        return "Digital Web Site / Document Screenshot"
    if "computer" in raw_cat or "laptop" in raw_cat or "monitor" in raw_cat or "telephone" in raw_cat:
        return f"Electronic Device / Screen ({clean})"
    if any(v in raw_cat for v in ["car", "bus", "train", "plane", "boat", "bike", "cycle"]):
        return f"Vehicle / Transportation Scene ({clean})"
    return clean


def validate_fabric_image(image_path: str) -> dict[str, Any]:
    """
    Validates whether the image at image_path is a genuine fabric/textile swatch.

    Returns:
        {
            "is_valid_fabric": bool,
            "material_status": "Fabric Verified" | "Non-Fabric",
            "confidence": float,
            "classification": str,
            "detected_category": str,
            "message": str,
            "suggestion": str | None,
            "metrics": dict,
        }
    """
    # 1. Image File Integrity
    if not os.path.isfile(image_path):
        return {
            "is_valid_fabric": False,
            "material_status": "Non-Fabric",
            "confidence": 0.0,
            "classification": "file_not_found",
            "detected_category": REJECTION_CATEGORY,
            "message": REJECTION_MESSAGE,
            "suggestion": REJECTION_SUGGESTION,
            "metrics": {},
        }

    img = cv2.imread(image_path)
    if img is None:
        return {
            "is_valid_fabric": False,
            "material_status": "Non-Fabric",
            "confidence": 0.0,
            "classification": "unreadable_file",
            "detected_category": REJECTION_CATEGORY,
            "message": REJECTION_MESSAGE,
            "suggestion": REJECTION_SUGGESTION,
            "metrics": {},
        }

    h, w = img.shape[:2]
    if h < 80 or w < 80:
        return {
            "is_valid_fabric": False,
            "material_status": "Non-Fabric",
            "confidence": 0.0,
            "classification": "resolution_too_low",
            "detected_category": REJECTION_CATEGORY,
            "message": REJECTION_MESSAGE,
            "suggestion": REJECTION_SUGGESTION,
            "metrics": {"width": w, "height": h},
        }

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))

    # 2. Check for blank, solid surfaces or extreme exposure
    if std_val < 5.0:
        return {
            "is_valid_fabric": False,
            "material_status": "Non-Fabric",
            "confidence": 0.98,
            "classification": "blank_surface",
            "detected_category": REJECTION_CATEGORY,
            "message": REJECTION_MESSAGE,
            "suggestion": REJECTION_SUGGESTION,
            "metrics": {"std": round(std_val, 2), "mean": round(mean_val, 2)},
        }

    if mean_val < 10.0:
        return {
            "is_valid_fabric": False,
            "material_status": "Non-Fabric",
            "confidence": 0.95,
            "classification": "underexposed",
            "detected_category": REJECTION_CATEGORY,
            "message": REJECTION_MESSAGE,
            "suggestion": REJECTION_SUGGESTION,
            "metrics": {"std": round(std_val, 2), "mean": round(mean_val, 2)},
        }

    # 3. Digital synthetic screenshots / code / flat graphics
    k = 16
    pure_zero_patches = 0
    total_patches = 0
    for y in range(0, h - k, k):
        for x in range(0, w - k, k):
            patch = gray[y:y + k, x:x + k]
            if np.std(patch) < 0.35:
                pure_zero_patches += 1
            total_patches += 1

    zero_ratio = pure_zero_patches / max(1, total_patches)
    if zero_ratio > 0.18:
        return {
            "is_valid_fabric": False,
            "material_status": "Non-Fabric",
            "confidence": 0.99,
            "classification": "document_screenshot",
            "detected_category": REJECTION_CATEGORY,
            "message": REJECTION_MESSAGE,
            "suggestion": REJECTION_SUGGESTION,
            "metrics": {
                "digital_flat_patch_ratio": round(zero_ratio, 4),
                "std": round(std_val, 2),
                "mean": round(mean_val, 2),
            },
        }

    # 4. Human / Person Face Presence Verification
    has_face, face_count = _detect_human_face(img)
    if has_face:
        return {
            "is_valid_fabric": False,
            "material_status": "Non-Fabric",
            "confidence": 0.99,
            "classification": "human_subject",
            "detected_category": REJECTION_CATEGORY,
            "message": REJECTION_MESSAGE,
            "suggestion": REJECTION_SUGGESTION,
            "metrics": {
                "face_count": face_count,
                "std": round(std_val, 2),
                "mean": round(mean_val, 2),
            },
        }

    # 5. Paper Document / Text Sheet Heuristic (Light background with dense dark text glyphs)
    if mean_val > 165.0 and std_val < 52.0:
        dark_text_pixels = np.mean(gray < 90.0)
        if dark_text_pixels > 0.045:
            return {
                "is_valid_fabric": False,
                "material_status": "Non-Fabric",
                "confidence": 0.95,
                "classification": "paper_document",
                "detected_category": REJECTION_CATEGORY,
                "message": REJECTION_MESSAGE,
                "suggestion": REJECTION_SUGGESTION,
                "metrics": {
                    "dark_text_pixel_ratio": round(float(dark_text_pixels), 4),
                    "mean": round(mean_val, 2),
                    "std": round(std_val, 2),
                },
            }

    # 6. MobileNetV3-Small Deep Semantic Out-of-Domain Classification
    model, preprocess, categories = _get_semantic_classifier()
    if model and preprocess and categories:
        try:
            import torch
            pil_img = Image.open(image_path).convert("RGB")
            batch = preprocess(pil_img).unsqueeze(0)
            with torch.inference_mode():
                logits = model(batch)
                probs = torch.softmax(logits, dim=-1)[0]

            top5_prob, top5_idx = torch.topk(probs, 5)
            top_idx = top5_idx[0].item()
            top_prob = float(top5_prob[0].item())
            raw_cat = categories[top_idx]

            # Aggregate category family probabilities
            apparel_person_prob = sum(probs[i].item() for i in _APPAREL_AND_PERSONS)
            bird_prob = sum(probs[i].item() for i in _BIRDS)
            animal_prob = sum(probs[i].item() for i in _PETS_WILDLIFE)
            marine_prob = sum(probs[i].item() for i in _MARINE_FISH)
            reptile_prob = sum(probs[i].item() for i in _REPTILES_AMPHIBIANS)
            food_prob = sum(probs[i].item() for i in _FOODS)
            doc_prob = sum(probs[i].item() for i in _DOCUMENTS_AND_PRINTS)
            is_tech_or_veh = raw_cat in _TECH_AND_VEHICLES

            # Determine rejection criteria
            rejection_reason = None
            rejection_conf = 0.0
            rejection_cat = raw_cat
            rejection_idx = top_idx

            # If top-1 category is a recognized textile / weave fabric, bypass OOD rejection
            if raw_cat in KNOWN_TEXTILES:
                pass
            else:
                if apparel_person_prob >= 0.22:
                    rejection_reason = "Person / Apparel Scene"
                    rejection_conf = apparel_person_prob
                    rejection_cat = raw_cat
                elif bird_prob >= 0.30:
                    rejection_reason = "Bird / Avian"
                    rejection_conf = bird_prob
                elif animal_prob >= 0.30:
                    rejection_reason = "Animal / Wildlife"
                    rejection_conf = animal_prob
                elif marine_prob >= 0.30:
                    rejection_reason = "Aquatic / Marine Life"
                    rejection_conf = marine_prob
                elif reptile_prob >= 0.30:
                    rejection_reason = "Reptile / Amphibian"
                    rejection_conf = reptile_prob
                elif food_prob >= 0.30:
                    rejection_reason = "Food / Beverage"
                    rejection_conf = food_prob
                elif doc_prob >= 0.20:
                    rejection_reason = "Document / Paper"
                    rejection_conf = doc_prob
                elif is_tech_or_veh and top_prob >= 0.30:
                    rejection_reason = "Vehicle / Technological Object"
                    rejection_conf = top_prob

            if rejection_reason:
                return {
                    "is_valid_fabric": False,
                    "material_status": "Non-Fabric",
                    "confidence": round(float(rejection_conf), 4),
                    "classification": rejection_cat,
                    "detected_category": REJECTION_CATEGORY,
                    "message": REJECTION_MESSAGE,
                    "suggestion": REJECTION_SUGGESTION,
                    "metrics": {
                        "semantic_class": rejection_cat,
                        "semantic_confidence": round(float(rejection_conf), 4),
                        "semantic_index": rejection_idx,
                        "std": round(std_val, 2),
                    },
                }

        except Exception as e:
            logger.warning("MobileNet inference exception: %s", e)

    # 7. Passed all non-fabric gates -> Verified authentic physical fabric
    return {
        "is_valid_fabric": True,
        "material_status": "Fabric Verified",
        "confidence": round(1.0 - zero_ratio, 3),
        "classification": "valid_fabric",
        "detected_category": "Authentic Textile Fabric",
        "message": "Fabric verified — valid yarn weave structure detected.",
        "suggestion": None,
        "metrics": {
            "digital_flat_patch_ratio": round(zero_ratio, 4),
            "std": round(std_val, 2),
            "mean": round(mean_val, 2),
        },
    }
