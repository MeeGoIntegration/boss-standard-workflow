#!/usr/bin/python
""" This participant is used to select extra packages that are added to an image
according to its definition. Currently only "testing" images can be defined.
To define a testing image for a set of packages (persumably being promoted) any
<packagename>-tests binary package produced by them are selected.
In addition their reverse dependencies are worked out and then all
<packagename>-tests binary packages produced by them are also selected.

:term:`Workitem` fields IN

:Parameters:
   test_project(string):
      The test project which contains the packages going to be tested
   repository(string):
      The repository in above said project
   image.arch(string):
      The arch of the image going to be built
   image.packages(list):
      Names of packages going to be tested


:term:`Workitem` params IN

:Parameters:
   image_type(string):
      The type of image to be defined (only "testing" for now)

:term:`Workitem` fields OUT

:Returns:
   result(boolean):
      True if everything was OK, False otherwise.
   image.packages(list):
      Extends the list of packages going to be included in the image

"""
from buildservice import BuildService

def select_subpkgs(subpkgs, package):
    """This function implements selection of test packages from a list of
    packages based on the packagename-tests naming convention

    :param subpkgs: the packages to select from
    :type subpkgs: list

    :param package: the name of the package that is going to be tested
    :type package: string
    """

    selected = []
    for bpk in subpkgs:
        if bpk.endswith('-debuginfo'):
            continue
        if bpk.endswith('-devel'):
            continue
        if bpk.endswith('-doc'):
            continue
        if bpk.endswith('-tests'):
            if package.endswith('-tests') and bpk == package:
                selected.append(bpk)
                continue
            if bpk == package + '-tests':
                selected.append(bpk)
                continue
            if bpk == package + '-unit-tests' :
                selected.append(bpk)
                continue
        selected.append(bpk)
    return selected

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None
        self.image_options = {}

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")
            if ctrl.config.has_option("defineimage", "imagetypes"):
                image_types = ctrl.config.get("defineimage",
                                              "imagetypes").split(',')
                for itype in image_types:
                    self.image_options[itype] = dict(ctrl.config.items(itype))

    def setup_obs(self, namespace):
        """ setup the Buildservice instance using the namespace as an alias
            to the apiurl """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def handle_wi(self, wid):
        """ actual job thread """
        wid.result = False

        itype = wid.params.image_type

        if not wid.fields.msg:
            wid.fields.msg = []

        if not itype:
            wid.fields.__error__ = "Parameter image_type not specified"
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing parameter")

        if not itype in self.image_options.keys() :
            wid.fields.__error__ = "Invalid image_type parameter %s" % itype
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Invalid parameter value")

        for fname in ["test_project", "repository", "image"]:
            if not getattr(wid.fields, fname, None):
                wid.fields.__error__ = "Field %s not specified" % fname
                wid.fields.msg.append(wid.fields.__error__)
                raise RuntimeError("Missing field")

        for fname in ["packages", "arch"]:
            if not getattr(wid.fields.image, fname, None):
                wid.fields.__error__ = "Field image.%s not specified" % fname
                wid.fields.msg.append(wid.fields.__error__)
                raise RuntimeError("Missing field")

        self.setup_obs(wid.fields.ev.namespace)

        if itype == "testing":
            prj = wid.fields.test_project
            repo = wid.fields.repository
            arch = wid.fields.image.arch
            packages = wid.fields.image.packages

            # get reverse dependencies of each package
            additional_pkgs = []
            for pkg in packages:
                for pkg_revdep in self.obs.getPackageReverseDepends(prj, repo,
                                                                    pkg, arch):
                    if pkg_revdep not in additional_pkgs:
                        additional_pkgs.append(pkg_revdep)

            packages.extend(additional_pkgs)

            # get subpackages of each package and select the ones we are
            # interested in
            selected = []
            for pkg in packages :
                pkg_subpkgs = self.obs.getPackageSubpkgs(prj, repo, pkg, arch)
                subpkgs = select_subpkgs(pkg_subpkgs, pkg)
                for subpkg in subpkgs:
                    if subpkg not in selected:
                        selected.append(subpkg)

            if "always_include" in self.image_options[itype]:
                for inc in self.image_options[itype]["always_include"]\
                                                .split(','):
                    if inc and inc not in selected:
                        selected.append(inc)

            wid.fields.image.packages.extend(selected)

            wid.fields.msg.append('Defined %s image includes %s' %
                                            (itype, (", ").join(selected)))

        wid.result = True
