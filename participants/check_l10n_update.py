#!/usr/bin/python

""" Compares l10n translation level in a submit (promotion) request.
This check unpacks source and destination .ts files and compares every language.
Test will fail if any language brings translation level down or source package
is missing language that is already present in destination package.

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      Request data structure :term:`actions`
      The participant only looks at submit actions

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if all the submit actions in the request keep the translation
      level up and no languages are removed.
      Otherwise False

"""

from buildservice import BuildService
import shutil
from tempfile import mkdtemp
from boss.rpm import extract_rpm
from translate.storage import factory
import re
import os
from subprocess import check_output


def _make_ts_diff(old_ts_path, new_ts_path):
    old = factory.getobject(old_ts_path)
    new = factory.getobject(new_ts_path)

    # this is for added / removed
    old_ids = set(old.getids())
    new_ids = set(new.getids())
    added = new_ids - old_ids
    removed = old_ids - new_ids

    old_trans_count = 0
    for unit_id in old_ids:
        if old.findid(unit_id).istranslated():
            old_trans_count += 1

    new_trans_count = 0
    for unit_id in new_ids:
        if new.findid(unit_id).istranslated():
            new_trans_count += 1

    return {
        "old_trans_count" : old_trans_count,
        "new_trans_count" : new_trans_count,
        "old_units"      : len(old_ids),
        "new_units"      : len(new_ids),
        "added"          : list(added),
        "removed"        : list(removed),
        }


def _extract_tar(tar_file, target_dir):
    """Extarct tar_file in target_dir

    We call tar because python tarfile module has issues extracting some
    compressed archives.
    """
    tar_file = os.path.abspath(tar_file)
    output = check_output(
        ['tar', '-vxaf', tar_file],
        cwd=target_dir
    )
    return output.splitlines()


def _get_ts_files(file_list):
    """Filter .ts files from list and return language -> ts file dict

    Expects paths in format xxx/<lang>/yyy.ts
    """
    lang_files = {}
    for f in file_list:
        if not f.endswith('.ts'):
            continue
        lang = f.split(os.path.sep)[-2]
        lang_files[lang] = f
    return lang_files


class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")

    def setup_obs(self, namespace):
        """ setup the Buildservice instance using the namespace as an alias
            to the apiurl """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def get_l10n_stats(self, source_project, target_project, package):
        tmp_dir_old = mkdtemp()
        tmp_dir_new = mkdtemp()

        old_ts_dir = os.path.join(tmp_dir_old, "ts")
        new_ts_dir = os.path.join(tmp_dir_new, "ts")
        target = self.obs.getTargets(str(source_project))[0]

        # Get src.rpm as it contains all .ts files
        src_rpm = [rpm for rpm in self.obs.getBinaryList(
                source_project, target, package) if "src.rpm" in rpm]
        target_rpm = [rpm for rpm in self.obs.getBinaryList(
                target_project, target, package) if "src.rpm" in rpm]

        # Download source and target rpms
        old_src_rpm = os.path.join(tmp_dir_old, target_rpm[0])
        self.obs.getBinary(target_project, target, package, target_rpm[0],
                           old_src_rpm)
        new_src_rpm = os.path.join(tmp_dir_new, src_rpm[0])
        self.obs.getBinary(source_project, target, package, src_rpm[0],
                           new_src_rpm)

        # Extract rpms and get the source tarball names
        old_tar = [
            f for f in extract_rpm(old_src_rpm, tmp_dir_old)
            if '.tar' in f
        ][0]
        new_tar = [
            f for f in extract_rpm(new_src_rpm, tmp_dir_new)
            if '.tar' in f
        ][0]

        # Extract tarballs and get ts files per language
        old_tar = os.path.join(tmp_dir_old, old_tar)
        new_tar = os.path.join(tmp_dir_new, new_tar)
        old_ts_files = _get_ts_files(_extract_tar(old_tar, old_ts_dir))
        new_ts_files = _get_ts_files(_extract_tar(new_tar, old_ts_dir))

        old_langs = set(old_ts_files.keys())
        new_langs = set(new_ts_files.keys())

        l10n_stats = {
            "removed_langs": list(old_langs - new_langs),
            "added_langs": list(new_langs - old_langs),
            "removed_strings": [],
        }
        for key in new_langs & old_langs:
            _old_path = os.path.join(old_ts_dir, old_ts_files[key])
            _new_path = os.path.join(new_ts_dir, new_ts_files[key])
            unit_diff = _make_ts_diff(_old_path, _new_path)
            l10n_stats[key] = unit_diff

        # Check that -ts-devel package is not going out of sync
        src_pkg = package.replace("-l10n", "")

        # Is there a package that is using -l10n pakcage already
        src_pkg = [rpm for rpm in self.obs.getPackageList(target_project) if src_pkg ==  rpm]

        if len(src_pkg) > 0:
            #get -ts-devel rpm
            src_ts_devel_rpm = [rpm for rpm in self.obs.getBinaryList(target_project, target, src_pkg[0]) if "-ts-devel" in rpm]
            if len(src_ts_devel_rpm) > 0:
                tmp_dir_ts = mkdtemp()
                self.obs.getBinary(target_project, target, src_pkg[0], src_ts_devel_rpm[0], tmp_dir_ts + "/orig.rpm")
                orig_ts_file = extract_rpm(tmp_dir_ts + "/orig.rpm", tmp_dir_ts, patterns="*.ts")
                original_units = factory.getobject(tmp_dir_ts + "/" + orig_ts_file[0])
                new_units = factory.getobject(tmp_dir_new + "/ts/" + new_ts_files['templates'])
                removed_units = set(original_units.getids()) - set(new_units.getids())
                l10n_stats.update({"removed_strings" : list(removed_units)})
                shutil.rmtree(tmp_dir_ts)

        #get rid of tmp dirs
        shutil.rmtree(tmp_dir_old)
        shutil.rmtree(tmp_dir_new)

        return l10n_stats

    def handle_wi(self, wid):
        """ actual job thread """

        wid.result = True
        if not wid.fields.msg:
            wid.fields.msg =  []

        if not wid.fields.ev:
            raise RuntimeError("Missing mandatory field 'ev'")
        if not wid.fields.ev.namespace:
            raise RuntimeError("Missing mandatory field 'ev.namespace'")
        if not wid.fields.ev.actions:
            raise RuntimeError("Missing mandatory field 'ev.actions'")

        self.setup_obs(wid.fields.ev.namespace)
        tgt_pkg_list = self.obs.getPackageList(str(wid.fields.project))

        all_ok = True

        for action in wid.fields.ev.actions:
            if action['type'] != 'submit':
                continue
            # do the check only for l10n packages
            if not "-l10n" in action['sourcepackage']:
                continue

            if action['sourcepackage'] not in tgt_pkg_list:
                #nothing to diff, pass through
                continue

            msg = ""
            package_ok = True
            l10n_stats = self.get_l10n_stats(str(action['sourceproject']),
                                             str(action['targetproject']),
                                             str(action['sourcepackage']))
            #store stats for later use
            wid.fields.l10n = { "stats" : l10n_stats }

            # check if there is '<pkg> bypass' message
            if wid.fields.ev.description:
                re1 = re.compile(r'%s bypass' % action['sourcepackage'])
                if re1.search(wid.fields.ev.description):
                    continue

            for key, value in l10n_stats.items():
                # removed_langs & added_langs
                if "_langs" in key:
                    continue
                if "removed_strings" in key:
                    continue
                if "Instructions" in key:
                    continue

                old_translated = float(value["old_trans_count"])
                new_translated = float(value["new_trans_count"])
                old_units = value["old_units"]
                new_units = value["new_units"]
                added     = len(value["added"])

                # check that translation level does not go down. New strings can be added
                # without an effect
                if (old_translated / old_units ) > ((new_translated + added) / new_units):
                    all_ok = package_ok = False
                    msg += "%s level down from %.4f to %.4f" % (
                        key, old_translated/ old_units, (new_translated + added) / new_units)

            # check that already present languages are not removed
            if len(l10n_stats["removed_langs"]) > 0:
                all_ok = package_ok = False
                msg += "%s langs removed" % (", ".join(l10n_stats['removed_langs']))
            if not package_ok:
                wid.fields.msg.append("%(sourcepackage)s has following l10n error(s):" % action)
                wid.fields.msg.append(msg)

        wid.result = all_ok
