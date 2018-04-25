# Current Version contains
# Support for 2-4 extruders
# Initial Flow for raft or anything before affected layers
# First part of modifiers so future options can be added easier (needs work)
# Modifiers Part 1. base_input - allowing it to be easier to add a wood texture modifier and heart beat modifier
# Modifiers Part 2. change_rate - allowing random distances between changes for wood texture
# Fixed duplicate 0:1:0, 0:1:0:0, and 0:0:1:0 showing up
# Abandoned Overflow until able to prove its useful
# Re-enabled the initiate_extruder function
# Ability to choose what color the print ends with after adjusted layers
# Added debug reporting to gcode file for troubleshooting user problems that may arise
# Ability to set the initial extruder rate and not shift through the print by setting change rate to 0
# Pattern Modifier added (Heartbeat)
# Split Rate Modifiers from Modifiers to add versatility
# Allowed for multiple runs of the script (this allows you to shift 1:0 > 0:1 for the first 20% of the print and then shift 0:1 > 1:0 for the last 20%)
# Enabled ability to wrap the shift back to the beginning nozzle with user input circular or linear
# Added Slope Modifier
# Added Ellipse Modifier
# Added Lerp Modifier
# Changed Initial extruder code to allow user to make adjustments

# Current Bugs
# duplicate values when running multiple scripts that overlap affected areas
# Its possible to enter non numeral values for initial and final extruder values  but non numerals would break the code

# Future Updates
# More Modifiers (exponential, logarithmic)

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
    version = "3.4.0"

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
                    "description": "How many extruders in mixing nozzle.",
                    "type": "enum",
                    "options": {"2":"Two","3":"Three","4":"Four"},
                    "default_value": "2"
                },
                "a_trigger":
                {
                    "label": "Shifting Clamp Type",
                    "description": "Begin and end shifting at percentage or layer.",
                    "type": "enum",
                    "options": {"percent":"Percentage","layer_no":"Layer No."},
                    "default_value": "percent"
                },
                "percent_change_start":
                {
                    "label": "Extrusion % Start",
                    "description": "Percentage of layer height to start shifting extruder percentage.",
                    "unit": "%",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "99",
                    "enabled": "a_trigger == 'percent'"
                },
                "percent_change_end":
                {
                    "label": "Extrusion % End",
                    "description": "Percentage of layer height to stop shifting extruder percentage.",
                    "unit": "%",
                    "type": "float",
                    "default_value": 100,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "minimum_value_warning": "1",
                    "maximum_value_warning": "100",
                    "enabled": "a_trigger == 'percent'"
                },
                "layer_change_start":
                {
                    "label": "Extrusion # Start",
                    "description": "Layer to start shifting extruder percentage.",
                    "unit": "#",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": "0",
                    "enabled": "a_trigger == 'layer_no'"
                },
                "layer_change_end":
                {
                    "label": "Extrusion # End",
                    "description": "Layer to stop changing extruder percentage. If layer is more then total layers the max layer will be chosen.",
                    "unit": "#",
                    "type": "int",
                    "default_value": 100000,
                    "minimum_value": "0",
                    "enabled": "a_trigger == 'layer_no'"
                },
                "b_trigger":
                {
                    "label": "Extruder Rotation",
                    "description": "The order in which the shift moves through the extruders.",
                    "type": "enum",
                    "options": {"normal":"Normal","reversed":"Reversed"},
                    "default_value": "normal"
                },
                "change_rate":
                {
                    "label": "Shift frequency",
                    "description": "How many layers until the color is shifted each time. Setting to 0 Allows the initial rate to be set only.",
                    "unit": "#",
                    "type": "int",
                    "default_value": 4,
                    "minimum_value": "0",
                    "maximum_value": "1000",
                    "minimum_value_warning": "1",
                    "maximum_value_warning": "100"
                },
                "c_trigger":
                {
                    "label": "Shift Loop Type",
                    "description": "::Linear: Start with primary extruder finish with last extruder. ::Circular: Start with primary extruder shift through to last extruder and then shift back to primary extruder",
                    "type": "enum",
                    "options": {"1":"Linear","0":"Circular"},
                    "default_value": "1"
                },
                "e_trigger":
                {
                    "label": "Modifier Type",
                    "description": "::Normal: Sets the shift to change gradually throughout the length of the layers within the clamp. ::Wood Texture: Sets one extruder at a random small percentage and adjusts change frequency by a random amount, simulating wood grain. ::Repeating Pattern: Repeats a set extruder pattern throughout the print. ",
                    "type": "enum",
                    "options": {"normal":"Normal", "wood":"Wood Texture", "pattern":"Repeating Pattern", "random":"Random", "lerp":"Linear Interpolation", "slope":"Slope Formula", "ellipse":"Ellipse Formula"},
                    "default_value": "normal"
                },
                "f_trigger":
                {
                    "label": "Rate Modifier Type",
                    "description": "How often the print shifts. ::Normal: Uses the change rate.  ::Random: picks a number of layers between the set change_rate and change_rate*2",
                    "type": "enum",
                    "options": {"normal":"Normal", "random":"Random"},
                    "default_value": "normal"
                },
                "lerp_i":
                {
                    "label": "Linear Interpolation",
                    "description": "Values shift up or down y axis.",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "-1",
                    "maximum_value": "1",
                    "minimum_value_warning": "-0.9",
                    "maximum_value_warning": "0.9",
                    "enabled": "e_trigger == 'lerp'"
                },
                "slope_m":
                {
                    "label": "Slope",
                    "description": "Slope (M) of the formula Y=MX+B. Normal range between -2 to 0. -1 is a one to one even slope. Values higher than -1 will start the shift later in the print. Values lower than -1 will start the print with a lower value for the primary extruder.",
                    "type": "float",
                    "default_value": -1,
                    "minimum_value": "-2",
                    "maximum_value": "0",
                    "minimum_value_warning": "-25",
                    "maximum_value_warning": "0.1",
                    "enabled": "e_trigger == 'slope'"
                },
                "slope_i":
                {
                    "label": "Y Intercept",
                    "description": "Y Intercept (B) of the formula Y=MX+B. Normal range between 2 to 0. 1 is normal. Values lower than 1 will cause the primary extruder to retain 1 longer. Values higher than 1 will start out with primary extruder at a lower value, which will also run out sooner.",
                    "type": "float",
                    "default_value": 1,
                    "minimum_value": "0",
                    "maximum_value": "2",
                    "minimum_value_warning": "0.1",
                    "maximum_value_warning": "1.9",
                    "enabled": "e_trigger == 'slope'"
                },
                "pattern":
                {
                    "label": "Pattern",
                    "description": "Set a repeating pattern of extruder values between 0 and 1.",
                    "type": "str",
                    "default_value": "0.5,1,0.25,0.75,0.5,0",
                    "enabled": "e_trigger == 'pattern'"
                },
                "e1_trigger":
                {
                    "label": "Expert Controls",
                    "description": "Enable more controls. Some of which are for debugging purposes and may change or be removed later",
                    "type": "bool",
                    "default_value": false
                },
                "enable_initial":
                {
                    "label": "Enable Initial Setup",
                    "description": "If your extruder setup isn't already set in the duet’s sd card settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "e1_trigger"
                },
                "initial_a":
                {
                    "label": "Define Tool",
                    "description": "Define Tool",
                    "type": "str",
                    "default_value": "M563 P0 D0:1 H1",
                    "enabled": "enable_initial"
                },
                "initial_b":
                {
                    "label": "Set Tool Axis Offsets",
                    "description": "Set Tool Axis Offsets",
                    "type": "str",
                    "default_value": "G10 P0 X0 Y0 Z0",
                    "enabled": "enable_initial"
                },
                "initial_c":
                {
                    "label": "Set Initial Tool Active",
                    "description": "Set Initial Tool Active",
                    "type": "str",
                    "default_value": "G10 P0 R120 S220",
                    "enabled": "enable_initial"
                },
                "initial_d":
                {
                    "label": "Turn On Tool Mixing For The Extruder",
                    "description": "Turn On Tool Mixing For The Extruder",
                    "type": "str",
                    "default_value": "M568 P0 S1",
                    "enabled": "enable_initial"
                },
                "initial_e":
                {
                    "label": "Extra GCode",
                    "description": "Any Extra Gcode To Run At Start Of Print.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_initial"
                },
                "initial_flow":
                {
                    "label": "Initial Main Flow",
                    "description": "Flow to initially set extruders must total up to 1.000  ::This allows the extruder to be set for any portion of the print before the actual shift begins.",
                    "unit": "0-1",
                    "type": "str",
                    "default_value": "1,0,0,0",
                    "enabled": "e1_trigger"
                },
                "final_flow":
                {
                    "label": "Final Main Flow",
                    "description": "Flow to initially set extruders must total up to 1.000  ::This allows the extruder to be set for any portion of the print after the affected layers.",
                    "unit": "0-1",
                    "type": "str",
                    "default_value": "0,0,0,1",
                    "enabled": "e1_trigger"
                },
                "flow_adjust":
                {
                    "label": "Ext Flow Adjust",
                    "description": "This compensates for under or over extrusion due to variances in filament",
                    "unit": "% + -",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "-20",
                    "maximum_value": "20",
                    "minimum_value_warning": "-5",
                    "maximum_value_warning": "5",
                    "enabled": "e1_trigger"
                },
                "flow_min":
                {
                    "label": "Minimum Flow Allowed",
                    "description": "Clamp to keep both extruders flowing a small amount to prevent clogs. 0% to 5% Normally",
                    "unit": "%",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "0",
                    "maximum_value": "10",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "5",
                    "enabled": "e1_trigger"
                }
            }
        }"""

    def execute(self, data: list):  # used to be data: list
        # Set user settings from cura
        clamp_choice = self.getSettingValueByKey("a_trigger")
        direction = self.getSettingValueByKey("b_trigger")

        # EVENTUALLY USED TO MAKE THE EXTRUDER LOOP BACK TO THE FIRST EXTRUDER
        loop = self.getSettingValueByKey("c_trigger")  # linear or circular (not currently enabled)

        modifier = self.getSettingValueByKey("e_trigger")  # normal, wood, pattern
        rate_modifier = self.getSettingValueByKey("f_trigger")  # normal, random
        change_rate = int(self.getSettingValueByKey("change_rate"))
        initial_flows = [float(initial_flow) for initial_flow in self.getSettingValueByKey("initial_flow").strip().split(',')]
        final_flows = [float(final_flow) for final_flow in self.getSettingValueByKey("final_flow").strip().split(',')]
        flow_adjust = float((self.getSettingValueByKey("flow_adjust")) / 100) + 1  # convert user input into multi
        qty_extruders = int(self.getSettingValueByKey("qty_extruders"))
        flow_min = float(self.getSettingValueByKey("flow_min") / 100) * qty_extruders
        flow_clamp_adjust = float(1 - (flow_min * qty_extruders))
        pattern = [float(pattern) for pattern in self.getSettingValueByKey("pattern").strip().split(',')]
        lerp_i = self.getSettingValueByKey("lerp_i")
        slope_m = self.getSettingValueByKey("slope_m")
        slope_i = self.getSettingValueByKey("slope_i")

        enable_initial = self.getSettingValueByKey("enable_initial")
        initial_a = self.getSettingValueByKey("initial_a")
        initial_b = self.getSettingValueByKey("initial_b")
        initial_c = self.getSettingValueByKey("initial_c")
        initial_d = self.getSettingValueByKey("initial_d")
        initial_e = self.getSettingValueByKey("initial_e")

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
        has_been_run = 0

        # Iterate through the layers
        for active_layer in data:

            # Remove the whitespace and split the gcode into lines
            lines = active_layer.strip().split("\n")

            modified_gcode = ""
            for line in lines:
                if ";Modified:" in line:
                    has_been_run = 1
                elif ";LAYER_COUNT:" in line:
                    # FINDING THE ACTUAL AFFECTED LAYERS
                    total_layers = float(line[(line.index(':') + 1): len(line)])

                    # Calculate positions based on total_layers
                    if clamp_choice == 'percent':
                        start_position = int(int(total_layers) * float(percent_start))
                        current_position = start_position
                        end_position = int(int(total_layers) * float(percent_end))
                    if clamp_choice == 'layer_no':
                        start_position = int(clamp(layer_start, 0, total_layers))
                        current_position = start_position
                        end_position = int(clamp(layer_end, 0, total_layers))

                    # how many layers are affected
                    adjusted_layers = end_position - start_position

                    # Make sure the change_rate doesnt sit outside of allowed values
                    change_rate = int(clamp(change_rate, 0, adjusted_layers))

                    # SETTING THE FLOWS SET BY USER IN EXPERT CONTROLS
                    while len(initial_flows) < len(base_input):  # Ensure at least as many are set as needed
                        initial_flows.append(float(0))
                    total_value = 0
                    i = 0
                    for ext in base_input:  # Disregard extras
                        initial_flows[i] = clamp(initial_flows[i], 0, 1)  # Clamp to value range
                        if i == len(base_input)-1 and total_value < 1:  # Make the last one add up to 1
                            base_input[i] = 1 - total_value
                        elif initial_flows[i] + total_value < 1:  # Keep within total of 1
                            base_input[i] = initial_flows[i]
                        else:
                            base_input[i] = 1 - total_value
                        total_value += base_input[i]
                        i += 1

                    # ASSIGN THE INITIAL VALUES TO A SINGLE GCODE LINE
                    ext_gcode_list = [''] * qty_extruders
                    gcode_index = 0
                    for code in ext_gcode_list:
                        ext_gcode_list[ext_gcode_list.index(code)] = format(base_input[gcode_index] * flow_adjust * flow_clamp_adjust + flow_min, '.3f')
                        gcode_index += 1

                    modified_gcode += line  # list the initial line info

                    if has_been_run == 0:
                        if enable_initial:
                            modified_gcode += initiate_extruder("", initial_a, initial_b, initial_c, initial_d, initial_e)
                        if direction == 'normal':
                            modified_gcode += adjust_extruder_rate("", *ext_gcode_list)
                        else:
                            modified_gcode += adjust_extruder_rate("", *ext_gcode_list[::-1])

                    # DEBUG FOR USER REPORTING
                    modified_gcode += print_debug("Version:", self.version)
                    modified_gcode += print_debug("Clamp_choice:", clamp_choice, "  Direction:", direction)
                    modified_gcode += print_debug("Modifier:", modifier, "  Rate Modifier:", rate_modifier)
                    modified_gcode += print_debug("Pattern:", pattern)
                    modified_gcode += print_debug("Change_rate:", change_rate, "  Initial_flows:", initial_flows, "  Final_flows", final_flows)
                    modified_gcode += print_debug("Qty_extruders:", qty_extruders, "  Flow_min:", flow_min)
                    modified_gcode += print_debug("Percent_start:", percent_start, "  Percent_end:", percent_end)
                    modified_gcode += print_debug("Layer_start:", layer_start, "  Layer_end:", layer_end)


                    # INITIATE VALUES USED THROUGH THE AFFECTED LAYERS
                    if change_rate != 0:
                        changes_total = int(adjusted_layers/change_rate)  # how many times are we allowed to adjust
                    else:
                        changes_total = 0

                    #changes_per_extruder = int(changes_total/(qty_extruders-1))
                    changes_per_extruder = int(changes_total/(qty_extruders-int(loop)))
                    current_extruder = 0
                    next_extruder = 1
                    ext_fraction = changes_per_extruder

                # CHANGES MADE TO LAYERS THROUGH THE AFFECTED LAYERS
                elif ";LAYER:" + str(current_position) in line and int(current_position) < int(end_position):

                    # ADJUST EXTRUDER RATES FOR NEXT AFFECTED LAYER 2 PARTS (should be simplified)
                    # Part 1 adjust rate by fraction to avoid rounding errors from addition
                    if modifier == 'normal':
                        base_input[current_extruder], base_input[next_extruder] = standard_shift(ext_fraction, changes_per_extruder)
                    elif modifier == 'wood':
                        base_input[current_extruder], base_input[next_extruder] = wood_shift(0.05, 0.25)
                    elif modifier == 'pattern':
                        base_input[current_extruder], base_input[next_extruder] = pattern_shift(pattern)
                    elif modifier == 'random':
                        base_input[current_extruder], base_input[next_extruder] = random_shift()
                    elif modifier == 'lerp':
                        base_input[current_extruder], base_input[next_extruder] = lerp_shift(0, changes_per_extruder, ext_fraction/changes_per_extruder, lerp_i)
                    elif modifier == 'slope':
                        base_input[current_extruder], base_input[next_extruder] = lerp_shift(ext_fraction, changes_per_extruder, slope_m, slope_i)
                    elif modifier == 'ellipse':
                        base_input[current_extruder], base_input[next_extruder] = ellipse_shift(ext_fraction/changes_per_extruder)

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
                        ext_gcode_list[ext_gcode_list.index(ext)] = format(base_input[gcode_index] * flow_adjust * flow_clamp_adjust + flow_min, '.3f')
                        gcode_index += 1

                    # TURN THE EXTRUDER VALUES INTO A SINGLE GCODE LINE
                    if direction == 'normal':
                        modified_gcode += adjust_extruder_rate(line, *ext_gcode_list)
                    else:
                        modified_gcode += adjust_extruder_rate(line, *ext_gcode_list[::-1])

                    # CHANGE THE POSITION FOR NEXT RUN
                    if rate_modifier == 'normal':
                        current_position += standard_rate(change_rate)
                    elif rate_modifier == 'random':
                        current_position += random_rate(change_rate, change_rate*2)

                # CHANGES MADE AFTER THE LAST AFFECTED LAYER TO COMPLETE THE PRINT WITH
                elif ";LAYER:" + str(end_position) in line:  # Runs last and only runs once
                    # SETTING THE FLOWS SET BY USER IN EXPERT CONTROLS
                    while len(final_flows) < len(base_input):  # Ensure at least as many are set as needed
                        final_flows.append(float(0))
                    total_value = 0
                    i = 0
                    for ext in base_input:  # Disregard extras
                        final_flows[i] = clamp(final_flows[i], 0, 1)  # Clamp to value range
                        if i == len(base_input) - 1 and total_value < 1:  # Make the last one add up to 1
                            base_input[i] = 1 - total_value
                        elif final_flows[i] + total_value < 1:  # Keep within total of 1
                            base_input[i] = final_flows[i]
                        else:
                            base_input[i] = 1 - total_value
                        total_value += base_input[i]
                        i += 1

                    # ASSIGN THE INITIAL VALUES TO A SINGLE GCODE LINE
                    ext_gcode_list = [''] * qty_extruders
                    gcode_index = 0
                    for code in ext_gcode_list:
                        ext_gcode_list[ext_gcode_list.index(code)] = format(base_input[gcode_index] * flow_adjust * flow_clamp_adjust + flow_min, '.3f')
                        gcode_index += 1

                    # change direction of shift if set by user
                    if direction == 'normal':
                        modified_gcode += adjust_extruder_rate(line, *ext_gcode_list)
                    else:
                        modified_gcode += adjust_extruder_rate(line, *ext_gcode_list[::-1])

                # LEAVE ALL OTHER LINES ALONE SINCE THEY ARE NOT NEW LAYERS
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
    return random_value, 1-random_value


def pattern_shift(list):
    value = list.pop()
    list.insert(0, value)
    return value, 1-value


def random_shift():
    random_value = random.uniform(0, 1)
    return random_value, 1-random_value


def slope_shift(x_numerator, x_denomerator, m_slope, y_intercept):
    y = (m_slope*x_numerator/x_denomerator)+y_intercept
    y = clamp(y, 0, 1)
    return 1-y, y


def lerp_shift(v0, v1, t, i):
    #answer = (1 - t) * v0 + t * (v1*(1+i))
    answer = 1
    return 1-answer, answer



def ellipse_shift(x):
    y = 4 - ((0.12*x*x) + (1.12 * x) + 2.78)
    y = clamp(y, 0, 1)
    y = pow(y, 0.5)
    y = clamp(y, 0, 1)  # This is unnecessary but here just as an in case.
    return 1-y, y


# RATES AFFECT FREQUENCY OF SHIFTS AND RETURN ONE VALUE
def standard_rate(rate):
    return rate


def random_rate(min_percentage, max_percentage):
    random_value = int(random.uniform(min_percentage, max_percentage))
    return random_value




