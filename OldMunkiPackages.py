#!/usr/bin/python

from distutils import version
import FoundationPlist
import logging
import os
from pprint import pprint
import sys
from types import StringType
from xml.parsers.expat import ExpatError

# Dictionary of protected packages.
# May move this to a .plist, if it turns out to be popular and more than just Microsoft Office 2011 updates.
protected_packages = {}
protected_packages['Office2011_update'] = { 'version': '14.1.0' }

# Stolen from offset's offset
if not os.path.exists(os.path.expanduser('~/Library/Logs')):
	os.makedirs(os.path.expanduser('~/Library/Logs'))
log_file = os.path.expanduser('~/Library/Logs/omp.log')

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG,
                    filename=log_file)

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
				logging.info("Moving %s to %s\n" % (old_location, new_location))
			else:
				logging.error("One of %s or %s does not exist\n" % (old_location, new_location))
	else:
		logging.error("%s is not a valid list\n" % trashlist)

# Function that checks paths are writable
def check_folder_writable(checkfolder):
	if not os.access(checkfolder, os.W_OK):
		logging.error("You don't have access to %s" % checkfolder)
		sys.exit(1)

# Main
def main():

	# Try to get the new Munki path
	munkiimport_prefs_location=os.path.join(os.getenv("HOME"), "Library/Preferences/com.googlecode.munki.munkiimport.plist")
	if os.path.exists(munkiimport_prefs_location):
		munkiimport_prefs=FoundationPlist.readPlist(munkiimport_prefs_location)
		MUNKI_ROOT_PATH=munkiimport_prefs['repo_path']
	else:
		logging.error("Cannot find the %s preferences file to read the Munki repo path" % munkiimport_prefs_location)
		sys.exit(1)

	# Where should old packages be moved to? User Trash by default
	default_where_to_dump=os.path.join(os.getenv("HOME"), ".Trash")
	omp_prefs_location=os.path.join(os.getenv("HOME"), "Library/Preferences/com.github.aysiu.omp.plist")
	if os.path.exists(omp_prefs_location):
		omp_prefs=FoundationPlist.readPlist(omp_prefs_location)
		if os.path.exists(omp_prefs['dump_location']):
			where_to_dump=omp_prefs['dump_location']
			logging.info("Will use dump location from the preferences file of %s." % where_to_dump)
		else:
			where_to_dump=default_where_to_dump
			logging.info("Cannot determine a dump location from %s. Will be dumping to %s." % (omp_prefs_location, where_to_dump))
	else:
		where_to_dump=default_where_to_dump
		logging.info("Cannot determine a dump location from %s. Will be dumping to %s." % (omp_prefs_location, where_to_dump))

	# Where is make catalogs?
	makecatalogs='/usr/local/munki/makecatalogs'

	MUNKI_PKGS_DIR_NAME = 'pkgs'
	MUNKI_PKGSINFO_DIR_NAME = 'pkgsinfo'

	# Join paths based on what's defined
	pkgsinfo_path=os.path.join(MUNKI_ROOT_PATH, MUNKI_PKGSINFO_DIR_NAME)
	pkgs_path=os.path.join(MUNKI_ROOT_PATH, MUNKI_PKGS_DIR_NAME)

	# Check that the paths for the pkgsinfo and pkgs exist
	if not os.path.isdir(pkgsinfo_path) and not os.path.isdir(pkgs_path):
		logging.error("Your pkgsinfo and pkgs paths are not valid. Please check your MUNKI_ROOT_PATH value")
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
				if dir.startswith("."):
					dirs.remove(dir)
			for file in files:
				# Skip files that start with a period
				if file.startswith("."):
					continue
				fullfile = os.path.join(root, file)
				plist = FoundationPlist.readPlist(fullfile)
				plistname = plist['name']
				plistversion = plist['version']
				# Make sure it's not a protected package
				if plistname in protected_packages and protected_packages[plistname]['version'] == plistversion:
					logging.info('Keeping %s version %s because it is a protected package.' % (plistname, plistversion))
				else:
					# The min OS version key doesn't exist in all pkginfo files
					if 'minimum_os_version' in plist:
						plistminimum_os_version = plist['minimum_os_version']
					else:
						plistminimum_os_version = ''
					plistcatalogs = plist['catalogs']
					plistcatalogs.sort()
					# Some items won't have an installer_item_location: nopkg .plist files, for example... that's okay
					if 'installer_item_location' in plist:
						plistinstaller_item_location = os.path.join(pkgs_path, plist['installer_item_location'])
					else:
						plistinstaller_item_location = ''
		
					# Create a dictionary based on the plist values read
					plistdict={ 'pkginfo': fullfile, 'version': plistversion, 'catalogs': plistcatalogs, 'installer_item_location': plistinstaller_item_location, 'minimum_os_version': plistminimum_os_version}
				
					# See if the plist name is already in all_items
					if plistname in all_items:
						# Compare the previously existing one to the currently focused one to see if they have the same catalogs (fix this because it could be testing production or production testing)
						if all_items[plistname]['catalogs'] == plistcatalogs and all_items[plistname]['minimum_os_version'] == plistminimum_os_version:
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

		if pkgs_to_delete:
			trash_old_stuff(pkgs_to_delete, pkgs_path, where_to_dump)
		if pkgsinfo_to_delete:
			trash_old_stuff(pkgsinfo_to_delete, pkgsinfo_path, where_to_dump)

		if pkgs_to_delete or pkgsinfo_to_delete:
			# If /usr/local/munki/makecatalogs exists (it should), then run it to reflect the changes or let the user know to run it
			if os.path.exists(makecatalogs):
				logging.info("Running makecatalogs")
				os.system(makecatalogs)
			else:
				logging.error("%s could not be found. When you have a chance, run makecatalogs on your Munki repo to have the changes reflected." % makecatalogs)
		else:
			logging.info("Nothing old to dump.")

if __name__ == '__main__':
    main()
