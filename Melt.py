# Credits for contributions
# gargansa, bass4aj, kenix, laraeb, datadink, keyreaper

from ..Script import Script
import random



# Convenience function for gargansa's coding familiarity
def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


# Function to compile the initial setup into a string
def initiate_extruder(existing_gcode, *gcode):
    setup_line = ""
    setup_line += existing_gcode
    for line in gcode:
        if line != str(""):
            setup_line += "\n" + str(line) #+ "\n"

    return setup_line


# Function to compile extruder info into a string
def adjust_extruder_rate(existing_gcode, *ext):
    i = 0
    for item in ext:
        if i == 0:
            setup_line = existing_gcode + "\nM567 P0 E" + str(item)
        else:
            setup_line += ":" + str(item)
        i += 1
    setup_line += "\n"
    return setup_line


# Just used to output info to text file to help debug
def print_debug(*report_data):
    setup_line = ";Debug "
    for item in report_data:
        setup_line += str(item)
    setup_line += "\n"
    return setup_line


class Melt(Script):
    version = "4.0.0"

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Multi-Extruder Layering Tool """ + self.version + """ (MELT)",
            "key":"Melt",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "firmware_type":
                {
                    "label": "Firmware Type",
                    "description": "Type of Firmware Supported.",
                    "type": "enum",
                    "options": {"duet":"Duet"},
                    "default_value": "duet"
                },
                "qty_extruders":
                {
                    "label": "Number of extruders",
                    "description": "How many total extruders in mixing nozzle.",
                    "type": "enum",
                    "options": {"2":"Two","3":"Three","4":"Four"},
                    "default_value": "2"
                },
                "affected_tool":
                {
                    "label": "Tool Affected",
                    "description": "Which Tool(Part) to Apply Color or Effect.",
                    "type": "enum",
                    "options": {"T0":"All","T1":"T1","T2":"T2","T3":"T3","T4":"T4"},
                    "default_value": "T0"
                },
                "effect_type":
                {
                    "label": "Blend or Effect",
                    "description": "Choose whether to apply a stationary blend to the tool or an effect such as a gradient",
                    "type": "enum",
                    "options": {"blend":"Define Blend","effect":"Changing Effect"},
                    "default_value": "blend"
                },
                "unit_type":
                {
                    "label": "Unit Type",
                    "description": "Percentage or Layer# Unit.",
                    "type": "enum",
                    "options": {"percent":"Percentage","layer_no":"Layer No."},
                    "default_value": "percent"
                },
                "percent_change_start":
                {
                    "label": "Location % Start",
                    "description": "Percentage location of layer height to begin effect.",
                    "unit": "%",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "99",
                    "enabled": "unit_type == 'percent'"
                },
                "percent_change_end":
                {
                    "label": "Location % End",
                    "description": "Percentage location of layer height to end effect.",
                    "unit": "%",
                    "type": "float",
                    "default_value": 100,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "minimum_value_warning": "1",
                    "maximum_value_warning": "100",
                    "enabled": "unit_type == 'percent' and effect_type == 'effect'"
                },
                "layer_change_start":
                {
                    "label": "Location # Start",
                    "description": "Layer location to begin effect.",
                    "unit": "#",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": "0",
                    "enabled": "unit_type == 'layer_no'"
                },
                "layer_change_end":
                {
                    "label": "Location # End",
                    "description": "Layer location to end effect.",
                    "unit": "#",
                    "type": "int",
                    "default_value": 100000,
                    "minimum_value": "0",
                    "enabled": "unit_type == 'layer_no' and effect_type == 'effect'"
                },
                "blend_values":
                {
                    "label": "Values",
                    "description": "What percentage values to set the extruder blend. Must add up to 100%",
                    "type": "str",
                    "default_value": "100,0,0,0",
                    "enabled": "effect_type == 'blend'"
                },
                "rotation_order":
                {
                    "label": "Extruder Rotation",
                    "description": "The order in which the shift moves through the extruders. Example 'ca' starts the shift at extruder c and moves towards extruder a. If only shifting through two layers list only those two. Must be lowercase. Must be at least two letters or it will default to ab",
                    "type": "str",
                    "default_value": "abcd",
                    "enabled": "effect_type == 'effect'"
                },
                "extruder_start":
                {
                    "label": "Extruder begin clamp",
                    "description": "The beginning percentage to start extruder.",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "effect_type == 'effect'"
                },
                "extruder_end":
                {
                    "label": "Extruder end clamp",
                    "description": "The ending percentage to end extruder.",
                    "type": "float",
                    "default_value": 100,
                    "enabled": "effect_type == 'effect'"
                },
                "change_rate":
                {
                    "label": "Effect Change frequency",
                    "description": "How many layers until the color is shifted each time.",
                    "unit": "#",
                    "type": "int",
                    "default_value": 4,
                    "minimum_value": "0",
                    "maximum_value": "1000",
                    "minimum_value_warning": "1",
                    "maximum_value_warning": "100",
                    "enabled": "effect_type == 'effect'"
                },
                "effect_modifier":
                {
                    "label": "Modifier Type",
                    "description": "::Normal: Sets the shift to change gradually throughout the length of the layers within the clamp. ::Wood Texture: Sets one extruder at a random small percentage and adjusts change frequency by a random amount, simulating wood grain. ",
                    "type": "enum",
                    "options": {"normal":"Normal", "wood":"Wood Texture", "random":"Random"},
                    "default_value": "normal",
                    "enabled": "effect_type == 'effect'"
                },
                "rate_modifier":
                {
                    "label": "Rate Modifier Type",
                    "description": "How often the print shifts. ::Normal: Uses the change rate.  ::Random: picks a number of layers between the set change_rate and change_rate*2",
                    "type": "enum",
                    "options": {"normal":"Normal", "random":"Random"},
                    "default_value": "normal",
                    "enabled": "effect_type == 'effect'"
                }
            }
        }"""

    def execute(self, data: list):  # used to be data: list

        qty_extruders = int(self.getSettingValueByKey("qty_extruders")) #"2":"Two","3":"Three","4":"Four"
        affected_tool = str(self.getSettingValueByKey("affected_tool")) #"All":"All","T0":"T0","T1":"T1","T2":"T2","T3":"T3"
        effect_type = str(self.getSettingValueByKey("effect_type")) #"blend":"Define Blend","effect":"Changing Effect"
        unit_type = str(self.getSettingValueByKey("unit_type")) #"percent":"Percentage","layer_no":"Layer No."
        percent_change_start = float(self.getSettingValueByKey("percent_change_start") / 100) #0-100
        percent_change_end = float(self.getSettingValueByKey("percent_change_end") / 100) #0-100
        layer_change_start = int(self.getSettingValueByKey("layer_change_start")) #0-infinity
        layer_change_end = int(self.getSettingValueByKey("layer_change_end")) #0-infinity
        blend_values = [float(blend_values) for blend_values in self.getSettingValueByKey("blend_values").strip().split(',')] #100,0,0,0
        change_rate = int(self.getSettingValueByKey("change_rate")) # default value 4
        effect_modifier = str(self.getSettingValueByKey("effect_modifier")) #"normal":"Normal", "wood":"Wood Texture", "random":"Random"
        rate_modifier = str(self.getSettingValueByKey("rate_modifier")) #"normal":"Normal", "random":"Random"

        # INITIATE EXTRUDERS AS ZERO EXCEPT FIRST ONE
        base_input = [0] * qty_extruders
        base_input[0] = 1

        # CHECK ORDER OF VALUES ENTERED BY USER
        percent_start = float(self.getSettingValueByKey("percent_change_start") / 100)
        percent_end = float(self.getSettingValueByKey("percent_change_end") / 100)
        layer_start = int(self.getSettingValueByKey("layer_change_start"))
        layer_end = int(self.getSettingValueByKey("layer_change_end"))
        # REORDER IF BACKWARDS
        if percent_end < percent_start:
            percent_start, percent_end = percent_end, percent_start
        if layer_end < layer_start:
            layer_start, layer_end = layer_end, layer_start

        current_position = 0
        end_position = 0

        index = 0
        active_tool = "T0"

        # Iterate through the layers
        for active_layer in data:

            # Remove the whitespace and split the gcode into lines
            lines = active_layer.strip().split("\n")

            modified_gcode = ""
            for line in lines:
                if ";LAYER_COUNT:" in line:
                    # FINDING THE ACTUAL AFFECTED LAYERS
                    total_layers = float(line[(line.index(':') + 1): len(line)])

                    modified_gcode += line  # list the initial line info

                    # DEBUG FOR USER REPORTING
                    modified_gcode += print_debug("Version:", self.version)

                    # INITIATE VALUES USED THROUGH THE AFFECTED LAYERS
                    if change_rate != 0:
                        changes_total = int(total_layers/change_rate)  # how many times are we allowed to adjust
                    else:
                        changes_total = 0

                    changes_per_extruder = int(changes_total / (qty_extruders - 1))
                    current_extruder = 0
                    next_extruder = 1
                    ext_fraction = changes_per_extruder
                # CHANGES MADE TO LAYERS THROUGH THE AFFECTED LAYERS

                elif ";LAYER:" + str(current_position) in line:
                    modified_gcode += line + "\n"

                    # ADJUST EXTRUDER RATES FOR NEXT AFFECTED LAYER 2 PARTS (should be simplified)
                    # Part 1 adjust rate by fraction to avoid rounding errors from addition
                    if effect_modifier == 'normal':
                        base_input[current_extruder], base_input[next_extruder] = standard_shift(ext_fraction, changes_per_extruder)
                    elif effect_modifier == 'wood':
                        base_input[current_extruder], base_input[next_extruder] = wood_shift(0.05, 0.25)
                    elif effect_modifier == 'random':
                        base_input[current_extruder], base_input[next_extruder] = random_shift()

                    # Part 2 initialize what percentage to reach wrap extruders back to start if out of range
                    ext_fraction -= 1
                    if ext_fraction < 0:
                        current_extruder += 1
                        next_extruder += 1
                        ext_fraction = changes_per_extruder-1  # -1 to avoid duplicate 0:1:0
                    if next_extruder == qty_extruders:
                        next_extruder = 0

                    # lAST TWEAK ADJUST THE EXTRUDER VALUES BY FLOW ADJUSTMENTS AND LIMITS
                    ext_gcode_list = [''] * qty_extruders
                    gcode_index = 0
                    for ext in ext_gcode_list:
                        ext_gcode_list[ext_gcode_list.index(ext)] = format(base_input[gcode_index] , '.3f')
                        gcode_index += 1

                    # TURN THE EXTRUDER VALUES INTO A SINGLE GCODE LINE
                    modified_gcode += adjust_extruder_rate(line, *ext_gcode_list)

                    # CHANGE THE POSITION FOR NEXT RUN
                    if rate_modifier == 'normal':
                        current_position += standard_rate(change_rate)
                    elif rate_modifier == 'random':
                        current_position += random_rate(change_rate, change_rate*2)

                elif "T0" in line:
                    modified_gcode += line + "\n;T0 found\n"
                    active_tool = "T0"
                elif "T1" in line:
                    modified_gcode += line + "\n;T1 found\n"
                    active_tool = "T1"
                elif "T2" in line:
                    modified_gcode += line + "\n;T2 found\n"
                    active_tool = "T2"
                elif "T3" in line:
                    modified_gcode += line + "\n;T3 found\n"
                    active_tool = "T3"
                elif "T4" in line:
                    modified_gcode += line + "\n;T4 found\n"
                    active_tool = "T4"
                elif "T5" in line:
                    modified_gcode += line + "\n;T5 found\n"
                    active_tool = "T5"
                elif "T6" in line:
                    modified_gcode += line + "\n;T6 found\n"
                    active_tool = "T6"
                else:
                    modified_gcode += line + "\n"

            # REPLACE THE DATA
            data[index] = modified_gcode
            index += 1
        return data


# MODIFIERS FOR DIFFERENT EFFECTS ON EXTRUDERS
# SHIFTS AFFECT EXTRUDER RATIOS AND RETURN BOTH VALUES TOGETHER (X AND 1-X)
def standard_shift(numerator, denominator):
    return numerator/denominator, (denominator-numerator)/denominator


def wood_shift(min_percentage, max_percentage):
    random_value = random.uniform(min_percentage, max_percentage)
    return 1-random_value, random_value


def random_shift():
    random_value = random.uniform(0, 1)
    return 1-random_value, random_value


# RATES AFFECT FREQUENCY OF SHIFTS AND RETURN ONE VALUE
def standard_rate(rate):
    return rate


def random_rate(min_percentage, max_percentage):
    random_value = int(random.uniform(min_percentage, max_percentage))
    return random_value


