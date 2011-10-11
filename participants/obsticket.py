#!/usr/bin/python

"""
This ParticipantHandler can be installed into skynet::

  skynet make_participant -n obsticket -p <path>

This participant provides a locking mechanism for processes. It is
aimed at cooperatively locking OBS projects but can be used for any
exclusive process lock.

A nice idiom is::

  define 'with_OBS_ticket' do
    sequence do
      obsticket :action => 'get', :lock_project => '${project}'
      apply
      obsticket :action => 'release', :lock_project => '${project}'
    end
  end

Which allows::

  with_OBS_ticket do
    task1
    task2
  end

"""

import os, json
from RuoteAMQP import Workitem 

class QueueEmpty(Exception):
    pass

class QueueNoNext(Exception):
    pass

class QueueNotBusy(Exception):
    pass

class WorkQueue(object):

    def __init__(self, queuename):
        """
        queuename is the base filename which all the .xxx & .curr &
        .tail files will be built on.
        """
        self.base = queuename
        tail_pointer = self.base + ".tail"
        if not os.path.exists(tail_pointer):
            self._settail(0)
            self._setcurr(0)
        self.curr = self._getcurr()
        self.tail = self._gettail()


    def head(self):
        """
        Returns the head of the Q or throws a QueueEmpty
        """
        if self.isquiet():
            raise QueueEmpty()

        qcurr = self.base + "." + str(self.curr)
        assert os.path.exists(qcurr)
        qt = open(qcurr, "r")
        data = qt.read()
        qt.close()
        return data


    def isquiet(self):
        "If the Q is quiet"
        return (True if (self.tail == self.curr) else False)

    def add(self, data):
        """
        Stores data onto the Q.  If the Q is quiet, returns true
        indicating that work can commence.
        """
        wasquiet = True if (self.tail == self.curr) else False

        # Assert the queue is clean
        qtail = self.base + "." + str(self.tail)
        print "creating %s" % qtail
        assert not os.path.exists(qtail)
        qt = open(qtail, "w")
        qt.write(data)
        qt.close()

        # Where does the next item go
        self.tail += 1
        self._settail(self.tail)

        return wasquiet

    def next(self):
        """
        If there is a next workitem, promotes it to the head of the Q
        and returns it.
        Throws QueueNoNext if the Q is empty before the promotion.
        Throws QueueEmpty if the Q is empty after the promotion.
        """
        if self.isquiet():
            raise QueueNoNext()

        # Delete old item
        qcurr = self.base + "." + str(self.curr)
        os.unlink(qcurr)

        # Next item
        self.curr += 1
        self._setcurr(self.curr)

        return self.head()

    def _setcurr(self, ticket):
        "Private. Set the current ticket"
        f = open(self.base + ".curr", "w")
        f.write(str(ticket))
        f.close()

    def _getcurr(self):
        "Private. Get the current ticket"
        f = open(self.base + ".curr", "r")
        return int(f.read())

    def _settail(self, ticket):
        "Private. Set the tail ticket"
        f = open(self.base + ".tail", "w")
        f.write(str(ticket))
        f.close()

    def _gettail(self):
        "Private. Get the tail ticket"
        f = open(self.base + ".tail", "r")
        return int(f.read())

class ParticipantHandler(object):
    "The Exo class wraps around this handler."

    def __init__(self):
        self.prjdir = None

    def send_to_engine(self, wi):
        """ Will get replaced by the EXO using a closure """
        pass

    def get_ticket(self, wid, project):
        """
        This locks an OBS project by putting the wi into the work queue.

        If the queue is busy:
             Return without sending wi to BOSS, blocking process
        Otherwise:
             Send wi to BOSS and allow process to continue

        """

        path = os.path.join(self.prjdir, project)
        q = WorkQueue(path)

        if not q.add(json.dumps(wid.to_h(), sort_keys=True, indent=4)):
            # Marking the wid to be forgotten ensures it's not sent
            # back to BOSS
            wid.forget = True

    def release_ticket(self, wid, project):
        """
        This unlocks an OBS project by moving along the work queue.
        If the queue is quiet it raises an exception

        # The Q.head.wfid is compared to the current wfid. If they
        # differ an exception is raised. NOT YET.

        The current wi is sent to BOSS to allow this process to
        continue.

        The Q.head wi is deleted and the new head is sent to BOSS to
        allow that process to continue (unblocking it)
        """

        path = os.path.join(self.prjdir, project)
        q = WorkQueue(path)

        head_wi = Workitem(q.head())
        if head_wi.wfid != wid.wfid:
            print "OUCH ... released the wrong lock"

        try:
            next_wid = Workitem(q.next())
            next_wid.result = True
            # Implementation is a bit convoluted but this just sends
            # the WI from the stack to BOSS
            self.send_to_engine(next_wid)
        except QueueEmpty:
            # That's OK, there's nothing waiting
            pass

    def handle_wi_control(self, ctrl):
        "Handle any special control actions"
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            self.prjdir = ctrl.config.get("obsticket", "prjdir")
#FIXME: Check it is writable and let errors get raised sooner than later

    def handle_wi(self, wid):
        "The bulk of the participant logic is handled here"

        wid.result = False

        if wid.fields.debug_dump:
            print wid.dump()

        if wid.fields.msg is None:
            wid.fields.msg = []

        for param in ["action", "lock_project"]:
            if not getattr(wid.params, param, None):
                wid.fields.__error__ = "Required parameter %s missing" % param
                wid.fields.msg.append(wid.fields.__error__)
                raise RuntimeError("Missing parameter")

        action = wid.params.action
        project = wid.params.lock_project

        if action == 'get':
            self.get_ticket(wid, project)
        elif action == 'release':
            self.release_ticket(wid, project)

        wid.result = True
