try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from core.actionModule import actionModule
from core.keystore import KeyStore as kb
from core.mynmap import mynmap


class nmapsmbshares(actionModule):
    def __init__(self, config, display, lock):
        super(nmapsmbshares, self).__init__(config, display, lock)
        self.title = "NMap SMB Share Scan"
        self.shortName = "NmapSMBShareScan"
        self.description = "execute [nmap -p445 --script=smb-enum-shares] on each target"

        self.requirements = ["nmap"]
        self.triggers = ["newPort445"]

        self.safeLevel = 5

    def getTargets(self):
        self.targets = kb.get(['host/*/tcpport/139', 'host/*/tcpport/445'])

    def process(self):
        # load any targets we are interested in
        self.getTargets()

        # loop over each target
        for t in self.targets:
            # verify we have not tested this host before
            if not self.seentarget(t):
                # add the new IP to the already seen list
                self.addseentarget(t)
                self.display.verbose(self.shortName + " - Connecting to " + t)
                # run nmap
                n = mynmap(self.config, self.display)
                scan_results = n.run(target=t, flags="--script=smb-enum-shares", ports="445", vector=self.vector,
                                     filetag=t + "_SMBSHARESCAN")['scan']

                tree = ET.parse(n.outfile + '.xml')
                root = tree.getroot()
                for table in root.iter('table'):
                    sharename = table.attrib["key"]
                    for elem in table:
                        if elem.text is not None:
                            kb.add("host/" + t + "/shares/SMB/" + sharename + "/" + str(elem.attrib['key'] + ": " + elem.text).replace("/", "%2F"))

        return
