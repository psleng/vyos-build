#!/usr/bin/env python3
#
# Copyright (C) 2024-2025 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import glob
import shutil
import sys
import tomli
import os

from argparse import ArgumentParser
from pathlib import Path
from subprocess import run, CalledProcessError, DEVNULL


def ensure_dependencies(dependencies: list) -> None:
    """Ensure Debian build dependencies are met"""
    if not dependencies:
        print("I: No additional dependencies to install")
        return

    print("I: Ensure Debian build dependencies are met")
    run(['sudo', 'apt-get', 'install', '-y'] + dependencies, check=True)


def apply_patches(repo_dir: Path, patch_dir: Path) -> None:
    """Apply patches from the patch directory to the repository"""
    if not patch_dir.exists() or not patch_dir.is_dir():
        print(f"I: Patch directory {patch_dir} does not exist, skipping patch application")
        return

    patches = sorted(patch_dir.glob('*'))
    if not patches:
        print(f"I: No patches found in {patch_dir}")
        return

    debian_patches_dir = repo_dir / 'debian/patches'
    debian_patches_dir.mkdir(parents=True, exist_ok=True)

    series_file = debian_patches_dir / 'series'
    with series_file.open('a') as series:
        for patch in patches:
            patch_dest = debian_patches_dir / patch.name
            shutil.copy(patch, patch_dest)
            series.write(patch.name + '\n')
            print(f"I: Applied patch: {patch.name}")

def prepare_package(repo_dir: Path, install_data: str) -> None:
    """Prepare a package"""
    if not install_data:
        print("I: No install data provided, skipping package preparation")
        return

    try:
        install_file = repo_dir / 'debian/install'
        install_file.parent.mkdir(parents=True, exist_ok=True)
        install_file.write_text(install_data)
        print("I: Prepared package")
    except Exception as e:
        print(f"Failed to prepare package: {e}")
        raise


def build_package(package: dict, patch_dir: Path, clean_git=False) -> None:
    """Build a package from the repository

    Args:
        package (list): List of Packages from toml
        patch_dir (Path): Directory containing patches
    """
    repo_name = package['name']
    repo_dir = Path(repo_name)
    print(f"I: build_package {repo_name} in {repo_dir}")

    # PSL-iolan_apps: Determine build mode from package configuration.
    # 'git_full' (default): Clone repo from SCM and checkout specific commit.
    # 'local_app': Build from the current working directory without git operations,
    #              useful for building packages from local source trees.
    build_mode = package.get('build_mode', 'git_full')

    # PSL-iolan_apps: Skip git clone/checkout for 'local_app' mode since we build from local sources
    if build_mode != 'local_app':
        try:
            # Clone the repository if it does not exist, otherwise check to see if we should clean / reset directory
            if not repo_dir.exists():
                run(['git', 'clone', package['scm_url'], str(repo_dir)], check=True)
                run(['git', 'checkout', package['commit_id']], cwd=repo_dir, check=True)
            elif clean_git:
                print("Repo detected; attempting to get latest rather than clone from scratch")
                # Must clean out anything in progress; notably patches may leave them in odd states
                run(['git', 'am', '--abort'], cwd=repo_dir, stdout=DEVNULL, stderr=DEVNULL)
                run(['git', 'merge', '--abort'], cwd=repo_dir, stdout=DEVNULL, stderr=DEVNULL)
                run(['git', 'rebase', '--abort'], cwd=repo_dir, stdout=DEVNULL, stderr=DEVNULL)
                run(['git', 'cherry-pick', '--abort'], cwd=repo_dir, stdout=DEVNULL, stderr=DEVNULL)
                run(['git', 'revert', '--abort'], cwd=repo_dir, stdout=DEVNULL, stderr=DEVNULL)
                # Continue by getting newest from remote, and cleaning out old to ensure we can successfully merge
                run(['git', 'fetch', 'origin', '--tags'], cwd=repo_dir, check=True)
                run(['sudo', 'git', 'clean', '-fdx'], cwd=repo_dir, check=True)
                # Slightly different commands if checking out a branch vs tag/sha, so do a check first to see which was passed in
                commit_check = run(['git', 'ls-remote', '--heads', 'origin', package['commit_id']], cwd=repo_dir, capture_output=True, text=True, check=True)
                current = run(['git', 'rev-parse', 'HEAD'], cwd=repo_dir, capture_output=True, text=True, check=True)
                # Checking for debs; if none are present then assume we need to rebuild
                # TODO: not sure how to guarantee there was no issue building debs; if 1 built and 1 failed this would still work
                deb_files = list(Path.cwd().glob('*.deb'))
                if commit_check.stdout.strip():
                    if deb_files:
                        remote = run(['git', 'rev-parse', f'origin/{package["commit_id"]}'], cwd=repo_dir, capture_output=True, text=True, check=True)
                        if remote.stdout.strip() in current.stdout:
                            print(f"I: Skipping building this package: {repo_name}\nCurrent and remote branches match, as well as their commit ID", flush=True)
                            return
                    run(['git', 'checkout', '--force', f'origin/{package["commit_id"]}'], cwd=repo_dir, check=True)
                else:
                    if deb_files:
                        remote = run(['git', 'rev-list', '-n', '1', package['commit_id']], cwd=repo_dir, capture_output=True, text=True, check=True)
                        tag_check = run(['git', 'ls-remote', '--tags', 'origin', package['commit_id']], cwd=repo_dir, capture_output=True, text=True, check=True)
                        if tag_check.stdout and current.stdout.strip() in remote.stdout:
                            print(f"I: Skipping building this package: {repo_name}\nCurrent commit ID and ID that remote tag points to both match", flush=True)
                            return
                        elif package["commit_id"] in remote.stdout:
                            print(f"I: Skipping building this package: {repo_name}\nCurrent and remote SHAs/commit IDs both match", flush=True)
                            return
                    run(['git', 'checkout', '--force', package['commit_id']], cwd=repo_dir, check=True)
            else:
                run(['git', 'checkout', package['commit_id']], cwd=repo_dir, check=True)

        except CalledProcessError as e:
            print(f"Failed to clone or checkout for package '{repo_name}': {e}")
            sys.exit(1)

    try:
        # The `pre_build_hook` is an optional configuration defined in `package.toml`.
        # It executes after the repository is checked out and before the build process begins.
        # This hook allows you to perform preparatory tasks, such as creating directories,
        # copying files, or running custom scripts/commands.
        #
        # Usage:
        # - Single command:
        #     pre_build_hook = "echo 'Hello Pre-Build-Hook'"
        #
        # - Multi-line commands:
        #     pre_build_hook = """
        #       mkdir -p ../hello/vyos
        #       mkdir -p ../vyos
        #       cp example.txt ../vyos
        #     """
        #
        # - Combination of commands and scripts:
        #     pre_build_hook = "ls -l; ./script.sh"
        pre_build_hook = package.get('pre_build_hook', '')
        if pre_build_hook:
            try:
                print(f'I: execute pre_build_hook for the package "{repo_name}"')
                run(pre_build_hook, cwd=repo_dir, check=True, shell=True)
            except CalledProcessError as e:
                print(e)
                print(f"I: pre_build_hook failed for the {repo_name}")
                raise

        # Apply patches if the 'apply_patches' key is set to True (default) in the package configuration
        # This allows skipping patch application for specific packages when desired
        #
        # Usage:
        #   apply_patches = false
        #
        # Default to True if the key is missing
        if package.get('apply_patches', True):
            # Check if the 'patches' directory exists in the repository
            if (repo_dir / 'patches'):
                apply_patches(repo_dir, patch_dir / repo_name)

        if build_mode == 'local_app':
            # PSL-iolan_apps: For local_app mode, use current working directory as the source tree
            # instead of a cloned repository directory
            repo_dir = Path(os.getcwd())
        else:
            # Sanitize the commit ID and build a tarball for the package
            commit_id_sanitized = package['commit_id'].replace('/', '_')
            tarball_name = f"{repo_name}_{commit_id_sanitized}.tar.gz"
            run(['tar', '--exclude=.git', '--exclude=.github', '-czf', tarball_name, '-C', str(repo_dir.parent), repo_name], check=True)
            print(f"I: Tarball created: {tarball_name}")

        # Prepare the package if required
        if package.get('prepare_package', False):
            prepare_package(repo_dir, package.get('install_data', ''))

        # Build dependency package and install it
        if (repo_dir / 'debian/control').exists():
            cmd = package.get('mk_build_deps_cmd', False)  # PSL: allow override
            try:
                if cmd:
                    run(cmd, cwd=repo_dir, check=True, shell=True)
                else:
                    run('sudo mk-build-deps --install --tool "apt-get --yes --no-install-recommends" 2>&1', cwd=repo_dir, check=True, shell=True)
                    run('sudo dpkg -i *build-deps*.deb 2>&1', cwd=repo_dir, check=True, shell=True)
                    if build_mode == 'local_app':
                        # PSL-iolan_apps: For local_app mode, explicitly install all dependencies listed in the
                        # build-deps package. This ensures locally built libs are used instead of
                        # versions from the upstream repositories if exists so local changes are prioritized.
                        run("sudo apt-get install -y $(dpkg-deb -f *build-deps*.deb Depends | tr ',' ' ') 2>&1", cwd=repo_dir, check=True, shell=True)
            except CalledProcessError as e:
                print(f"Failed to build package {repo_name}: {e}")
                #exit(e.returncode)  # Really fail

        # Build the package, check if we have build_cmd in the package.toml
        try:
            build_cmd = package.get('build_cmd', 'dpkg-buildpackage -uc -us -tc -F --source-option=--tar-ignore=.git --source-option=--tar-ignore=.github')
            run(build_cmd + " 2>&1", cwd=repo_dir, check=True, shell=True)
        except CalledProcessError as e:
            print(e)
            print("I: Source packages build failed, ignoring - building binaries only")
            build_cmd = package.get('build_cmd', 'dpkg-buildpackage -uc -us -tc -b')
            run(build_cmd + " 2>&1", cwd=repo_dir, check=True, shell=True)

    except CalledProcessError as e:
        print(f"Failed to build package {repo_name}: {e}")
        #exit(e.returncode)  # Really fail
    finally:
        # Clean up repository directory
        # shutil.rmtree(repo_dir, ignore_errors=True)
        pass


def cleanup_build_deps(repo_dir: Path) -> None:
    """Clean up build dependency packages"""
    try:
        if repo_dir.exists():
            for file in glob.glob(str(repo_dir / '*build-deps*.deb')):
                os.remove(file)
            print("I: Cleaned up build dependency packages")
    except Exception as e:
        print(f"Error cleaning up build dependencies: {e}")


def copy_packages(repo_dir: Path) -> None:
    """Copy generated .deb packages to the parent directory"""
    try:
        deb_files = glob.glob(str(repo_dir / '*.deb'))
        for deb_file in deb_files:
            shutil.copy(deb_file, repo_dir.parent)
            print(f'I: copy generated "{deb_file}" package')
    except Exception as e:
        print(f"Error copying packages: {e}")


if __name__ == '__main__':
    # Prepare argument parser
    arg_parser = ArgumentParser()
    arg_parser.add_argument('--config',
                            default='package.toml',
                            help='Path to the package configuration file')
    arg_parser.add_argument('--patch-dir',
                            default='patches',
                            help='Path to the directory containing patches')
    arg_parser.add_argument('--clean-git',
                            action='store_true',
                            help='Path to the directory containing patches')
    args = arg_parser.parse_args()

    # Load package configuration
    with open(args.config, 'rb') as file:
        config = tomli.load(file)

    packages = config['packages']
    patch_dir = Path(args.patch_dir)

    # Update APT mirror list before the build
    run(['sudo', 'apt-get', 'update'], check=True)

    # Load global dependencies
    global_dependencies = config.get('dependencies', {}).get('packages', [])
    if global_dependencies:
        ensure_dependencies(global_dependencies)

    for package in packages:
        # Build the package
        build_package(package, patch_dir, args.clean_git)

        # Clean up build dependency packages after build
        cleanup_build_deps(Path(package['name']))

        # Copy generated .deb packages to parent directory
        copy_packages(Path(package['name']))
