import os

from setuptools import setup

USE_MYPYC = os.getenv("USE_MYPYC", "0") == "1"

# Attempt to import MyPyC
if USE_MYPYC:
    from mypyc.build import mypycify

    # Generate Extension List
    extensions = mypycify(
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
else:
    extensions = []

# Compile C Extensions using MyPyC
setup(
    ext_modules=extensions,
)
