#
# Copyright (C) 2025 StatiXOS
# SPDX-License-Identifier: Apache-2.0
#

#!/usr/bin/env python3

import os
import subprocess
import re
import sys
import argparse
from multiprocessing import Pool, cpu_count

# --- Partition Mapping ---
PARTITION_MAPPING = {
    "vendor": ["vendor"],
    "odm": ["odm"],
    "system_ext": ["system_ext"],
    "system": ["system"],
    "product": ["product"],
    "vendor_boot": ["vendor_boot"],
    "init_boot": ["init_boot"],
    "dtbo": ["dtbo"]
}

# --- Helper Functions ---

def find_file_in_aosp(module_name_and_aosp_root, verbose=False):
    """
    Uses mgrep to find if ANY file with the given name (without extension) exists in AOSP.
    Returns True if found, False otherwise.
    """
    module_name, aosp_root = module_name_and_aosp_root  # Unpack arguments

    # Search using mgrep (case-insensitive)
    mgrep_command = ["mgrep", "-i", "-r", module_name]
    try:
        mgrep_result = subprocess.run(mgrep_command, capture_output=True, text=True, check=False, cwd=aosp_root)
        if mgrep_result.returncode == 0:
            if verbose:
                print(f"Found {module_name} in AOSP using mgrep")
            return True
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"Error running mgrep: {e}")
        return False
    except FileNotFoundError:
        if verbose:
            print("Error: mgrep not found. Make sure it is available in your environment.")
        return False

    return False  # File not found

def get_partition_from_path(file_path):
    """
    Infers the partition from the file path (without leading /).
    """
    for partition, path_prefixes in PARTITION_MAPPING.items():
        for prefix in path_prefixes:
            if file_path.startswith(prefix + "/"):
                return partition

    # Check for dlkm partitions
    if "_dlkm" in file_path:
        return "dlkm"

    return "unknown"

def process_stock_file(stock_file_and_aosp_root_verbose):
    """
    Processes a single stock file.
    Returns:
        A tuple: (entry_for_proprietary_files, entry_for_interfaces_mk)
    """
    stock_file, aosp_root, verbose = stock_file_and_aosp_root_verbose  # Unpack arguments
    stock_file_name = os.path.basename(stock_file)
    stock_file_partition = get_partition_from_path(stock_file)

    print(f"Processing file: {stock_file}") # Normal output: Processing file

    if verbose:
        print(f"  File name: {stock_file_name}")
        print(f"  Partition: {stock_file_partition}")

    # Convert to lower case for case-insensitive comparisons
    stock_file_lower = stock_file.lower()

    # Apply Exclusions:
    excluded_partitions = ["product", "system", "dlkm", "vendor_boot", "init_boot", "dtbo"]
    if stock_file_name.endswith((".vdex", ".odex", ".apex", ".wav", ".ogg", ".txt", ".jpg", ".png", ".gz")):
        if verbose:
            print(f"  Skipping excluded file type: {stock_file_name}")
        return None, None

    if stock_file_partition in excluded_partitions:
        if verbose:
            print(f"  Skipping file from {stock_file_partition} partition: {stock_file_name}")
        return None, None

    if stock_file_name.endswith(".img") and stock_file_partition not in ["vendor", "odm"]:
        if verbose:
            print(f"  Skipping .img file from invalid partition: {stock_file_name}")
        return None, None

    if "overlay" in stock_file_lower:
        if verbose:
            print(f"  Skipping file containing 'overlay': {stock_file_name}")
        return None, None

    if "google" in stock_file_lower or "gms" in stock_file_lower:
        if verbose:
            print(f"  Skipping file containing 'google' or 'gms': {stock_file_name}")
        return None, None

    if "sepolicy" in stock_file_lower or "selinux" in stock_file_lower:
        if verbose:
            print(f"  Skipping file containing 'sepolicy' or 'selinux': {stock_file_name}")
        return None, None

    # Check for "android.hardware" files
    if stock_file_name.startswith("android.hardware"):
        if verbose:
            print(f"  Found android.hardware file: {stock_file_name}")
        module_name = stock_file_name.removesuffix(".so").removesuffix(".ko").removesuffix(".apk").removesuffix(".xml").removesuffix(".img")
        if stock_file_partition == "vendor":
            module_name += ".vendor"
        return None, f"    {module_name} \\"

    # Check if the file exists in AOSP using a broader mgrep search (without extension)
    module_name = stock_file_name.removesuffix(".so").removesuffix(".ko").removesuffix(".apk").removesuffix(".xml").removesuffix(".img")
    if not find_file_in_aosp((module_name, aosp_root), verbose): # Pass verbose flag
        if verbose:
            print(f"  {stock_file_name} NOT found in AOSP source.")
        return stock_file, None  # No leading hyphen
    else:
        if verbose:
            print(f"  {stock_file_name} found in AOSP source. Skipping.")
        return None, None

# --- Main Script ---

def main():
    parser = argparse.ArgumentParser(description="Generate proprietary-files.txt and interfaces.mk for LineageOS device bringup.")
    parser.add_argument("codename", help="Device codename")
    parser.add_argument("aosp_root", help="Path to AOSP root directory")
    parser.add_argument("-f", "--files", default="all_files.txt", help="Path to the list of all stock firmware files (default: all_files.txt)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output") # Add verbose argument
    args = parser.parse_args()

    stock_firmware_files_list = args.files
    device_codename = args.codename
    aosp_root = args.aosp_root
    output_file = "proprietary-files.txt"
    interfaces_mk_file = "interfaces.mk"
    verbose = args.verbose # Get verbose flag

    if not os.path.exists(aosp_root) or not os.path.exists(stock_firmware_files_list):
        print("Error: AOSP root directory or all_files.txt does not exist.")
        sys.exit(1)

    # Read the list of all stock firmware files
    try:
        with open(stock_firmware_files_list, 'r') as f:
            stock_files = [line.strip() for line in f]
    except FileNotFoundError:
        print(f"Error: {stock_firmware_files_list} not found.")
        sys.exit(1)

    # Prepare arguments for multiprocessing
    process_args = [(stock_file, aosp_root, verbose) for stock_file in stock_files] # Pass verbose flag

    # Parallelize the processing
    num_processes = cpu_count()
    if verbose:
        print(f"Using {num_processes} processes...")
    with Pool(processes=num_processes) as pool:
        results = pool.imap(process_stock_file, process_args)

        proprietary_files = []
        interface_entries = []
        for result in results:
            if result[0] is not None:
                proprietary_files.append(result[0])
            if result[1] is not None:
                interface_entries.append(result[1])

    # Write the proprietary-files.txt
    with open(output_file, "w") as f:
        f.write("# This file is generated by a script. Do not modify manually.\n")
        f.write(f"# Device: {device_codename}\n")

        current_partition = ""
        for line in proprietary_files:
            partition = get_partition_from_path(line)
            if partition != current_partition:
                f.write(f"\n# {partition}\n")
                current_partition = partition
            f.write(line + "\n")

    # Write the interfaces.mk
    with open(interfaces_mk_file, "w") as f:
        f.write("# This file is generated by a script. Do not modify manually.\n")
        f.write(f"# Device: {device_codename}\n\n")
        f.write("PRODUCT_PACKAGES += \\\n")
        for entry in interface_entries:
            f.write(entry + "\n")

    print(f"\nGenerated {output_file} and {interfaces_mk_file} for use with extract-files.sh")

if __name__ == "__main__":
    main()
