# WSGI Entry Point
import os
from app import create_app, db

# Apply patches if necessary (copied from run.py)
import numpy as np
try:
    if not hasattr(np, 'object'):
        np.object = object
    if not hasattr(np, 'bool'):
        np.bool = bool
    if not hasattr(np, 'int'):
        np.int = int
    if not hasattr(np, 'float'):
        np.float = float
    if not hasattr(np, 'typeDict'):
        np.typeDict = np.sctypeDict
except Exception as e:
    print(f"NumPy Patch Error: {e}")

app = create_app()

if __name__ == "__main__":
    app.run()
