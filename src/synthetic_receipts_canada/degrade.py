"""Turn a clean print into something like a phone photo of a real thermal receipt.

Each step is parameterised from the seeded RNG and the chosen parameters are returned with the
image, so a ground-truth file can say exactly how hard its degraded copy is. Steps, in order:
paper tint, ink fade with a gradient (thermal print fades toward the tear-off edge), low-frequency
shading (uneven lighting), a fold, blur, rotation, a mild perspective warp, sensor noise, then
JPEG recompression as a phone camera would do.
"""

import random
from dataclasses import asdict, dataclass

import numpy as np
from PIL import Image, ImageFilter


@dataclass
class Degradation:
    paper_gray: int  # 0..255 brightness of the paper
    ink_gray_top: int  # darkest ink level at the top of the receipt
    ink_gray_bottom: int  # ink level at the bottom (higher = more faded)
    shading_amplitude: float  # 0..1 strength of the low-frequency lighting variation
    fold_position: float | None  # 0..1 fraction of height, None = no fold
    blur_radius: float
    rotation_degrees: float
    perspective: float  # 0..1 strength of the corner jitter
    noise_sigma: float
    salt_pepper_fraction: float
    jpeg_quality: int

    def to_dict(self) -> dict:
        return asdict(self)


def sample_degradation(rng: random.Random, severity: str = "mixed") -> Degradation:
    """`severity`: 'light' (crisp receipt, careful photo), 'heavy' (faded, sloppy) or 'mixed'."""
    if severity == "mixed":
        severity = rng.choice(["light", "medium", "heavy"])
    level = {"light": 0.0, "medium": 0.5, "heavy": 1.0}[severity]
    jitter = lambda lo, hi: lo + (hi - lo) * min(1.0, max(0.0, level + rng.uniform(-0.25, 0.25)))
    return Degradation(
        paper_gray=int(jitter(245, 205)),
        ink_gray_top=int(jitter(20, 70)),
        ink_gray_bottom=int(jitter(40, 170)),
        shading_amplitude=jitter(0.05, 0.35),
        fold_position=rng.uniform(0.3, 0.8) if rng.random() < level * 0.8 else None,
        blur_radius=jitter(0.0, 1.6),
        rotation_degrees=rng.uniform(-1, 1) * jitter(0.5, 5.0),
        perspective=jitter(0.0, 0.06),
        noise_sigma=jitter(2.0, 12.0),
        salt_pepper_fraction=jitter(0.0, 0.004),
        jpeg_quality=int(jitter(92, 55)),
    )


def apply(clean: Image.Image, params: Degradation, rng: random.Random) -> Image.Image:
    arr = np.asarray(clean.convert("L"), dtype=np.float32) / 255.0  # 1 = paper, 0 = ink
    h, w = arr.shape
    ink = 1.0 - arr

    # Ink fade: the darkest level drifts from top to bottom.
    rows = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    ink_level = (params.ink_gray_top + (params.ink_gray_bottom - params.ink_gray_top) * rows) / 255.0
    paper = params.paper_gray / 255.0
    img = paper * (1.0 - ink) + ink_level * ink

    # Low-frequency shading: a couple of smooth sinusoids across the sheet.
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    phase_x, phase_y = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
    shade = 1.0 - params.shading_amplitude * (
        0.5 + 0.5 * np.sin(xx / w * 3.1 + phase_x) * np.cos(yy / h * 2.2 + phase_y)
    )
    img *= shade

    if params.fold_position is not None:
        fy = int(params.fold_position * h)
        band = np.exp(-((yy - fy) ** 2) / (2 * 6.0**2))
        img = img * (1.0 - 0.25 * band) + 0.08 * np.roll(band, 8, axis=0) * paper

    out = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8), "L")
    if params.blur_radius > 0.05:
        out = out.filter(ImageFilter.GaussianBlur(params.blur_radius))

    # Rotate and warp on a background that looks like the table under the receipt.
    background = int(params.paper_gray * rng.uniform(0.35, 0.7))
    out = out.rotate(params.rotation_degrees, resample=Image.BICUBIC, expand=True, fillcolor=background)
    if params.perspective > 0.001:
        W, H = out.size
        j = lambda: rng.uniform(-params.perspective, params.perspective)
        quad = (
            j() * W, j() * H,
            j() * W, H + j() * H,
            W + j() * W, H + j() * H,
            W + j() * W, j() * H,
        )
        out = out.transform((W, H), Image.QUAD, quad, resample=Image.BICUBIC, fillcolor=background)

    arr = np.asarray(out, dtype=np.float32)
    arr += np.random.default_rng(rng.getrandbits(32)).normal(0.0, params.noise_sigma, arr.shape)
    if params.salt_pepper_fraction > 0:
        mask = np.random.default_rng(rng.getrandbits(32)).random(arr.shape)
        arr[mask < params.salt_pepper_fraction / 2] = 0
        arr[mask > 1 - params.salt_pepper_fraction / 2] = 255
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")
