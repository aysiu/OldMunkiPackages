# OldMunkiPackages
Cleans out old Munki packages

## Why does OldMunkiPackages exist?
Like a lot of open source software, this is useful to the author (me). Others may find it useful, too, which is why I'm sharing it, but ultimately I created it to cull old packages from the [Munki](https://github.com/munki/munki/wiki) server I maintain. If you find yourself doing that a lot, too, you may find this useful.

Even with a GUI tool like [MunkiAdmin](https://github.com/hjuutilainen/munkiadmin), the catalog can get unwieldy and take a while to scroll through if you have a lot of old software packages.

There are other great tools and tutorials (see below) that do similar things but not exactly what I wanted, which is just a straight clean-out of old packages. I also wanted to learn a little more Python, so this was a good exercise to undertake for that.

[Spruce](https://github.com/sheagcraig/Spruce-for-Munki) is a fairly sophisticated tool that does way more than I want (pretty cool features, though), and then there's [an interactive shell script](https://grpugh.wordpress.com/2015/04/24/munki-how-to-remove-cruft/) that helps to get old things out.

I wanted to keep OMP (Old Munki Packages) fairly simple--just run with no arguments and automatically dump the old packages and pkginfo files.

## How do you use OMP?
Download the **OldMunkiPackages.py** file and put it somewhere you can reference later. It can go in /usr/local/bin/OldMunkiPackages.py or even on your desktop.

If you would like the dumped files to go somewhere other than your trash, modify the &lt;string&gt;&lt;/string&gt; part to be &lt;string&gt;/Path/To/Where/You/Want/Files/Dumped&lt;/string&gt;, and then put the **com.github.aysiu.omp.plist** file in the /Users/*username*/Library/Preferences folder of the *username* you're going to run OMP under. Otherwise, OMP will just default to using the logged-in user's trash as the dump folder.

OMP will also look for your repo path in **~/Library/Preferences/com.googlecode.munki.munkiimport.plist**, which you create when you run the `/usr/local/munki/munkiimport --configure` command the first time you set up Munki.

If you want to use OMP in conjunction with [Outset](https://github.com/chilcote/outset), you can put OMP into /usr/local/outset/login-every and have the script run every time you log into your Munki server or, if you use [Offset](https://github.com/aysiu/offset), you can put OMP into /usr/local/offset/logout-every and have the script run every time you log out of your Munki server. If you don't want it scheduled, you can just put it in a random folder and call it manually:
```python /path/to/OldMunkiPackages.py```

## What are the requirements for OMP?
I've tested it only on Mac OS X (El Capitan). In theory, it should work on older Macs. The way the script is written (referencing .plist files in ~/Library/Preferences) means it won't work for Windows or Linux.

The user who runs the script must have full read/write permissions on the Munki repository, as well as the destination (her own trash, or whatever folder you pick to move the old packages to).

## Why isn't OMP on a schedule?
The script isn't that destructive (rather than straight-out deleting the packages, it just moves them to a new location, even if that new location is the trash). Nevertheless, I would rather leave it up to the user to schedule (or run manually).

## How does OMP work?
You're welcome to look at the code, but in plain English, it basically works this way:
* Loop through the pkgsinfo folder (and subfolders) in the Munki repo.
* For each pkgsinfo, check to see if it exists in a list of packages to keep. If it doesn't, add it. If it does, and it's a newer version than what's already in there, move the older one to a list of packages to remove, and then put the newer version in the list of packages to keep.
* Loop through the packages (both pkgsinfo and pkgs) to remove and move them to the new location.
* If any files have been dumped, run makecatalogs if it exists (it should).

## What does OMP do with older packages that aren't in the same catalogs as the newer packages?
OMP will check the catalogs a package belongs to, sort them (so _testing, production_ and _production, testing_ will be comparable), and compare them. So only if the exact catalogs match will the old one be dumped. This works well for situations like an older package being in _testing_ and _production_, and a newer package being in only _testing_. In that case, you don't want to ditch the older package yet (until you've had a chance to test the newer one).

If you have some packages going through _development_, _testing_, _production_ while other packages go through only _testing_, _production_, that's fine... as long as each package of the same name goes through the same catalog track. In other words, if CustomForYourOrg goes through _development_, _testing_, _production_ and has two versions, the older version will be ditched if both the older and newer versions have _development_, _testing_, _production_ as their catalogs. But you could also have MozillaFirefox go through only _testing_, _production_, and OMP will work fine to get rid of all the old Firefoxes, as long as they all have _testing_, _production_ as their catalogs.

## How do I keep two recent versions instead of only one?
As I said before, the goal of this tool is to be as simple as possible. I generally test new packages as they come in. At a certain point, though, if I decide the new packages are good, I just want to flush out all the old ones at once.

## Acknowledgements
I straight-up lifted some code from Munki (to compare package versions and see which is newer), so thanks to Greg Neagle and the other Munki contributors.
