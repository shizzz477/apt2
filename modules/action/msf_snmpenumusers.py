import re

from core.actionModule import actionModule
from core.keystore import KeyStore as kb
from core.mymsf import myMsf
from core.utils import Utils


class msf_snmpenumusers(actionModule):
    def __init__(self, config, display, lock):
        super(msf_snmpenumusers, self).__init__(config, display, lock)
        self.triggers = ["snmpCred"]
        self.requirements = ["msfconsole"]
        self.title = "Enumerate Local User Accounts Using LanManager/psProcessUsername OID Values"
        self.shortName = "MSFSNMPEnumUsers"
        self.description = "execute [auxiliary/scanner/snmp/snmp_enumusers] on each target"
        self.safeLevel = 5

    def getTargets(self):
        # we are interested only in the hosts that have UDP 161 open
        self.targets = kb.get('host/*/vuln/snmpCred')

    def process(self):
        # load any targets we are interested in
        self.getTargets()

        if len(self.targets) > 0:
            # connect to msfrpc
            msf = myMsf(host=self.config['msfhost'], port=int(self.config['msfport']), user=self.config['msfuser'],
                        password=self.config['msfpass'])

            if not msf.isAuthenticated():
                return

            # loop over each target
            for t in self.targets:
                # verify we have not tested this host before
                if not self.seentarget(t):
                    # add the new IP to the already seen list
                    self.addseentarget(t)
                    self.display.verbose(self.shortName + " - Connecting to " + t)
                    # Get list of working community strings for this host
                    comStrings = kb.get("host/" + t + "/vuln/snmpCred/communityString")
                    for comString in comStrings:
                        msf.execute("use auxiliary/scanner/snmp/snmp_enumusers\n")
                        msf.execute("set RHOSTS %s\n" % t)
                        msf.execute("set COMMUNITY %s\n" % comString)
                        msf.execute("run\n")
                        msf.sleep(int(self.config['msfexploitdelay']))
                        result = msf.getResult()
                        while (re.search(".*execution completed.*", result) is None):
                            result = result + msf.getResult()

                        outfile = self.config["proofsDir"] + self.shortName + "_" + t + "_" + Utils.getRandStr(10)
                        Utils.writeFile(result, outfile)
                        kb.add("host/" + t + "/files/" + self.shortName + "/" + outfile.replace("/", "%2F"))

                        # Extract usernames from results and add to KB
                        parts = re.findall(".* users: .*", result)
                        for part in parts:
                            userlist = (part.split(':')[2]).split(',')
                            for username in userlist:
                                kb.add("host/" + t + "/user/" + username.strip())

            # clean up after ourselves
            result = msf.cleanup()

        return
