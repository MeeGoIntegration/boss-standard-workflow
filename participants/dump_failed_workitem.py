#!/usr/bin/python
"""
Dumps a workitem in a configured filesystem store for test harness usage.

NOTE: Please clean up the workitems when no longer needed.

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
                self.workitem_path = ctrl.config.get("dump_failed_workitem",
                                                     "path")

    def write_workitem(self, wid):
        """
        Write a workitem to a file and return the filename if successfull, 
        exception otherwise.
        
        :Parameter:
            wid:
                The whole workitem to write to a file.
        """
        if not wid.result == False:
            raise RuntimeError("You must submit only failed workitems!")
        else:
            workitem_file = []
            if wid.fields.ev.project:
                workitem_file.append(wid.fields.ev.project)
                workitem_file.append("_")
            if wid.fields.ev.time:
                workitem_file.append(wid.fields.ev.time)
                workitem_file.append("_")
            if wid.fields.ev.id:
                workitem_file.append("SR-#%s-"%wid.fields.ev.id)
            if wid.fields.ev.type:
                workitem_file.append(wid.fields.ev.type)

            if len(workitem_file) > 1:
                final_path = os.path.join(self.workitem_path, 
                                          "".join(workitem_file))
                with open(final_path, 'w') as workitem_f:
                    workitem_f.write(wid.dump())
                    workitem_f.close()
                return final_path
            raise RuntimeError("Path too short!")

    def handle_wi(self, wid):
        """Actual job thread."""
        wid.result = False
        workitem_filename = self.write_workitem(wid)
        if workitem_filename:
            wid.result = True
            wid.fields.workitem_filename = workitem_filename

