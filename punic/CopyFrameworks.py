__author__ = 'schwa'

import os
import subprocess
import re
import shutil

def main():

    valid_architectures = set(os.environ["VALID_ARCHS"].split(" "))
    input_file_count = int(os.environ["SCRIPT_INPUT_FILE_COUNT"])
    input_files = [os.environ["SCRIPT_INPUT_FILE_{}".format(index)] for index in range(0, input_file_count )]
    expanded_identity = os.environ["EXPANDED_CODE_SIGN_IDENTITY_NAME"]
    built_products_dir = os.environ["BUILT_PRODUCTS_DIR"]
    frameworks_folder_path = os.environ["FRAMEWORKS_FOLDER_PATH"]
    frameworks_path = os.path.join(built_products_dir, frameworks_folder_path)
    code_signing_allowed = os.environ["CODE_SIGNING_ALLOWED"] == "YES"

    for input_path in input_files:
        # We don't modify the input frameworks but rather the ones in the built products directory
        output_path = os.path.join(frameworks_path, os.path.split(input_path)[1])

        framework_name = os.path.splitext(os.path.split(input_path)[1])[0]

        print "# Copying framework {}".format(framework_name)

        if os.path.exists(output_path):
            shutil.rmtree(output_path)

        shutil.copytree(input_path, output_path)

        framework_path = output_path

        if not code_signing_allowed:
            continue

        binary_path = os.path.join(framework_path, framework_name)


        # Find out what architectures the framework has
        output = subprocess.check_output(["/usr/bin/xcrun", "lipo", "-info", binary_path])
        match = re.match(r"^Architectures in the fat file: (.+) are: (.+)".format(binary_path), output)
        assert(match.groups()[0] == binary_path)
        architectures = set(match.groups()[1].strip().split(" "))

        # Produce a list of architectures that are not valid
        excluded_architectures = architectures.difference(valid_architectures)



        # Skip if all architectures are valid
        if not excluded_architectures:
            continue





        # For each invalid architecture strip it from framework
        for architecture in excluded_architectures:
            print "# Stripping {} from {}".format(architecture, framework_name)
            output = subprocess.check_output(["/usr/bin/xcrun", "lipo", "-remove", architecture, "-output", binary_path, binary_path])
            print output

        # Resign framework
        print "# Resigning {} with {}".format(framework_name, expanded_identity)
        result = subprocess.check_call(["/usr/bin/xcrun", "codesign", "--force", "--sign", expanded_identity, "--preserve-metadata=identifier,entitlements", binary_path])

if __name__ == "__main__":
    main()