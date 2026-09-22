from typing import Protocol, Optional
import numpy as np
from shapely.geometry import Polygon

class FieldDetectorProtocol(Protocol):
    def extract_mask(self, frame: np.ndarray) -> np.ndarray:
        """Extract a mask representing the field from the given frame."""
        ...
        
    def derive_polygon(self, mask: np.ndarray) -> Optional[Polygon]:
        """Derive a Shapely Polygon from the given mask."""
        ...
