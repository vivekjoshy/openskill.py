import os

from setuptools import setup

extensions = []

USE_MYPYC = os.getenv("USE_MYPYC", "0") == "1"

# MyPyC compiled extensions (opt-in via USE_MYPYC=1)
if USE_MYPYC:
    from mypyc.build import mypycify

    extensions.extend(
        mypycify(
            [
                "openskill/models/weng_lin/bradley_terry_full.py",
                "openskill/models/weng_lin/bradley_terry_part.py",
                "openskill/models/weng_lin/plackett_luce.py",
                "openskill/models/weng_lin/thurstone_mosteller_full.py",
                "openskill/models/weng_lin/thurstone_mosteller_part.py",
                "openskill/models/weng_lin/common.py",
                "openskill/models/common.py",
            ]
        )
    )

# Cython fast-path extension (auto-built when Cython is available)
try:
    from Cython.Build import cythonize

    pyx_path = os.path.join("openskill", "_cfast.pyx")
    if os.path.isfile(pyx_path):
        extensions.extend(
            cythonize(
                [pyx_path],
                compiler_directives={
                    "boundscheck": False,
                    "wraparound": False,
                    "cdivision": True,
                    "language_level": "3",
                },
            )
        )
except ImportError:
    pass

setup(
    ext_modules=extensions,
)
