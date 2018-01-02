from ..Script import Script
# current problems...
# running two sets of post processing fails the second post process
# possibly need an option for shift every 4 layers and shift about 100 times per print to be more clear with choices
# need description of project

# Recent fixed problems
# Reduced size of clamp function
# Reduced size of adjust_extruder_rate function
# simplified verifying input isn't backwards for layer_no and percentage
# simplified initiate_extruder function
# Math is correct between starting layer shift and ending layer shift so that ratio starts at 0:1 and ends at 1:0 instead of ending at 0.994:0.006 for example

# potential updates
# possible initial option choices
# easy mode (shift approx 100 times from top to bottom)
# Clamp Percentage (shift every n layers between start percentage and end percentage)
# clamp layer (shift every n layers between defined start and stop layers)

# possible secondary option (type of shifts)
# normal shift
# reverse shift
# logarithmic shift
# exponential shift
# fibonacci shift (1+1+2+3+5+8)
# heartbeat shift (pulse to set degree and frequency)
# wood shift (randomize up to degree of change and length of ring)

# Credits
# gargansa, bass4aj

# convenience function for coding familiarity
def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))

# function to compile the initial setup into a string
def initiate_extruder(existing_gcode,*ext):
    qty_ext = len(ext)
    setup_line = ""
    setup_line += ";Modified by ColorShift" + "\n"
    setup_line += existing_gcode + " Modified:\n"
    #define tool
    for i in range(0, qty_ext):
        if i == 0:
            setup_line += "M563 P0 D" + str(i)
        else:
            setup_line += ":" + str(i)
    setup_line += " H1 ;Define tool 0" + "\n"
    #position tool
    for i in range(0, qty_ext):
        setup_line += "M563 P2 D" + str(i) + " H" + str(i+1)
        setup_line += " ;Position " + str(i+1) + " tool" + "\n"
    #set axis offsets
    setup_line += "G10 P0 X0 Y0 Z0 ;Set tool 0 axis offsets" + "\n"
    #activate tool
    setup_line += "G10 P2 R120 S220 ;Set initial tool 0 active" + "\n"
    #set initial extrusion rate
    setup_line += adjust_extruder_rate(";Initial Extruder Rate", *ext)
    #initiate the tool
    setup_line += "M568 P0 S1 ;Turn on tool mixing for the extruder" + "\n"
    return setup_line

# function to compile extruder info into a string
def adjust_extruder_rate(existing_gcode, *ext):
    i = 0
    for item in ext:
        if i == 0:
            setup_line = existing_gcode + " ;Modified: \nM567 P0 E" + str(item)
        else:
            setup_line += ":" + str(item) + "\n"
        i += 1
    return setup_line


class ColorShift(Script):
    version = "1.0.0"
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"ColorShift",
            "key":"ColorShift",
            "metadata": {},
            "version": 2,
            "settings":
            {
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
                    "label": "Direction of Shift",
                    "description": "Allows the shift to run the opposite direction without swapping filaments.",
                    "type": "enum",
                    "options": {"normal":"Normal","reversed":"Reversed"},
                    "default_value": "normal"
                },
                "e1_trigger":
                {
                    "label": "Expert Controls",
                    "description": "Enable more controls. Some of which are for debugging purposes and may change or be removed later",
                    "type": "bool",
                    "default_value": false
                },
                "adjustments":
                {
                    "label": "Adjustments",
                    "description": "To grant an even shift adjustments are calculated based on this formula affected_layers/adjustments = change rate. The affected_layers are the total layers within the clamp set by percentages or layer numbers chosen. Adjustments are set here. The resulting change_rate is rounded down and the print will shift every count of change_rate.",
                    "unit": "# of changes",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "maximum_value": "400",
                    "minimum_value_warning": "1",
                    "maximum_value_warning": "200",
                    "enabled": "e1_trigger"
                },
                "flow_one_adjust":
                {
                    "label": "Ext One Flow Adjust",
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
                "flow_two_adjust":
                {
                    "label": "Ext Two Flow Adjust",
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
                    "description": "Clamp to keep both extruders flowing a small amount to prevent clogs",
                    "unit": "%",
                    "type": "float",
                    "default_value": 1,
                    "minimum_value": "0",
                    "maximum_value": "10",
                    "minimum_value_warning": "1",
                    "maximum_value_warning": "5",
                    "enabled": "e1_trigger"
                }
            }
        }"""

    def execute(self, data: list):  # used to be data: list
        # Set user settings from cura
        choice = self.getSettingValueByKey("a_trigger")
        direction = self.getSettingValueByKey("b_trigger")
        adjustments = int(clamp(self.getSettingValueByKey("adjustments"), 0, 999))  # clamp within understandable range
        flow_one_adjust = float((self.getSettingValueByKey("flow_one_adjust"))/100)+1  # convert user input into multi
        flow_two_adjust = float((self.getSettingValueByKey("flow_two_adjust"))/100)+1  # convert user input into multi
        flow_min = float(self.getSettingValueByKey("flow_min")/100)
        flow_clamp_adjust = float(1-(flow_min*2))

        # Make sure user settings are in order after loading
        percent_start = float(self.getSettingValueByKey("percent_change_start")/100)
        percent_end = float(self.getSettingValueByKey("percent_change_end")/100)
        if percent_end < percent_start:
            percent_start, percent_end = percent_end, percent_start

        # Make sure user settings are in order after loading
        layer_start = int(self.getSettingValueByKey("layer_change_start"))
        layer_end = int(self.getSettingValueByKey("layer_change_end"))
        if layer_end < layer_start:
            layer_start, layer_end = layer_end, layer_start

        # Initialize things that affect decisions
        current_position = 0
        index = 0

        # Iterate through the layers
        for active_layer in data:

            # Remove the whitespace and split the gcode into lines
            lines = active_layer.strip().split("\n")

            modified_gcode = ""
            for line in lines:

                # Find where to add the initial setup info
                if ";LAYER_COUNT:" in line:

                    # Find the actual total layers in the gcode
                    total_layers = float(line[(line.index(':') + 1): len(line)])

                    # Calculate positions based on total_layers
                    if choice == 'percent':
                        start_position = int(int(total_layers) * float(percent_start))  # find where to start
                        current_position = start_position
                        end_position = int(int(total_layers) * float(percent_end))  # find where to end
                    if choice == 'layer_no':
                        start_position = int(clamp(layer_start, 0, total_layers))
                        current_position = start_position
                        end_position = int(clamp(layer_end, 0, total_layers))

                    # Find the layers that are actually affected or the ones within the clamp set by user
                    adjusted_layers = end_position - current_position

                    # Make sure that the set adjustments are less then the actual affected layers since you can only adjust once per layer
                    adjustments = clamp(int(adjustments), 0, adjusted_layers)

                    # Find how often to adjust the rate
                    change_rate = int(int(adjusted_layers) / int(adjustments))

                    # Math to determine extruder percentage based on layer location without flow clamp and adjustments
                    location = (current_position-start_position)/(adjusted_layers-change_rate)

                    # Adjust extruder percentages by user set flow and clamp adjustments
                    extruder_one = format(location * flow_one_adjust * flow_clamp_adjust + flow_min, '.3f')
                    extruder_two = format((1-location) * flow_two_adjust * flow_clamp_adjust + flow_min, '.3f')

                    # Send extruder percentages to be compiled into a string based on direction set by user
                    if direction == 'normal':
                        modified_gcode = initiate_extruder(line, extruder_one, extruder_two)
                    else:
                        modified_gcode = initiate_extruder(line, extruder_two, extruder_one)

                # Find where to add for affected layers
                elif ";LAYER:" + str(current_position) in line and int(current_position) < int(end_position):

                    # Same thing we did above
                    location = (current_position-start_position)/(adjusted_layers-change_rate)
                    extruder_one = format(location*flow_one_adjust * flow_clamp_adjust + flow_min, '.3f')
                    extruder_two = format((1-location)*flow_two_adjust * flow_clamp_adjust + flow_min, '.3f')
                    if direction == 'normal':
                        modified_gcode = adjust_extruder_rate(line, extruder_one, extruder_two)
                    else:
                        modified_gcode = adjust_extruder_rate(line, extruder_two, extruder_one)

                    # Increase the position for the next line to find it on the next loop
                    current_position += int(change_rate)

                # If no conditions apply leave the code alone
                else:
                    modified_gcode += line + "\n"

            # Replace the data
            data[index] = modified_gcode
            index += 1
        return data
