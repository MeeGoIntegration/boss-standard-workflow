#!/usr/bin/python

"""
The request_notice participant is a minimal participant that is used by
the standard workflow to allow a process to block until a request is
changed.

It is started as normal:

skynet enable request_notice

It should be registered as follows:

skynet register -r req_changed_\.\* -q request_notice

This ensures it handles any process step beginning with "req_changed_"

Usage:
======

Normal use is to invoke it when a request state change is detected.
This is typically done in ruote like:

ref 'req_changed_${ev.id}'

Since this participant is registerd to the regexp 'req_changed_.*' it will
handle that step and simply print a notice to the log.

Meanwhile the process waiting for a request change event is doing:

listen :to => 'req_changed_${ev.id}', :upon => 'reply'

When this participant returns, the waiting process will simply
continue.
"""

class ParticipantHandler(object):

    def handle_wi_control(self, ctrl):
        pass

    def handle_lifecycle_control(self, ctrl):
        pass

    def handle_wi(self, wi):

        print "This is the request notice for %s" % wi.fields.ev.id
