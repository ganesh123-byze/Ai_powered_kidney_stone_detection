"""
Kidney Ultrasound Classification - Image Preprocessing Service
OpenCV-based preprocessing for inference.
"""

import io
import os
from pathlib import Path
from typing import Tuple, Union, Optional, TYPE_CHECKING, Any, List

import cv2
import numpy as np
from PIL import Image
from loguru import logger


class UltrasoundGate:
    """One-class ultrasound-likeness gate.

    Purpose: reject obvious non-ultrasound images (flowers/dogs/etc.) before the
    stone detector runs, since the stone classifier will otherwise force every
    image into {Normal, Stone}.

    Implementation:
    - Build a reference grayscale histogram distribution from known ultrasound
      images in reference directories.
    - For an input image, compute histogram distance + simple colorfulness
      heuristics.
    """

    _IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

    def __init__(
        self,
        enabled: bool = True,
        reference_dirs: Optional[List[Path]] = None,
        max_reference_images: int = 300,
        hist_bins: int = 256,
        reference_stats_path: Optional[Path] = None,
    ):
        self.enabled = enabled
        self.reference_dirs = reference_dirs or []
        self.max_reference_images = max_reference_images
        self.hist_bins = hist_bins
        self.reference_stats_path = reference_stats_path

        self._ref_hist_mean: Optional[np.ndarray] = None
        self._ref_dist_threshold: Optional[float] = None

        self._ref_feat_mean: Optional[np.ndarray] = None
        self._ref_feat_inv_cov: Optional[np.ndarray] = None
        self._ref_feat_threshold: Optional[float] = None
        self._built = False

    @staticmethod
    def _parse_reference_dirs(env_value: Optional[str]) -> List[Path]:
        if not env_value:
            return []
        parts = [p.strip() for p in env_value.split(",") if p.strip()]
        return [Path(p) for p in parts]

    @staticmethod
    def _repo_root() -> Path:
        # preprocessing.py -> backend/app/services/preprocessing.py
        # parents[0]=services, [1]=app, [2]=backend, [3]=repo root
        return Path(__file__).resolve().parents[3]

    @classmethod
    def _resolve_dirs(cls, dirs: List[Path]) -> List[Path]:
        repo_root = cls._repo_root()
        resolved: List[Path] = []
        for d in dirs:
            p = Path(d)
            if not p.is_absolute():
                p = (repo_root / p).resolve()
            resolved.append(p)
        return resolved

    @classmethod
    def from_env(cls) -> "UltrasoundGate":
        enabled = os.getenv("ULTRASOUND_GATE_ENABLED", "true").lower() in {"1", "true", "yes", "y"}

        # Allow explicit override from env; otherwise try common dataset locations.
        ref_dirs = cls._parse_reference_dirs(os.getenv("ULTRASOUND_REFERENCE_DIRS"))
        if not ref_dirs:
            ref_dirs = [
                Path("backend/data/Normal"),
                Path("backend/data/stone"),
                Path("data/Normal"),
                Path("data/stone"),
            ]

        ref_dirs = cls._resolve_dirs(ref_dirs)

        max_imgs = int(os.getenv("ULTRASOUND_REFERENCE_MAX_IMAGES", "300"))

        stats_path_env = os.getenv("ULTRASOUND_GATE_STATS_PATH")
        stats_path = Path(stats_path_env) if stats_path_env else (cls._repo_root() / "backend/app/assets/ultrasound_gate_ref.json")
        if not stats_path.is_absolute():
            stats_path = (cls._repo_root() / stats_path).resolve()

        return cls(
            enabled=enabled,
            reference_dirs=ref_dirs,
            max_reference_images=max_imgs,
            reference_stats_path=stats_path,
        )

    def _load_reference_stats(self) -> bool:
        path = self.reference_stats_path
        if not path:
            return False
        try:
            if not path.exists():
                return False
            import json

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            hist_mean = np.array(data["ref_hist_mean"], dtype=np.float32)
            self.hist_bins = int(data.get("hist_bins", int(hist_mean.shape[0])))
            self._ref_hist_mean = hist_mean
            self._ref_dist_threshold = float(data["ref_hist_threshold"])

            self._ref_feat_mean = np.array(data["ref_feat_mean"], dtype=np.float32)
            self._ref_feat_inv_cov = np.array(data["ref_feat_inv_cov"], dtype=np.float32)
            self._ref_feat_threshold = float(data["ref_feat_threshold"])

            logger.info(f"UltrasoundGate: loaded reference stats from {path}")
            return True
        except Exception as e:
            logger.warning(f"UltrasoundGate: failed to load reference stats ({path}): {e}")
            return False

    def _iter_reference_images(self) -> List[Path]:
        images: List[Path] = []
        for ref_dir in self.reference_dirs:
            if not ref_dir.exists() or not ref_dir.is_dir():
                continue
            for p in ref_dir.rglob("*"):
                if p.is_file() and p.suffix.lower() in self._IMAGE_EXTS:
                    images.append(p)
                    if len(images) >= self.max_reference_images:
                        return images
        return images

    def _gray_hist(self, bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [self.hist_bins], [0, 256]).reshape(-1)
        hist_sum = float(hist.sum())
        if hist_sum <= 0:
            return np.ones((self.hist_bins,), dtype=np.float32) / self.hist_bins
        return (hist / hist_sum).astype(np.float32)

    @staticmethod
    def _chi_square_distance(a: np.ndarray, b: np.ndarray) -> float:
        eps = 1e-8
        num = (a - b) ** 2
        den = a + b + eps
        return float(0.5 * np.sum(num / den))

    @staticmethod
    def _colorfulness_scores(bgr: np.ndarray) -> Tuple[float, float]:
        """Return (channel_diff, mean_saturation) in [0,1] approx."""
        b = bgr[:, :, 0].astype(np.float32)
        g = bgr[:, :, 1].astype(np.float32)
        r = bgr[:, :, 2].astype(np.float32)
        channel_diff = float((np.mean(np.abs(r - g)) + np.mean(np.abs(r - b)) + np.mean(np.abs(g - b))) / (3.0 * 255.0))

        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        s = hsv[:, :, 1].astype(np.float32) / 255.0
        mean_saturation = float(np.mean(s))
        return channel_diff, mean_saturation

    def build_reference(self) -> None:
        if self._built or not self.enabled:
            self._built = True
            return

        ref_images = self._iter_reference_images()
        if not ref_images:
            if self._load_reference_stats():
                self._built = True
                return

            logger.warning(
                "UltrasoundGate: no reference images found; using heuristic-only gating. "
                f"Set ULTRASOUND_REFERENCE_DIRS or provide {self.reference_stats_path}. tried={self.reference_dirs}"
            )
            self._built = True
            return

        hists: List[np.ndarray] = []
        feats: List[np.ndarray] = []
        for p in ref_images:
            img = cv2.imread(str(p))
            if img is None:
                continue
            hists.append(self._gray_hist(img))
            feats.append(self._features(img))

        if len(hists) < 10:
            logger.warning("UltrasoundGate: too few reference images; using heuristic-only gating")
            self._built = True
            return

        ref_hist_mean = np.mean(np.stack(hists, axis=0), axis=0).astype(np.float32)

        # Distance distribution among reference ultrasound images.
        dists = [self._chi_square_distance(h, ref_hist_mean) for h in hists]
        # Conservative threshold: 99th percentile + small margin.
        thresh = float(np.percentile(np.array(dists, dtype=np.float32), 99.0) + 0.02)

        self._ref_hist_mean = ref_hist_mean
        self._ref_dist_threshold = thresh

        # Fit a simple one-class model in feature space (Mahalanobis distance)
        X = np.stack(feats, axis=0).astype(np.float32)
        mu = np.mean(X, axis=0)
        cov = np.cov(X, rowvar=False).astype(np.float32)
        # Regularize for numerical stability
        cov = cov + (np.eye(cov.shape[0], dtype=np.float32) * 1e-3)
        try:
            inv_cov = np.linalg.inv(cov).astype(np.float32)
        except Exception:
            inv_cov = np.linalg.pinv(cov).astype(np.float32)

        mdists = [self._mahalanobis(x, mu, inv_cov) for x in X]
        fthresh = float(np.percentile(np.array(mdists, dtype=np.float32), 99.5) + 0.5)

        self._ref_feat_mean = mu.astype(np.float32)
        self._ref_feat_inv_cov = inv_cov
        self._ref_feat_threshold = fthresh
        self._built = True

        logger.info(
            f"UltrasoundGate built: n_ref={len(hists)}, hist_th={self._ref_dist_threshold:.4f}, feat_th={self._ref_feat_threshold:.2f}"
        )

    @staticmethod
    def _entropy(gray: np.ndarray, bins: int = 256) -> float:
        hist = cv2.calcHist([gray], [0], None, [bins], [0, 256]).reshape(-1).astype(np.float32)
        s = float(hist.sum())
        if s <= 0:
            return 0.0
        p = hist / s
        eps = 1e-8
        ent = float(-np.sum(p * np.log(p + eps)))
        return ent / float(np.log(bins))

    def _features(self, bgr: np.ndarray) -> np.ndarray:
        # Compute cheap features that separate ultrasound scans from natural photos.
        img = cv2.resize(bgr, (256, 256), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        channel_diff, mean_saturation = self._colorfulness_scores(img)
        black_ratio = float(np.mean(gray < 20))

        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.mean(edges > 0))

        lap = cv2.Laplacian(gray, cv2.CV_32F)
        lap_var = float(np.var(lap) / (255.0 * 255.0))

        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        high = cv2.absdiff(gray, blur)
        speckle = float(np.mean(high) / 255.0)

        ent = self._entropy(gray)

        return np.array(
            [
                mean_saturation,
                channel_diff,
                black_ratio,
                edge_density,
                lap_var,
                speckle,
                ent,
            ],
            dtype=np.float32,
        )

    @staticmethod
    def _mahalanobis(x: np.ndarray, mu: np.ndarray, inv_cov: np.ndarray) -> float:
        d = (x - mu).astype(np.float32)
        return float(d.T @ inv_cov @ d)

    def is_ultrasound(self, bgr: np.ndarray) -> bool:
        if not self.enabled:
            return True
        if not self._built:
            self.build_reference()

        # Always reject strong color photos.
        channel_diff, mean_saturation = self._colorfulness_scores(bgr)
        if mean_saturation >= 0.55 and channel_diff >= 0.16:
            return False

        # If reference model isn't available, we can only do weak checks.
        if self._ref_hist_mean is None or self._ref_dist_threshold is None:
            return mean_saturation < 0.60

        # Histogram check (grayscale distribution)
        h = self._gray_hist(bgr)
        hist_dist = self._chi_square_distance(h, self._ref_hist_mean)
        if hist_dist > (self._ref_dist_threshold * 6.0):
            return False

        # Feature-space one-class check
        if self._ref_feat_mean is not None and self._ref_feat_inv_cov is not None and self._ref_feat_threshold is not None:
            x = self._features(bgr)
            md = self._mahalanobis(x, self._ref_feat_mean, self._ref_feat_inv_cov)
            if md > self._ref_feat_threshold:
                return False

        return True


class ImagePreprocessor:
    """
    Image preprocessing service for kidney ultrasound images.
    Uses OpenCV for efficient image processing.
    """
    
    # ImageNet normalization values
    IMAGENET_MEAN = [0.485, 0.456, 0.406]
    IMAGENET_STD = [0.229, 0.224, 0.225]
    
    def __init__(
        self,
        image_size: int = 224,
        use_clahe: bool = True,
        clahe_clip_limit: float = 2.0,
        clahe_grid_size: Tuple[int, int] = (8, 8)
    ):
        """
        Initialize the preprocessor.
        
        Args:
            image_size: Target image size (square)
            use_clahe: Whether to apply CLAHE enhancement
            clahe_clip_limit: CLAHE clip limit
            clahe_grid_size: CLAHE grid size
        """
        self.image_size = image_size
        self.use_clahe = use_clahe
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_grid_size = clahe_grid_size
        
        # Create CLAHE object
        if use_clahe:
            self.clahe = cv2.createCLAHE(
                clipLimit=clahe_clip_limit,
                tileGridSize=clahe_grid_size
            )

        self.ultrasound_gate = UltrasoundGate.from_env()
        # Build lazily on first request; but attempt build at startup to log threshold early.
        try:
            self.ultrasound_gate.build_reference()
        except Exception as e:
            logger.warning(f"UltrasoundGate init failed (will fallback to heuristic-only): {e}")
        
        logger.info(f"ImagePreprocessor initialized (size={image_size}, clahe={use_clahe})")
    
    def load_image(
        self,
        source: Union[str, Path, bytes, np.ndarray, Image.Image]
    ) -> np.ndarray:
        """
        Load image from various sources.
        
        Args:
            source: Image path, bytes, numpy array, or PIL Image
        
        Returns:
            Image as BGR numpy array (OpenCV format)
        """
        if isinstance(source, (str, Path)):
            image = cv2.imread(str(source))
            if image is None:
                raise ValueError(f"Failed to load image from: {source}")
        
        elif isinstance(source, bytes):
            nparr = np.frombuffer(source, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Failed to decode image from bytes")
        
        elif isinstance(source, np.ndarray):
            if len(source.shape) == 2:
                image = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
            elif source.shape[2] == 4:
                image = cv2.cvtColor(source, cv2.COLOR_RGBA2BGR)
            elif source.shape[2] == 3:
                image = source.copy()
            else:
                raise ValueError(f"Unexpected image shape: {source.shape}")
        
        elif isinstance(source, Image.Image):
            image = np.array(source.convert('RGB'))
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        else:
            raise TypeError(f"Unsupported image source type: {type(source)}")
        
        return image
    
    def apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE enhancement."""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = self.clahe.apply(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def preprocess(
        self,
        source: Union[str, Path, bytes, np.ndarray, Image.Image],
        return_original: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Preprocess image for model inference.
        Returns a normalized numpy array (C, H, W) for ONNX Runtime.
        """
        # Load image
        image = self.load_image(source)
        
        # Apply CLAHE if enabled
        if self.use_clahe:
            image = self.apply_clahe(image)
        
        # Resize
        image = cv2.resize(image, (self.image_size, self.image_size))
        
        # Keep original for visualization if needed
        original = image.copy() if return_original else None
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert to float32 and normalize to [0, 1]
        image = image.astype(np.float32) / 255.0
        
        # Normalize with ImageNet values: (img - mean) / std
        for i in range(3):
            image[:, :, i] = (image[:, :, i] - self.IMAGENET_MEAN[i]) / self.IMAGENET_STD[i]
        
        # Transpose (H, W, C) -> (C, H, W) for ONNX Runtime
        tensor = image.transpose(2, 0, 1)
        
        if return_original:
            return tensor, original
        return tensor
    
    def validate_image(
        self,
        source: Union[str, Path, bytes, np.ndarray, Image.Image]
    ) -> Tuple[bool, Optional[str]]:
        """Validate if image can be processed."""
        try:
            image = self.load_image(source)
            if image.shape[0] < 10 or image.shape[1] < 10:
                return False, "Image is too small (minimum 10x10 pixels)"
            return True, None
        except Exception as e:
            return False, str(e)

    def validate_ultrasound(
        self,
        source: Union[str, Path, bytes, np.ndarray, Image.Image]
    ) -> Tuple[bool, Optional[str]]:
        """Return (is_ultrasound, error_message_if_not).

        Message is intentionally user-facing.
        """
        try:
            image = self.load_image(source)
            if not self.ultrasound_gate.is_ultrasound(image):
                return False, "Please upload ultrasound image"
            return True, None
        except Exception as e:
            # Fail-open here to avoid blocking real ultrasounds due to gate issues.
            # Invalid images are already caught by validate_image().
            if os.getenv("DEBUG", "false").lower() == "true":
                return False, str(e)
            return True, None


# Global instance
_preprocessor: Optional[ImagePreprocessor] = None


def get_preprocessor(
    image_size: int = 224,
    use_clahe: bool = True
) -> ImagePreprocessor:
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = ImagePreprocessor(image_size=image_size, use_clahe=use_clahe)
    return _preprocessor
