#!/usr/bin/python

"""
The built_notice participant is a minimal participant that is used by
the standard workflow to allow a process to block until an event is
received.

It is started as normal::

    skynet enable built_notice

It should be registered as follows::

    skynet register -n built_\.\* -q built_notice

This ensures it handles any process step beginning with "`built_`"

Usage:
======
When project Project:CE:Trunk is determined to be built, a process
step of

built_Project:CE:Trunk

is invoked. This is typically done in ruote like:

ref 'built_${project}'

Since this participant is registerd to the regexp `built_.*` it will
handle that step - and simply self.log.info(a notice to the log.)

Meanwhile the process waiting for a build event is doing:

listen :to => 'built_${trial_project}', :upon => 'reply'

When this participant returns, the waiting process will simply
continue.
"""

class ParticipantHandler(object):

    def handle_wi_control(self, ctrl):
        pass

    def handle_lifecycle_control(self, ctrl):
        pass

    def handle_wi(self, wi):
        self.log.info("This is the built notice for ", wi.fields.project)
