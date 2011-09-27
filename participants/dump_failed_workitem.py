#!/usr/bin/python
"""
Dumps a workitem in a configured filesystem store for test harness usage.

:term:`Workitem` fields IN:

:Parameters:
   wid:
      workitem id

:term:`Workitem` params IN

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if everything went OK and workitem was dumped. False otherwise.
   workitem_filename(string):
      Workitem file written to participant host machine.

"""

import os


class ParticipantHandler(object):
    """Participant class as defined by the SkyNET API."""

    def __init__(self):
        self.workitem_path = None

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        if ctrl.message == "start":
            if ctrl.config.has_option("dump_failed_workitem", "path"):
                self.workitem_path = ctrl.config.get("dump_failed_workitem", "path")

    def write_workitem(self, wid):
        """
        Write a workitem to a file and return the filename if successfull, 
        "NO PATH" string otherwise.
        
        :Parameter:
            wid:
                The whole workitem to write to a file.
        """
        if not wid.result == False:
            raise RuntimeError("You must submit only failed workitems!")
        else:
            workitem_file = []
            if wid.fields.project:
                workitem_file.append(wid.fields.project)
                workitem_file.append("_")
            if wid.fields.time:
                workitem_file.append(wid.fields.time)
                workitem_file.append("_")
            if wid.fields.id:
                workitem_file.append("-SR-#%s-"%wid.fields.id)
            if wid.fields.type:
                workitem_file.append(wid.fields.type)
            if len(workitem_file) > 1:
                final_path = os.path.join(self.workitem_path, "".join(workitem_file))
            else:
                return "NO PATH"
            with open(final_path, 'w') as f:
                f.write(wid.dump())
                f.close()
            return final_path

    def handle_wi(self, wid):
        """Actual job thread."""

        # We may want to examine the fields structure
        if wid.fields.debug_dump:
            print wid.dump()
        workitem_filename = self.write_workitem(wid)
        if workitem_filename != "NO PATH":
            wid.result = True
            wid.fields.workitem_filename = workitem_filename
        else:
            wid.result = False

