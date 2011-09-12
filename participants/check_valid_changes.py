#!/usr/bin/python
""" Implements a simple changes file validator according to the
    common guidelines http://wiki.meego.com/Packaging/Guidelines#Changelogs

.. warning::
   Either the get_relevant_changelog or the get_changelog participant
   participants should have been run first to fetch the relevant changelog
   entries, or the full changelog


:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list of dict):
      submit request data structure :term:`actions`
      each action annotated with key "relevant_changelog" (in relevant mode)
      relevant changelogs are formatted as lists of entries (which are strings)

   changelog(string):
      full package changelog (in full mode)
      usually placed there by get_changelog participant

:term:`Workitem` params IN

:Parameters:
   using(string):
      Optional parameter to specify mode "relevant_changelog" or "full"
      Default is full

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if the changes files of all packages are valid, False otherwise.
"""

import re

def workitem_error(workitem, msg):
    """Convenience function for reporting unlikely errors."""
    workitem.error = msg
    workitem.fields.msg.append(msg)
    raise RuntimeError(msg)

class Expected(Exception):
    _ref = "http://wiki.meego.com/Packaging/Guidelines#Changelogs"

    def __init__(self, found, expected, lineno, line=None):
        super(Expected, self).__init__()
        self.found = found
        self.expected = expected
        self.lineno = lineno
        self.line = line

    def __str__(self):
        msg = ["\nFound unexpected %s at line %d, expected %s\n"
               % (self.found, self.lineno, ", ".join(self.expected))]
        if self.line:
            msg.append(self.line)
        msg.append("\nplease follow ref at %s" % self._ref)
        return "".join(msg)

class Invalid(Exception):
    _ref = "http://wiki.meego.com/Packaging/Guidelines#Changelogs"

    def __init__(self, invalid, missing=None, lineno=None, line=None):
        super(Invalid, self).__init__()
        self.invalid = invalid
        self.missing = missing
        self.lineno = lineno
        self.line = line

    def __str__(self):
        if self.missing:
            msg = ["\nInvalid %s at line %d, maybe missing %s\n"
                   % (self.invalid, self.lineno, self.missing)]
        else:
            msg = ["\nInvalid %s at line %d\n" % (self.invalid, self.lineno)]
        if self.line:
            msg.append(self.line)
        msg.append("\nplease follow ref at %s" % self._ref)
        return "".join(msg)

class Validator(object):
    header_re = re.compile(r"^\* +(?P<date>\w+ +\w+ +\w+ +\w+) (?P<author>[^<]+)? ?(?P<email><.*>)?(?P<hyphen> *\-)? *(?P<version>[^ ]+)? *$")
    header_groups = ["date", "author", "email", "hyphen", "version"]
    blank_re = re.compile(r"^$")
    body_re = re.compile(r"^[-\s]\s*\S.*$")

    after_header = ["body"]
    after_blank = ["EOF", "header","blank"]
    after_body = ["blank", "EOF", "body"]
    initial_expect = ["header"]

    def validate(self, changes):
        lineno = 0
        changes = changes.split("\n")
        for line in changes:
            lineno = lineno + 1
            line = line.rstrip("\n")
            if line.startswith("*"):
                # changelog header
                if "header" not in self.initial_expect:
                    raise Expected("header", self.initial_expect, lineno=lineno)

                header = self.header_re.match(line)
                if not header:
                    raise Invalid("header", lineno=lineno, line=line)

                for group in self.header_groups:
                    if not header.group(group):
                        raise Invalid("header", missing=group, lineno=lineno, line=line)

                    expect = self.after_header
                    continue

            if self.blank_re.match(line):
                if "blank" not in expect:
                    raise Expected("blank", expect, lineno=lineno, line=line)
                expect = self.after_blank
                continue

            if self.body_re.match(line):
                if "body" not in expect:
                    raise Expected("body", expect, lineno=lineno, line=line)
                expect = self.after_body
                continue

class ParticipantHandler(object):
    """Participant class as defined by the SkyNET API"""

    def __init__(self):
        self.obs = None
        self.oscrc = None
        self.validator = Validator()

    def handle_wi_control(self, ctrl):
        """Job control thread"""
        pass

    def handle_lifecycle_control(self, ctrl):
        """Handle messages for the participant itself, like start and stop."""
        pass

    def check_changelog(self, wid, changelog):
        try:
            self.validator.validate(changelog)
        except (Invalid, Expected), exp:
            wid.fields.msg.append(str(exp))
            return False
        return True

    def check_relevant_changelogs(self, wid, actions):
        result = True
        for action in actions:
            changes = action.get('relevant_changelog', None)
            if changes is None:
                wid.fields.msg.append("Missing relevant_changelog for"
                                      " package %s" % action['sourcepackage'])
                result = False
                continue

            # merge ces list into one string
            changelog = "\n".join(changes)
            if not self.check_changelog(wid, changelog):
                result = False
        return result

    def handle_wi(self, wid):
        """Handle a workitem: do the quality check."""

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        using = wid.params.using or "full"

        if using == "relevant_changelog":
            if not wid.fields.ev or wid.fields.ev.actions is None:
                workitem_error(wid, "Mandatory field: ev.actions missing.")
            result = self.check_relevant_changelogs(wid, wid.fields.ev.actions)
        elif using == "full":
            if not wid.fields.changelog:
                workitem_error(wid, "Mandatory field: changelog missing.")
            result = self.check_changelog(wid, wid.fields.changelog)
        else:
            workitem_error(wid, "Unknown mode %s" % using)

        if not result:
            wid.fields.status = "FAILED"
            wid.fields.__error__ = "Some changelogs were invalid or missing"

        wid.result = result
