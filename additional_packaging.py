# Copy files located in test_files to the output directory for testing
import shutil
import os
import sys

src = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_files")
dest = os.path.join(os.path.dirname(os.path.realpath(__file__)), "output", "TA-MS-AAD")

def additional_packaging(ta_name=None):
    include_tests = os.getenv("INCLUDE_TESTS")
    if((include_tests is not None) and (include_tests.lower() == "true")):
        shutil.copytree(src, dest, dirs_exist_ok=True)

if __name__ == "__main__":
    additional_packaging()