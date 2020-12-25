import json
import os
import shutil
import sys
import click

# App Details
APP_NAME = "Debian Control File Builder"
APP_AUTHOR = "Nightwind Developments"

# Important Constants
PREFIX_ARGS = "--"
RAW_ARGS = "config"
OUTPUT_ARG = "output"


# Makes a new directory if it does not exist
def mkdir_if_not_exist(path):
    if not os.path.exists(path):
        os.mkdir(path)


# Mandatory Keys Not Found Error/Exception
class MandatoryKeyNotFoundError(Exception):

    def __init__(self, missing_keys, is_json):
        self.missing_keys = missing_keys
        if is_json:
            self.message = "[In JSON File]"
        else:
            self.message = "[In Parameters]"
        self.message += " The Following Keys were missing: " + str(self.missing_keys)
        super().__init__(self.message)


class InvalidParameters(Exception):

    def __init__(self):
        self.message = "Uneven amount of parameters. Perhaps you missed an argument or value"
        super().__init__(self.message)


# Debian Control Class
class DebControl:

    # Argument Parameter Keys
    CONFIG_FILE_ARG = "file"
    DEP_FILE_ARG = "deps_file"

    # File Names
    CTRL_FILE_NAME = "Control"

    # Default Paths
    OUTPUT_DEFAULT = "output/"

    # Keywords
    DEPENDS_KEYWORD = "Depends"

    # Commonly Used Syntax within File
    COLON = ": "
    COMMA = ", "

    # Constant Data Keys
    MK_PACKAGE = 0
    MK_VERSION = 1
    MK_ARCH = 2
    MK_MAINTAIN = 3
    MK_DESCRIPTION = 4
    MANDATORY_KEYS = ["Package", "Version", "Architecture", "Maintainer", "Description"]
    OTHER_DATA_KEYS = list()

    # Class Constructor
    def __init__(self, **named_args):

        is_config_file = self.CONFIG_FILE_ARG in named_args

        # JSON Configuration File Case
        if is_config_file:
            json_file = open(named_args[self.CONFIG_FILE_ARG])
            temp_dict = json.load(json_file)
            temp_dict_keys = temp_dict.keys()
        # Parameters Case
        else:
            temp_dict_keys = named_args.keys()
            temp_dict = named_args

        # Ensures Imported List Contains at minimum the Mandatory Keys
        mk_not_found = list()
        for mk in self.MANDATORY_KEYS:
            if mk not in temp_dict_keys:
                mk_not_found.append(mk)
        if mk_not_found:
            raise MandatoryKeyNotFoundError(mk_not_found, bool(is_config_file))

        # Saves Configuration Data
        self.data = temp_dict

        # Initialises Dependencies List
        self.dependencies = list()

        # Saves Non-Mandatory Keys
        self.OTHER_DATA_KEYS = [x for x in self.data.keys() if x not in self.MANDATORY_KEYS]

    def generate_line_from_data(self, key):
        return str(key + self.COLON + self.data[key] + "\n")

    # Parses Dependency File to Save Dependencies
    def parse_deps_file(self, deps_list_file_path):
        try:
            with open(deps_list_file_path) as deps_file:
                dep_entry = deps_file.readline().rstrip()
                while dep_entry:
                    self.dependencies.append(dep_entry)
                    dep_entry = deps_file.readline().rstrip()
        except IOError:
            print("Dependency File not found")
            exit(-2)

    # Builds Debian Control File
    def build_control_file(self, output_path=OUTPUT_DEFAULT):
        mkdir_if_not_exist(output_path)
        output_path_full = output_path + self.CTRL_FILE_NAME
        build_file = open(output_path_full, "w")

        # Writes Mandatory Configurations First
        for i in self.MANDATORY_KEYS:
            build_file.write(self.generate_line_from_data(i))

        # Writes Required Dependencies
        if self.dependencies:
            deps_line = self.COMMA.join(self.dependencies)
            deps_line_full = self.DEPENDS_KEYWORD + self.COLON + deps_line
            build_file.write(deps_line_full)

        # Writes Other Configurations Last
        for i in self.OTHER_DATA_KEYS:
            build_file.write(self.generate_line_from_data(i))


# Main Function to Run on Start
@click.command()
@click.option('-f', PREFIX_ARGS + DebControl.CONFIG_FILE_ARG, type=click.Path(exists=True, file_okay=True))
@click.option('-df', PREFIX_ARGS + DebControl.DEP_FILE_ARG, type=click.Path(exists=True, file_okay=True))
@click.option('-c', PREFIX_ARGS + RAW_ARGS, type=(str, str), multiple=True)
@click.option('-o', PREFIX_ARGS + OUTPUT_ARG, type=click.Path(), default=DebControl.OUTPUT_DEFAULT)
def main(file, config, deps_file, output):
    print("'{}' by {}".format(APP_NAME, APP_AUTHOR))
    if file:
        gen = DebControl(file=file)
    elif config:
        print("Configuration Data from Inputted Arguments:")
        temp_dict = dict()
        for pair in config:
            key = pair[0]
            content = pair[1]
            temp_dict[key] = content
            print("\t* " + key + ": " + content)
        gen = DebControl(**temp_dict)
    else:
        gen = None
        print("Error: Required Parameters not filled")
        print("Program exiting...")
        sys.exit("Error: Required Parameters not filled.")

    if deps_file:
        gen.parse_deps_file(deps_file)

    gen.build_control_file()


# Ensures Main Function is to be run first
if __name__ == "__main__":
    main()
