import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

print("1. Testing Imports...")
try:
    from deepface import DeepFace
    print("   DeepFace imported successfully.")
except Exception as e:
    print(f"   FATAL: DeepFace import failed: {e}")
    sys.exit(1)

try:
    import app.utils
    print("   app.utils imported successfully.")
except ImportError as e:
    print(f"   FATAL: app.utils import failed: {e}")
    # Continue to see other errors
except Exception as e:
    print(f"   FATAL: app.utils crashed: {e}")

print("\n2. Testing DeepFace Model Load (this might take time)...")
try:
    # Use a dummy image (black 100x100)
    import numpy as np
    import cv2
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    print("   Checking VGG-Face...")
    # This triggers build_model
    DeepFace.build_model("VGG-Face")
    print("   VGG-Face Model loaded successfully.")
except Exception as e:
    print(f"   FATAL: DeepFace Model failed: {e}")
    
print("\nDone.")
