#!/bin/python3

import os
import subprocess
import json

bazel_targets = subprocess.run(
    ["bazel", "query", "--noshow_progress", "--noshow_loading_progress",
    'kind("cc_(library|binary|test|inc_library|proto_library)", //...) union kind("objc_(library|binary|test)", //...)'],
    stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()
print(f">> bazel targets: {bazel_targets}")
bazel_exec_root = subprocess.run(
    ["bazel", "info", "execution_root"],
    stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()[0]
print(f">> clean *.compile_commands.json files under {bazel_exec_root}...")
subprocess.run(["find", bazel_exec_root, "-name", "*.compile_commands.json", "-delete"])
subprocess.run([
    "bazel", "build",
    f"--override_repository=bazel_compdb={os.path.dirname(os.path.realpath(__file__))}", 
    "--aspects=@bazel_compdb//:aspects.bzl%compilation_database_aspect",
    "--noshow_progress",
    "--noshow_loading_progress",
    "--output_groups=compdb_files,header_files",
    ] + bazel_targets)
dbs = subprocess.run(
    ["find", bazel_exec_root, "-name", "*.compile_commands.json"],
    stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()
print(f">> found {len(dbs)} *.compile_commands.json files under {bazel_exec_root}")
db_entries = []
for db in dbs:
    with open(db, 'r') as file:
        db_entries.extend(json.loads(f"[{file.read()}]"))
bazel_workspace = subprocess.run(
    ["bazel", "info", "workspace"],
    stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()[0]
def replace_bazel_var(db_entry):
    if "directory" in db_entry and db_entry["directory"] == "__EXEC_ROOT__":
        db_entry["directory"] = bazel_workspace
        return db_entry
db_entries = list(map(replace_bazel_var, db_entries))
print(f">> generate {len(db_entries)} entries to compile_commands.json")
with open('compile_commands.json', 'w') as outdb:
    json.dump(db_entries, outdb, indent=2)
