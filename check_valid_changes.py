#!/usr/bin/python
""" Implements a simple changes file validator according to the
    common guidlines http://wiki.meego.com/Packaging/Guidelines#Changelogs

.. warning::
   Either the get_relevant_changelog or the get_changelog participant
   participants should have been run first to fetch the relevant changelog
   entries, or the full changelog


:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`

:term:`Workitem` params IN

:Parameters:
   using(string):
      Optional parameter to specify which mode to use "relevant" or "full"

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if the changes files of all packages are valid, False otherwise.

"""

import re

class Expected(Exception):

    _ref = "http://wiki.meego.com/Packaging/Guidelines#Changelogs"

    def __init__(self, found, expected, lineno, line=None):
        super(Expected, self).__init__()
        self.found = found
        self.expected = expected
        self.lineno = lineno
        self.line = line

    def __str__(self):
        msg =  ["\nFound unexpected %s at line %d, expected %s\n" % (self.found,
                                                                 self.lineno,
                                                      ", ".join(self.expected))]
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
            msg = ["\nInvalid %s at line %d, maybe missing %s\n" % (
                                                                 self.invalid,
                                                                 self.lineno,
                                                                 self.missing)]
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

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None
        self.validator = None

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            self.validator = Validator()

    def quality_check(self, wid):

        """ Quality check implementation """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions
        changelog = wid.fields.changelog
        using = wid.params.using

        if using == "relevant_changelog":
            if not actions:
                wid.fields.__error__ = "Mandatory field: actions does not exist."
                wid.fields.msg.append(wid.fields.__error__)
                raise RuntimeError("Missing mandatory field")
        elif not changelog:
            wid.fields.__error__ = "Mandatory field: changelog does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        result = True
        for action in actions:
            changes = None
            if using == "relevant_changelog":
                changes = action['relevant_changelog']
                # merge ces list into one string
                changelog = "\n".join(changes)

            # Assert validity of changes
            try:
                self.validator.validate(changelog)
            except Invalid, exp:
                wid.fields.msg.append(str(exp))
                result = False
            except Expected, exp:
                wid.fields.msg.append(str(exp))
                result = False

        if not result:
            wid.fields.__error__ = "Some changelogs were invalid"

        wid.result = result

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.quality_check(wid)
