################################################################################
#
# MELT Core Library
#
# Methods to facilitate processing gcode.
#
# Usage:
#   Creating a mix:
#       mix = Miso.Mix([0.5,0.5,0.5,0.5])
#
#   Configuring a tool:
#       tool = Miso.Tool([mix])
#       Miso.setToolConfig(0, tool) # sets this mix for tool 0
#
#   Configuring a gradient:
#       gradientStart = Miso.Mix([0.1,0.1,0.1,0.1], 0.25)
#       gradientStop = Miso.Mix([0.9,0,0,0], 0.75)
#       tool = Miso.Tool([gradientStart, gradientStop])
#       Miso.setToolConfig(2, tool) # sets this gradient for tool 2
#
#   Converting gcode:
#       maxZHeight = maxHeightOfPrint
#       newcode = Miso.fromGcode(gcode, maxZHeight)
#
################################################################################

import re

class Miso:
    # Hash of ToolConfigurations
    # Allows extruder mixes to be assigned to different tools
    _toolConfigs = {}

    @staticmethod
    def setToolConfig(toolId, toolConfig):
        Miso._toolConfigs[toolId] = toolConfig

    @staticmethod
    def getToolConfig(toolId):
        if toolId in Miso._toolConfigs:
            return Miso._toolConfigs[toolId]
        return Miso.Tool() #default

    # Forward-reading modification of gcode here
    # tracks tool changes, z changes, and relative / absolute changes
    # When an extrusion command is found and any of this info has changed
    # then a new mix command is written
    @staticmethod
    def fromGcode(gcode, zmax):
        tool = 0
        toolHistory = tool
        zpos = 0
        zposHistory = zpos
        relative = False
        relativeHistory = relative
        newcode = ''
        for line in gcode:
            tool = Miso.Gcode.updateTool(line, tool)
            zpos = Miso.Gcode.updateZ(line, zpos, relative)
            relative = Miso.Gcode.updateRelative(line, relative)
            isDirty = tool != toolHistory or zpos != zposHistory or relative != relativeHistory
            if isDirty and Miso.Gcode.isExtrude(line):
                toolHistory = tool
                zposHistory = zpos
                relativeHistory = relative
                newcode += Miso.Gcode.formatMix(tool, zpos, zmax) + "\n"
            newcode += line + '\n'
        return newcode

    # Miso.Tool
    # Mix and gradient information for a specific tool
    # Example:
    #   toolConfig = Miso.Tool([mix1, mix2, ...])
    class Tool:
        def __init__(self, stops=None):
            stops = stops or [Miso.Mix()]
            self.stops = {}
            for stop in stops:
                self.stops[stop.zstop] = stop.mix

    # Miso.Mix
    # Mix information for a single stop (layer)
    # Z is expressed in percentage (0 to 1)
    # extruders is an array of percentages (0 to 1)
    class Mix:
        def __init__(self, mix=[1], zstop=0):
            self.mix = mix
            self.zstop = zstop

    # Miso.Gcode
    # Methods that help read and generate gcode
    class Gcode:
        _movecodes = re.compile('^\\s*(G0|G1).+Z(?P<distance>\\d+)\\b')
        _extrudecodes = re.compile('^\\s*(G0|G1|G2|G3).+(E|F)\\d+\\b')
        _toolcodes = re.compile('^\\s*T(?P<toolid>\\d+)\\b')
        _absolutecodes = re.compile('^\\s*G91\\b')
        _relativecodes = re.compile('^\\s*G90\\b')

        @staticmethod
        def updateRelative(line, current):
            if Miso.Gcode._relativecodes.match(line):
                return True
            if Miso.Gcode._absolutecodes.match(line):
                return False
            return current

        @staticmethod
        def updateTool(line, current):
            match = Miso.Gcode._toolcodes.search(line)
            if match:
                return int(match.group('toolid'))
            return current

        @staticmethod
        def updateZ(line, current, relative):
            match = Miso.Gcode._movecodes.search(line)
            if match and relative:
                change = float(match.group('distance'))
                return current + change
            if match:
                return float(match.group('distance'))
            return current

        @staticmethod
        def isExtrude(line):
            return Miso.Gcode._extrudecodes.match(line)

        @staticmethod
        def formatMix(tool, zpos, zmax):
            index = zpos / zmax
            mix = Miso.Gcode._calcMix(index, tool)
            for i in range(len(mix)):
                mix[i] = Miso.Gcode._formatNumber(mix[i])
            return 'M567 P' + str(tool) + ' E' + ':'.join(mix)

        @staticmethod
        def _calcMix(index, tool):
            segment = Miso.Gcode._calcSegment(index, tool)
            srange = segment.keys()
            if len(srange) == 0:
                return [1]
            if len(srange) == 1:
                return segment[srange[0]]
            index = (index - min(srange[0], srange[1])) / (max(srange[0], srange[1])-min(srange[0], srange[1]))
            mix = []
            start = segment[min(srange[0], srange[1])]
            end = segment[max(srange[0], srange[1])]
            for extruder in range(max(len(start), len(end))):
                svalue = len(start) < extruder and start[extruder] or 0
                evalue = len(end) < extruder and end[extruder] or 0
                mix.append((evalue - svalue) * index + svalue)
            return mix

        @staticmethod
        def _calcSegment(index, tool):  # NOTE: this will allow mixes that total more than 1
            stops = Miso.getToolConfig(tool).stops
            start = None
            end = None
            for stop in stops.keys():  # TODO: If stop is 0 there will be a bug
                start = stop <= index and (start != None and max(start, stop) or stop) or start
                end = stop >= index and (end != None and max(end, stop) or stop) or end
            segment = {}
            if start:
                segment[start] = stops[start]
            if end:
                segment[end] = stops[end]
            return segment

        @staticmethod
        def _formatNumber(value):
            value = str(value).strip()
            if re.match('^\\.', value):
                value = '0' + value
            filter = re.search('\\d+(\\.\\d{1,2})?', value)
            if not filter:
                return '0'
            return filter.string[filter.start():filter.end()]
