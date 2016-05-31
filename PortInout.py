from Port import *

class PortInout(Port):

    def __init__(self, attrs):
        attrs["direction"] = "inout"
        Port.__init__(self, attrs)

    # link the port!
    def link(self, net):
        net.addFanout(self)
        Port.link(self, net)
