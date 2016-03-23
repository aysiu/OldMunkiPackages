# OldMunkiPackages
Cleans out old Munki packages

* [Why does OldMunkiPackages exist?](#why-does-oldmunkipackages-exist)
* [How do you install OMP?](#how-do-you-install-omp)
 * [Install .pkg file](#install-pkg-file)
 * ["Install" OMP manually](#install-omp-manually)
* [How do you use OMP?](#how-do-you-use-omp)
* [What are the requirements for OMP?](#what-are-the-requirements-for-omp)
* [Why isn't OMP on a schedule?](#why-isnt-omp-on-a-schedule)
* [How does OMP work?](#how-does-omp-work)
* [What does OMP do with older packages that aren't in the same catalogs as the newer packages?](#what-does-omp-do-with-older-packages-that-arent-in-the-same-catalogs-as-the-newer-packages)
* [How do I keep two recent versions instead of only one?](#how-do-i-keep-two-recent-versions-instead-of-only-one)
* [How do I make sure one particular old version of a package never gets removed?](#how-do-make-sure-one-particular-old-version-of-a-package-never-gets-removed)
* [Acknowledgements](#acknowledgements)

## Why does OldMunkiPackages exist?
Like a lot of open source software, this is useful to the author (me). Others may find it useful, too, which is why I'm sharing it, but ultimately I created it to cull old packages from the [Munki](https://github.com/munki/munki/wiki) server I maintain. If you find yourself doing that a lot, too, you may find this useful.

Even with a GUI tool like [MunkiAdmin](https://github.com/hjuutilainen/munkiadmin), the catalog can get unwieldy and take a while to scroll through if you have a lot of old software packages.

There are other great tools and tutorials (see below) that do similar things but not exactly what I wanted, which is just a straight clean-out of old packages. I also wanted to learn a little more Python, so this was a good exercise to undertake for that.

[Spruce](https://github.com/sheagcraig/Spruce-for-Munki) is a fairly sophisticated tool that does way more than I want (pretty cool features, though), and then there's [an interactive shell script](https://grpugh.wordpress.com/2015/04/24/munki-how-to-remove-cruft/) that helps to get old things out.

I wanted to keep OMP (Old Munki Packages) fairly simple--just run with no arguments and automatically dump the old packages and pkginfo files.

## How do you install OMP?

### Install .pkg file
Head over to [the releases page](https://github.com/aysiu/OldMunkiPackages/releases/) to get the latest pre-packaged release.

### "Install" OMP manually
Download the **OldMunkiPackages.py** file and put it in **/usr/local/omp/**

If you would like the dumped files to go somewhere other than your trash, modify the &lt;string&gt;&lt;/string&gt; part to be &lt;string&gt;/Path/To/Where/You/Want/Files/Dumped&lt;/string&gt;, and then put the **com.github.aysiu.omp.plist** file in the /Users/*username*/Library/Preferences folder of the *username* you're going to run OMP under. Otherwise, OMP will just default to using the logged-in user's trash as the dump folder.

Alternatively, you can (instead of modifying and moving the file) just use a defaults command to create and modify the file at once:
`defaults write /Users/username/Library/Preferences/com.github.aysiu.omp.plist dump_location "/Path/To/Where/You/Want/Files/Dumped"` where **username** is your username and **/Path/To/Where/You/Want/Files/Dumped** is where you want files dumped.

## How do you use OMP?
OMP will also look for your repo path in **~/Library/Preferences/com.googlecode.munki.munkiimport.plist**, which you create when you run the `/usr/local/munki/munkiimport --configure` command the first time you set up Munki.

If you want to use OMP in conjunction with [Outset](https://github.com/chilcote/outset), you can put OMP into /usr/local/outset/login-every and have the script run every time you log into your Munki server or, if you use [Offset](https://github.com/aysiu/offset), you can put OMP into /usr/local/offset/logout-every and have the script run every time you log out of your Munki server.

If you don't want it scheduled, you can just call it manually:
```python /usr/local/omp/OldMunkiPackages.py```

Logs (errors or information) will go to **~/Library/Logs/omp.log**

## What are the requirements for OMP?
I've tested it only on Mac OS X (El Capitan). In theory, it should work on older Macs. The way the script is written (referencing .plist files in ~/Library/Preferences) means it won't work for Windows or Linux.

The user who runs the script must have full read/write permissions on the Munki repository, as well as the destination (her own trash, or whatever folder she picks to move the old packages to).

## Why isn't OMP on a schedule by default?
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

I don't plan on implementing a configurable number of recent package versions to keep (apart from the most recent one), but feel free to fork the project if you'd like to write your own modification.

## How do I make sure one particular old version of a package never gets removed?
So far, I can thinkn of only one good example of this problem, which is Office2011_update version 14.1.0--more details at [its AutoPkg recipe](https://github.com/autopkg/recipes/blob/master/MSOfficeUpdates/MSOffice2011Updates.munki.recipe). For now, I've just hard-coded (in a one-item directory) that particular old version and package. In the future, I may consider making an array in the .plist preference file for allowing users to configure their own "protected packages."

OMP also will not remove older versions of packages (even in the same catalogs) if the older version has a different minimum OS, so that may be one way around it if you want to keep older versions. For example, you may have a version of one package that goes through 10.10 and another that goes 10.11 and up. If you remove the 10.10 package, then the 10.10 users won't have access to any version of that package.

## Acknowledgements
I straight-up lifted some code from Munki (to compare package versions and see which is newer), so thanks to Greg Neagle and the other Munki contributors. Also thanks to Joseph Chilcote for some Python logging code.
