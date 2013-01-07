#!/usr/bin/python -tt
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# (c) 2007 Red Hat. Written by skvidal@fedoraproject.org

import os
import yum
import rpmUtils
import datetime
import urlparse
from yum.misc import to_unicode

class DiffYum(yum.YumBase):
    def __init__(self):
        yum.YumBase.__init__(self)
        self.dy_repos = {'old':[], 'new':[]}
        self.dy_basecachedir = yum.misc.getCacheDir()
        os.chdir(self.dy_basecachedir)
        self.dy_archlist = ['src']
        
    def dy_shutdown_all_other_repos(self):
        # disable all the other repos
        self.repos.disableRepo('*')

        
    def dy_setup_repo(self, repotype, baseurl):
        repoid = urlparse.urlsplit(baseurl)[2].replace(":","_").replace("/", "_")
        self.dy_repos[repotype].append(repoid)
     
        # make our new repo obj
        newrepo = yum.yumRepo.YumRepository(repoid)
        newrepo.name = repoid
        newrepo.baseurl = [baseurl]
        newrepo.basecachedir = self.dy_basecachedir
        newrepo.metadata_expire = 0
        newrepo.sslverify = 0 
        # add our new repo
        self.repos.add(newrepo)        
        # enable that repo
        self.repos.enableRepo(repoid)
        # setup the repo dirs/etc
        self.doRepoSetup(thisrepo=repoid)
        self._getSacks(archlist=self.dy_archlist, thisrepo=repoid)

    def dy_diff(self):
        add = []
        remove = []        
        modified = []
        obsoleted = {} # obsoleted = by
        newsack = yum.packageSack.ListPackageSack()
        for repoid in self.dy_repos['new']:
            newsack.addList(self.pkgSack.returnPackages(repoid=repoid))

        oldsack = yum.packageSack.ListPackageSack()
        for repoid in self.dy_repos['old']:
            oldsack.addList(self.pkgSack.returnPackages(repoid=repoid))

        for pkg in newsack.returnNewestByName():
            tot = self.pkgSack.searchNevra(name=pkg.name)
            if len(tot) == 1: # it's only in new
                add.append(pkg)
            if len(tot) > 1:
                if oldsack.contains(name=pkg.name):
                    newest_old = oldsack.returnNewestByName(name=pkg.name)[0]
                    modified.append((pkg, newest_old))
                else:
                    add.append(pkg)

        for pkg in oldsack.returnNewestByName():
            if len(newsack.searchNevra(name=pkg.name)) == 0:
                remove.append(pkg)


        for po in remove:
            for newpo in add:
                foundit = 0
                for obs in newpo.obsoletes:
                    if po.inPrcoRange('provides', obs):
                        foundit = 1
                        obsoleted[po] = newpo
                        break
                if foundit:
                    break
        
        ygh = yum.misc.GenericHolder()
        ygh.add = add
        ygh.remove = remove
        ygh.modified = modified
        ygh.obsoleted = obsoleted
        return ygh

def short_diff(new, old):

    my = DiffYum()
    my.dy_shutdown_all_other_repos()

    for r in old:
        try:
            my.dy_setup_repo('old', str(r))
        except yum.Errors.RepoError, e:
            raise RuntimeError("Could not setup repo at url  %s: %s" % (r, e))
    
    for r in new:
        try:
            my.dy_setup_repo('new', str(r))
        except yum.Errors.RepoError, e:
            raise RuntimeError("Could not setup repo at url %s: %s" % (r, e))

    ygh = my.dy_diff()

    added = removed = modified = []
    diff = {}

    if ygh.add:
        added = [ pkg.name for pkg in ygh.add ]
        if added:
            diff["added"] = added
    if ygh.remove:
        removed = [ pkg.name for pkg in ygh.remove ]
        if removed:
            diff["removed"] = removed
    if ygh.modified:
        for pkg, oldpkg in ygh.modified:
            if not pkg.ver == oldpkg.ver:
                modified.append(pkg.name)
        if modified:
            diff["modified"] = modified

    return diff

def generate_short_diff(new, old):

    report = []

    for k, v in short_diff(new, old).items():
        report.append("%s: %s" % (k, ", ".join(v)))

    return "\n".join(report)

def generate_report(new, old, quiet=True, archlist=['src'], size=False, rebuilds=False, commits=False):
 
    my = DiffYum()
    my.dy_shutdown_all_other_repos()
    my.dy_archlist = archlist
    report = []

    if not quiet: report.append('setting up repos')
    for r in old:
        if not quiet: report.append("setting up old repo %s" % r)
        try:
            my.dy_setup_repo('old', str(r))
        except yum.Errors.RepoError, e:
            raise RuntimeError("Could not setup repo at url  %s: %s" % (r, e))
    
    for r in new:
        if not quiet: report.append("setting up new repo %s" % r)
        try:
            my.dy_setup_repo('new', str(r))
        except yum.Errors.RepoError, e:
            raise RuntimeError("Could not setup repo at url %s: %s" % (r, e))

    if not quiet: report.append('performing the diff')
    ygh = my.dy_diff()
    

    new_repo = my.repos.getRepo(my.dy_repos['new'][-1])
    old_repo = my.repos.getRepo(my.dy_repos['old'][-1])
    new_ts = datetime.datetime.fromtimestamp(new_repo.repoXML.timestamp)
    old_ts = datetime.datetime.fromtimestamp(old_repo.repoXML.timestamp)
    new_name = urlparse.urlsplit(new_repo.urls[0])[2].replace("/", " ")
    old_name = urlparse.urlsplit(old_repo.urls[0])[2].replace("/"," ")
    report.append('Changes introduced to repository%screated at %s compared to repository%screated at %s\n\n' % (new_name, new_ts, old_name, old_ts))

    total_sizechange = 0
    add_sizechange = 0
    remove_sizechange = 0
    rebuilt = 0
    commits = 0
    if ygh.add:
        for pkg in ygh.add:
            report.append('New package %s' % pkg.name)
            report.append('        %s' % pkg.summary)
            add_sizechange += int(pkg.size)
            commits += 1
                
    if ygh.remove:
        for pkg in ygh.remove:
            report.append('Removed package %s' % pkg.name)
            if ygh.obsoleted.has_key(pkg):
                report.append('Obsoleted by %s' % ygh.obsoleted[pkg])
            remove_sizechange += (int(pkg.size))
                
    if ygh.modified:
        report.append('Updated Packages:\n')
        for (pkg, oldpkg) in ygh.modified:
            msg = "%s-%s-%s" % (pkg.name, pkg.ver, pkg.rel)
            dashes = "-" * len(msg) 
            msg += "\n%s\n" % dashes
            header = msg
            # get newest clog time from the oldpkg
            # for any newer clog in pkg
            oldlogs = oldpkg.changelog
            if len(oldlogs):
                #  Don't sort as that can screw the order up when time is the
                # same.
                oldtime    = oldlogs[0][0]
                oldauth    = oldlogs[0][1]
                oldcontent = oldlogs[0][2]
                for (t, author, content) in  pkg.changelog:
                    if t < oldtime:
                        break
                    if ((t == oldtime) and (author == oldauth) and 
                        (content == oldcontent)):
                        break

                    tm = datetime.date.fromtimestamp(int(t))
                    tm = tm.strftime("%a %b %d %Y")
                    msg += "* %s %s\n%s\n\n" % (tm, to_unicode(author),
                                                to_unicode(content))
                    commits += 1
                    

            if size:
                sizechange = int(pkg.size) - int(oldpkg.size)
                total_sizechange += sizechange
                msg += "\nSize Change: %s bytes\n" % sizechange

            if msg == header:
                rebuilt = rebuilt + 1
                if  rebuilds:
                    msg += "\n* Package rebuilt due to dependencies\n"
                    report.append(msg)
            else:
                report.append(msg)


    mod = len(ygh.modified) - rebuilt
    report.append('Summary:')
    report.append('Added Packages: %s' % len(ygh.add))
    report.append('Removed Packages: %s' % len(ygh.remove))
    report.append('Modified Packages: %d' % mod)
    if rebuilds:
        report.append('Rebuilt Packages: %s' % rebuilt)
    if size:
        report.append('Size of added packages: %s' % add_sizechange)
        report.append('Size change of modified packages: %s' % total_sizechange)
        report.append('Size of removed packages: %s' % remove_sizechange)
    if commits:
        report.append('Count of OBS commits: %d' % commits)

    return "\n".join(report)

