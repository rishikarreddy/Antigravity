import os
import base64
from deepface import DeepFace
from flask import current_app

import traceback

def save_base64_image(data_url, student_id):
    """Decodes and saves a base64 image."""
    try:
        header, encoded = data_url.split(",", 1)
        data = base64.b64decode(encoded)
        
        filename = f"student_{student_id}_face.jpg"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(data)
            
        print(f"DEBUG: Saved image to {filepath}")
        return filepath
    except Exception as e:
        print(f"Image Save Error: {e}")
        traceback.print_exc()
        return None

def generate_embedding(image_path):
    """Generates 2622-dim embedding using VGG-Face via DeepFace."""
    try:
        print(f"DEBUG: Generating embedding for {image_path}")
        # returns list of dicts. We take the first face.
        # returns list of dicts. We take the first face.
        # enforce_detection=True ensures we don't register bad data.
        
        objs = None
        
        # 1. Try RetinaFace (Best for Profile/Side Faces)
        try:
            print("DEBUG: Attempting detection with RetinaFace...")
            objs = DeepFace.represent(
                img_path=image_path, 
                model_name="VGG-Face", 
                detector_backend="retinaface",
                enforce_detection=True,
                align=True
            )
        except Exception as e_retina:
            print(f"WARNING: RetinaFace failed ({e_retina}). Falling back to SSD.")
            
            # 2. Try SSD (Fast, Robust)
            try:
                print("DEBUG: Attempting detection with SSD...")
                objs = DeepFace.represent(
                    img_path=image_path, 
                    model_name="VGG-Face", 
                    detector_backend="ssd",
                    enforce_detection=True,
                    align=True
                )
            except Exception as e_ssd:
                print(f"WARNING: SSD failed ({e_ssd}). Falling back to OpenCV.")
                
                # 3. Try OpenCV (Basic, Fails on side faces, but works)
                objs = DeepFace.represent(
                    img_path=image_path, 
                    model_name="VGG-Face", 
                    detector_backend="opencv",
                    enforce_detection=True,
                    align=True
                )

        if objs:
            embedding = objs[0]["embedding"]
            # Ensure it is a list of floats (not numpy array)
            if hasattr(embedding, "tolist"):
                embedding = embedding.tolist()
            return embedding
            
    except Exception as e:
        print(f"DeepFace Embedding Error: {e}")
        traceback.print_exc()
    return None
