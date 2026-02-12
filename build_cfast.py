#!/usr/bin/env python
"""Build the optional Cython extension for openskill.

Usage:
    python build_cfast.py

The compiled ``_cfast`` module is placed directly into the
``openskill/`` package directory so that ``from openskill._cfast
import cy_rate_game`` works without installation.
"""

import os
import sys

def build() -> bool:
    try:
        from Cython.Build import cythonize
        from setuptools import Distribution, Extension
        from setuptools.command.build_ext import build_ext
    except ImportError as exc:
        print(f"Build dependency missing: {exc}", file=sys.stderr)
        print("Install with:  pip install cython setuptools", file=sys.stderr)
        return False

    src = os.path.join("openskill", "_cfast.pyx")
    if not os.path.isfile(src):
        print(f"Source not found: {src}", file=sys.stderr)
        return False

    extensions = cythonize(
        [Extension("openskill._cfast", [src])],
        compiler_directives={
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
            "language_level": "3",
        },
    )

    dist = Distribution({"ext_modules": extensions})
    dist.parse_config_files()

    cmd = build_ext(dist)
    cmd.inplace = True
    cmd.ensure_finalized()
    cmd.run()

    print("\nBuild successful.  Verify with:")
    print("  python -c \"from openskill._cfast import cy_rate_game; print('OK')\"")
    return True


if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
