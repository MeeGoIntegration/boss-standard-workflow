"""Used to trigger service of an OBS project / package :

:term:`Workitem` fields IN:

:Parameters:
   :ev.namespace (string):
      Used to contact the right OBS instance.
   :package (string):
      Package name to be rebuilt
   :project (string):
      OBS project in which the package lives
   
   
:term:`Workitem` params IN

:Parameters:
   :package (string):
      Package name to be rebuilt, overrides the package field
   :project (string):
      OBS project in which the package lives, overrides the project field

:term:`Workitem` fields OUT:

:Returns:
   :result (Boolean):
      True if the everything went OK, False otherwise

"""

from boss.obs import BuildServiceParticipant
import osc

service = """
<services>
  <service name="tar_git">
    <param name="url">%(url)s</param>
    <param name="branch">%(branch)s</param>
    <param name="revision">%(revision)s</param>
  </service>
</services>
"""

class ParticipantHandler(BuildServiceParticipant):
    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ Workitem handling function """
        wid.result = False
        f = wid.fields
        p = wid.params

        project = None
        package = None

        if f.project and f.package:
            project = f.project
            package = f.package

        if p.project and p.package:
            project = p.project
            package = p.package

        if not project or not package:
           raise RuntimeError("Missing mandatory field or parameter: package, project")

        if not f.repourl and not p.repourl:
           raise RuntimeError("Missing mandatory field or parameter: repourl")

        params = { "url" : f.repourl }

        if p.repourl:
            params["url"] = p.repourl
        if f.branch:
            params["branch"] = f.branch
        if p.branch:
            params["branch"] = p.branch
        if f.revision:
            params["revision"] = f.revision
        if p.revision:
            params["revision"] = p.revision

        if self.obs.isNewPackage(project, package):
            self.obs.getCreatePackage(project, package)
        
        self.obs.setupService(project, package, service % params)

        wid.result = True
