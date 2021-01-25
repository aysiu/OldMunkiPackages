#!/usr/local/munki/munki-python

from CoreFoundation import CFPreferencesCopyAppValue
from distutils.version import LooseVersion
import logging
import os
import plistlib
import sys

# Stolen from offset's offset
if not os.path.exists(os.path.expanduser('~/Library/Logs')):
    os.makedirs(os.path.expanduser('~/Library/Logs'))
log_file = os.path.expanduser('~/Library/Logs/omp.log')

logging.basicConfig(format = '%(asctime)s - %(levelname)s: %(message)s',
                    datefmt = '%m/%d/%Y %I:%M:%S %p',
                    level = logging.DEBUG,
                    filename = log_file)


# Function that moves from old location to new location for a list of items
def trash_old_stuff(trashlist, trashpath, newpath):
    if isinstance(trashlist, list):
        for old_location in trashlist:
            # Get the subfolders needed to be created
            path_within_destination = os.path.relpath(old_location, trashpath)
            # Create what will be the destination path
            new_location = os.path.join(newpath, path_within_destination)
            # Make sure all the relevant subfolders exist in the destination
            if not os.path.exists(os.path.dirname(new_location)):
                os.makedirs(os.path.dirname(new_location))
            # Even though we've been double-checking paths all along, let's just make one
            # last check
            if os.path.exists(old_location) and os.path.isdir(newpath):
                os.rename(old_location, new_location)
                logging.info('Moving {} to {}\n'.format(old_location, new_location))
            else:
                logging.error('One of {} or {} does not exist\n'.format(old_location,
                    new_location))
    else:
        logging.error('{} is not a valid list\n'.format(trashlist))

# Function that checks paths are writable
def check_folder_writable(checkfolder):
    if not os.access(checkfolder, os.W_OK):
        logging.error("You don't have access to {}".format(checkfolder))
        sys.exit(1)

def get_munkiimport_prefs():
    munkirepo = None
    munkirepo = CFPreferencesCopyAppValue('repo_url', 'com.googlecode.munki.munkiimport').replace('file://', '')
    if not munkirepo:
        logging.error('Cannot determine Munki repo URL. Be sure to run munkiimport --configure')
        sys.exit(1)
    return munkirepo

# Function that gets protected packages or returns an empty dictionary
def get_protected_packages(prefs):
    protected = {}
    if 'protected_packages' in prefs:
        for package in prefs['protected_packages']:
            if package['name'] in protected:
                protected[package['name']].append(package['version'])
                logging.info('Adding version {} to {} in protected '
                    'packages.'.format(package['version'], package['name']))
            else:
                protected[package['name']] = [package['version']]
                logging.info('Adding {} version {} to protected '
                    'packages.'.format(package['name'], package['version']))
    return protected

# Function that gets the dump location or returns the default
def get_dump_location(prefs, default_dump):
    if 'dump_location' in prefs and os.path.exists(prefs['dump_location']):
        dump_location = prefs['dump_location']
        logging.info('Will use dump location from the preferences '
            'file of {}.'.format(dump_location))
    else:
        dump_location = default_dump
        logging.info('Cannot determine a dump location from {}. Will '
            'be dumping to {}.'.format(prefs, default_dump))
    return dump_location

# Function that checks if a package and version are protected or not... for some reason,
# putting the two conditions in as one if/then doesn't seem to work
def not_protected_package(name, version, protected):
    if name in protected:
        if version in protected[name]:
            return False
        else:
            return True
    else:
        return True

def get_omp_prefs():
    # Where should old packages be moved to? User Trash by default
    default_where_to_dump = os.path.expanduser('~/.Trash')
    omp_prefs_location = os.path.expanduser('~/Library/Preferences/com.github.aysiu.omp.plist')
    if os.path.exists(omp_prefs_location):
        try:
            f = open(omp_prefs_location, 'r+b')
        except:
            logging.error('Unable to open {}'.format(omp_prefs_location))
            sys.exit(1)
        try:
            omp_prefs = plistlib.load(f)
        except:
            logging.error('Unable to get contents of {}'.format(omp_prefs_location))
            sys.exit(1)
        f.close()
        # Call function to get dump location from file
        where_to_dump = get_dump_location(omp_prefs, default_where_to_dump)
        # Call function to get protected packages
        protected_packages = get_protected_packages(omp_prefs)
    else:
        where_to_dump = default_where_to_dump
        logging.info('Cannot determine a dump location from {}. Will be dumping '
            'to {}.'.format(omp_prefs_location, where_to_dump))
        protected_packages = {}
        logging.info('Cannot determine a protected packages list from {}. Not '
            'protecting any packages.'.format(omp_prefs_location))
    return where_to_dump, protected_packages

# Main
def main():

    # Try to get the new Munki path
    MUNKI_ROOT_PATH = get_munkiimport_prefs()

    # Get OMP prefs or use defaults
    where_to_dump, protected_packages = get_omp_prefs()

    # Where is make catalogs?
    makecatalogs = '/usr/local/munki/makecatalogs'

    MUNKI_PKGS_DIR_NAME = 'pkgs'
    MUNKI_PKGSINFO_DIR_NAME = 'pkgsinfo'

    # Join paths based on what's defined
    pkgsinfo_path = os.path.join(MUNKI_ROOT_PATH, MUNKI_PKGSINFO_DIR_NAME)
    pkgs_path = os.path.join(MUNKI_ROOT_PATH, MUNKI_PKGS_DIR_NAME)

    # Check that the paths for the pkgsinfo and pkgs exist
    if not os.path.isdir(pkgsinfo_path) and not os.path.isdir(pkgs_path):
        logging.error('Your pkgsinfo and pkgs paths are not valid. Please '
            'check your repo_url value')
    else:
        # Make sure all relevant folders are writable
        check_folder_writable(pkgsinfo_path)
        check_folder_writable(pkgs_path)
        check_folder_writable(where_to_dump)
    
        # A list to store all items
        all_items = {};

        # Lists to store items to delete
        pkgs_to_delete = [];
        pkgsinfo_to_delete = [];

        # Walk through the pkgsinfo files...
        for root, dirs, files in os.walk(pkgsinfo_path):
            for dir in dirs:
                # Skip directories starting with a period
                if dir.startswith('.'):
                    dirs.remove(dir)
            for file in files:
                # Skip files that start with a period
                if file.startswith('.'):
                    continue
                fullfile = os.path.join(root, file)
                try:
                    f = open(fullfile, 'r+b')
                except:
                    logging.error('Unable to open {}'.format(fullfile))
                    continue
                try:
                    plist = plistlib.load(f)
                except:
                    logging.error('Unable to get contents of {}'.format(fullfile)) 
                    continue
                plistname = plist['name']
                plistversion = plist['version']
                # Make sure it's not a protected package
                # For some reason, if plistname in protected_packages and plistversion in
                # protected_packages[plistname]: won't work combined, so we'll do a
                # function test that separates them
                if not_protected_package(plistname, plistversion, protected_packages):
                    # The min OS version key doesn't exist in all pkginfo files
                    if 'minimum_os_version' in plist:
                        plistminimum_os_version = plist['minimum_os_version']
                    else:
                        plistminimum_os_version = ''
                    try:
                        plistcatalogs = plist['catalogs']
                    except KeyError as err:
                        logging.error('KeyError occured looking for key {} while checking '
                            '{}, it does not have a catalog'.format(err, file))
                    plistcatalogs.sort()
                    # Some items won't have an installer_item_location: nopkg .plist
                    # files, for example... that's okay
                    if 'installer_item_location' in plist:
                        plistinstaller_item_location = os.path.join(pkgs_path,
                            plist['installer_item_location'])
                    else:
                        plistinstaller_item_location = ''
        
                    # Create a dictionary based on the plist values read
                    plistdict = { 'pkginfo': fullfile,
                            'version': plistversion,
                            'catalogs': plistcatalogs,
                            'installer_item_location': plistinstaller_item_location,
                            'minimum_os_version': plistminimum_os_version }
                
                    # See if the plist name is already in all_items
                    if plistname in all_items:
                        # Compare the previously existing one to the currently focused
                        # one to see if they have the same catalogs (fix this because it
                        # could be testing production or production testing)
                        if (all_items[plistname]['catalogs'] ==  plistcatalogs and
                                all_items[plistname]['minimum_os_version'] ==
                                    plistminimum_os_version):
                            # See if this is a newer version than the one in there
                            if (LooseVersion(plistversion) >
                                    LooseVersion(all_items[plistname]['version'])):
                                # If this is newer, then move the old one to the items to
                                # delete list
                                if( all_items[plistname]['installer_item_location'] !=  '' ):
                                    pkgs_to_delete.append(all_items[plistname]['installer_item_location'])
                                pkgsinfo_to_delete.append(all_items[plistname]['pkginfo'])
                                del all_items[plistname]
                                all_items[plistname] = plistdict
                            else:
                                # Otherwise, if this is older, keep the old one in there,
                                # and move this one to the delete list
                                if( plistdict['installer_item_location'] !=  '' ):
                                    pkgs_to_delete.append(plistdict['installer_item_location'])
                                pkgsinfo_to_delete.append(plistdict['pkginfo'])
                    else:
                        # If it's not in the list already, add it
                        all_items[plistname] = plistdict

                else:
                    logging.info('Keeping {} version {} because it is a protected '
                        'package.'.format(plistname, plistversion))    

        if pkgs_to_delete:
            trash_old_stuff(pkgs_to_delete, pkgs_path, where_to_dump)
        if pkgsinfo_to_delete:
            trash_old_stuff(pkgsinfo_to_delete, pkgsinfo_path, where_to_dump)

        if pkgs_to_delete or pkgsinfo_to_delete:
            # If /usr/local/munki/makecatalogs exists (it should), then run it to reflect
            # the changes or let the user know to run it
            if os.path.exists(makecatalogs):
                logging.info('Running makecatalogs')
                os.system(makecatalogs)
            else:
                logging.error('{} could not be found. When you have a chance, run '
                    'makecatalogs on your Munki repo to have the changes '
                    'reflected.'.format(makecatalogs))
        else:
            logging.info('Nothing old to dump.')

if __name__ ==  '__main__':
    main()
