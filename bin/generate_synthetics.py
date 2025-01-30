#!/usr/bin/env python

import sys
import yaml
from pathlib import Path
from synthgen import __version__
from synthgen.synthetics_generator_class import Synthetics_generator


def read_configuration_file(config_path, check_version=True):
    """
    Reads a YAML configuration file and returns its content with optional
    version checking against the current module version.

    Args:
        config_path (str or Path): Path to the YAML configuration file.
        check_version (bool, optional): If True, checks if the file's version
        matches the expected version.

    Returns:
        RecursiveAttributeDict: A dictionary-like object with configuration
        parameters accessible as attributes.

    Raises:
        ValueError: If `check_version` is True and the version does not match.
    """

    with open(str(config_path), 'r') as yaml_file:
        configs = yaml.load(yaml_file, Loader=yaml.FullLoader)

    if check_version:
        # Check if the version in the file matches the required version
        file_version = configs.get('version', None)
        if file_version is None:
            raise ValueError("`version` field not found in the configuration file!")
        elif file_version != __version__:
            raise ValueError(
                "Configuration file version %r doesn't match the current "
                "SYNTHGEN version (%r)" % (file_version, __version__))
    return configs


def main(config_file):
    # 1. Read YAML config
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    inputs = config["inputs"]
    inv_filename = config["inv_filename"]
    data_dir = config["data_dir"]
    gfstore_dir = config["gfstore_dir"]
    gf_store = config["gf_store"]
    time_window = config["time_window"]
    buffer = config["buffer"]
    resampling_freq = config["resampling_freq"]
    highcut_freq = config["highcut_freq"]
    event_type = config["event_type"]
    source_type = config["source_type"]
    data_id = config["data_id"]
    parallel = config["parallel"]
    catname = config["catname"]

    dataset = Synthetics_generator(
                data_dir, inv_filename, gfstore_dir, gf_store, data_id)
    dataset.generate_catalogue(inputs, catname, event_type)
    dataset.generate_waveforms(dataset.events,
                               time_window,
                               buffer,
                               resampling_freq,
                               highcut_freq,
                               source_type,
                               parallel)


if __name__ == "__main__":
    # Expect a config filename as the first argument
    if len(sys.argv) < 2:
        print("USAGE: %s CONFIG.yml" % Path(sys.argv[0]).name)
        sys.exit(1)

    CONFIG = read_configuration_file(sys.argv[1], check_version=True)
    main(CONFIG)
