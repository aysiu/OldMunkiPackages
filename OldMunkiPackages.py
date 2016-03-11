#!/usr/bin/python

import os
import plistlib
import sys
from pprint import pprint
from xml.parsers.expat import ExpatError
from distutils import version
from types import StringType

MUNKI_ROOT_PATH = '/Users/Shared/munki_repo'
###### Where is the path to your Munki repo?
###### Uncomment the line below if your Munki repo is somewhere else
# MUNKI_ROOT_PATH = 'Put/Path/You/Want'

# Where should old packages be moved to?
# Guess at user trash
where_to_dump=os.path.join(os.getenv("HOME"), ".Trash")

###### Uncomment the line below if you'd like the packages to go somewhere other than the trash folder
# where_to_dump='/Put/Path/You/Want'

# Where is make catalogs?
makecatalogs='/usr/local/munki/makecatalogs'

# Double-check the user trash exists
if not os.path.isdir(where_to_dump):
	# If the directory doesn't already exist, make it
	where_to_dump=os.makedirs(where_to_dump)

MUNKI_PKGS_DIR_NAME = 'pkgs'
MUNKI_PKGSINFO_DIR_NAME = 'pkgsinfo'

# Stolen from Munki's munkicommon.py
class MunkiLooseVersion(version.LooseVersion):
    '''Subclass version.LooseVersion to compare things like
    "10.6" and "10.6.0" as equal'''

    def __init__(self, vstring=None):
        if vstring is None:
            # treat None like an empty string
            self.parse('')
        if vstring is not None:
            if isinstance(vstring, unicode):
                # unicode string! Why? Oh well...
                # convert to string so version.LooseVersion doesn't choke
                vstring = vstring.encode('UTF-8')
            self.parse(str(vstring))

    def _pad(self, version_list, max_length):
        """Pad a version list by adding extra 0
        components to the end if needed"""
        # copy the version_list so we don't modify it
        cmp_list = list(version_list)
        while len(cmp_list) < max_length:
            cmp_list.append(0)
        return cmp_list

    def __cmp__(self, other):
        if isinstance(other, StringType):
            other = MunkiLooseVersion(other)

        max_length = max(len(self.version), len(other.version))
        self_cmp_version = self._pad(self.version, max_length)
        other_cmp_version = self._pad(other.version, max_length)

        return cmp(self_cmp_version, other_cmp_version)


# Function that moves from old location to new location for a list of items
def trash_old_stuff(trashlist, trashpath, newpath):
	if isinstance(trashlist, list):
		for old_location in trashlist:
			# Get the subfolders needed to be created
			path_within_destination=os.path.relpath(old_location, trashpath)
			# Create what will be the destination path
			new_location=os.path.join(newpath, path_within_destination)
			# Make sure all the relevant subfolders exist in the destination
			if not os.path.exists(os.path.dirname(new_location)):
				os.makedirs(os.path.dirname(new_location))
			# Even though we've been double-checking paths all along, let's just make one last check
			if os.path.exists(old_location) and os.path.isdir(newpath):
				os.rename(old_location, new_location)
				print "Moving %s to %s\n" % (old_location, new_location)
			else:
				print "One of %s or %s does not exist\n" % (old_location, new_location)
	else:
		print "%s is not a valid list\n" % trashlist


# Join paths based on what's defined
pkgsinfo_path=os.path.join(MUNKI_ROOT_PATH, MUNKI_PKGSINFO_DIR_NAME)
pkgs_path=os.path.join(MUNKI_ROOT_PATH, MUNKI_PKGS_DIR_NAME)

# Check that the paths for the pkgsinfo and pkgs exist
if not os.path.isdir(pkgsinfo_path) and not os.path.isdir(pkgs_path):
	print "Your pkgsinfo and pkgs paths ae not valid. Please check your MUNKI_ROOT_PATH value"
else:

	# A list to store all items
	all_items = {};

	# Lists to store items to delete
	pkgs_to_delete = [];
	pkgsinfo_to_delete = [];

	# Walk through the pkgsinfo files...
	for root, dirs, files in os.walk(pkgsinfo_path):
		for dir in dirs:
			# Skip directories starting with a period
			if dir.startswith("."):
				dirs.remove(dir)
		for file in files:
			# Skip files that start with a period
			if file.startswith("."):
				continue
			fullfile = os.path.join(root, file)
			plist = plistlib.readPlist(fullfile)
			plistname = plist['name']
			plistversion = plist['version']
			plistcatalogs = plist['catalogs']
			plistcatalogs.sort()
			# Some items won't have an installer_item_location: nopkg .plist files, for example... that's okay
			if 'installer_item_location' in plist:
				plistinstaller_item_location = os.path.join(pkgs_path, plist['installer_item_location'])
			else:
				plistinstaller_item_location = ''
		
			# Create a dictionary based on the plist values read
			plistdict={ 'pkginfo': fullfile, 'version': plistversion, 'catalogs': plistcatalogs, 'installer_item_location': plistinstaller_item_location}
				
			# See if the plist name is already in all_items
			if plistname in all_items:
				# Compare the previously existing one to the currently focused one to see if they have the same catalogs (fix this because it could be testing production or production testing)
				if all_items[plistname]['catalogs'] == plistcatalogs:
					# See if this is a newer version than the one in there
					if cmp (MunkiLooseVersion(plistversion), MunkiLooseVersion(all_items[plistname]['version'])) > 0 :
						# If this is newer, then move the old one to the items to delete list
						if( all_items[plistname]['installer_item_location'] != '' ):
							pkgs_to_delete.append(all_items[plistname]['installer_item_location'])
						pkgsinfo_to_delete.append(all_items[plistname]['pkginfo'])
						del all_items[plistname]
						all_items[plistname]=plistdict
					else:
						# Otherwise, if this is older, keep the old one in there, and move this one to the delete list
						if( plistdict['installer_item_location'] != '' ):
							pkgs_to_delete.append(plistdict['installer_item_location'])
						pkgsinfo_to_delete.append(plistdict['pkginfo'])
			else:
				# If it's not in the list already, add it
				all_items[plistname]=plistdict		

	trash_old_stuff(pkgs_to_delete, pkgs_path, where_to_dump)
	trash_old_stuff(pkgsinfo_to_delete, pkgsinfo_path, where_to_dump)

	# If /usr/local/munki/makecatalogs exists (it should), then run it to reflect the changes or let the user know to run it
	if os.path.exists(makecatalogs):
		print "Running makecatalogs"
		os.system(makecatalogs)
	else:
		print "%s could not be found. When you have a chance, run makecatalogs on your Munki repo to have the changes reflected." % makecatalogs
