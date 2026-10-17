"""`synthetic-receipts-canada generate --family restaurant_websrm --count 100 --seed 1 --out corpus`."""

import argparse
import json
import random
from pathlib import Path

from . import degrade, render
from .families import FAMILIES


def generate(args: argparse.Namespace) -> None:
    families = list(FAMILIES) if args.family == "all" else [args.family]
    for family in families:
        module = FAMILIES[family]
        out_dir = Path(args.out) / family
        out_dir.mkdir(parents=True, exist_ok=True)
        for index in range(1, args.count + 1):
            # One RNG per receipt, seeded from (seed, family, index): regenerating a single
            # receipt or adding more never changes the ones already produced.
            rng = random.Random(f"{args.seed}/{family}/{index}")
            receipt, truth = module.generate(rng, paper_mm=args.paper)
            clean = render.render(receipt, paper_mm=args.paper, font_family=args.font)
            stem = out_dir / f"{index:04d}"
            clean.save(stem.with_suffix(".png"), optimize=True)
            truth["files"] = {"clean": stem.with_suffix(".png").name}
            if not args.no_degrade:
                params = degrade.sample_degradation(rng, args.severity)
                photo = degrade.apply(clean, params, rng)
                photo.save(stem.with_suffix(".jpg"), quality=params.jpeg_quality)
                truth["files"]["degraded"] = stem.with_suffix(".jpg").name
                truth["degradation"] = params.to_dict()
            stem.with_suffix(".json").write_text(json.dumps(truth, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{family}: {args.count} receipts -> {out_dir}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="synthetic-receipts-canada")
    sub = parser.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate", help="render receipts, their degraded photos and ground truth")
    g.add_argument("--family", default="all", choices=["all", *FAMILIES])
    g.add_argument("--count", type=int, default=10)
    g.add_argument("--seed", default="1")
    g.add_argument("--out", default="corpus")
    g.add_argument("--paper", type=int, default=80, choices=[58, 80], help="paper width in mm")
    g.add_argument("--severity", default="mixed", choices=["light", "medium", "heavy", "mixed"])
    g.add_argument("--font", default=None, help="substring of a monospace TTF path to prefer (e.g. cour, Noto)")
    g.add_argument("--no-degrade", action="store_true")
    g.set_defaults(func=generate)
    args = parser.parse_args(argv)
    args.func(args)
