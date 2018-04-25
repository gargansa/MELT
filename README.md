# MELT Multi-Extruder Layering Tool

A Cura plugin that adds support for the [M3D ProMega 3D Printer](https://store.printm3d.com/pages/promega) Compound Extruder and QuadFusion Extruder.

Please visit the [melt Wiki](https://github.com/gargansa/melt/wiki) for more information!

## Cura
[Cura](https://ultimaker.com/en/products/ultimaker-cura-software) is a 3rd party slicing software created and maintained by the folks over at [Ultimaker](https://ultimaker.com/). This software is provided for free and can be used to generate [.gcode](https://en.wikipedia.org/wiki/G-code) files for use with your [M3D ProMega 3D Printer](https://store.printm3d.com/pages/promega).

## M3D
[M3D](http://printm3d.com/) is one of the leading manufacturers of consumer 3D printers and filaments in the world. M3D is the company that produces the [M3D ProMega 3D Printer](https://store.printm3d.com/pages/promega).

## MELT
[melt](https://github.com/gargansa/MELT) is a plugin that adds support for some of the new / advanced features of the [M3D ProMega 3D Printer](https://store.printm3d.com/pages/promega).

## Version History


## Current Features List
1. Support for 2-4 extruders
2. allows the shift to start at any layer or percentage of the print and stop at any layer or percentage.
3. Initial Flow setting for raft or anything before affected layers
4. Shift Modifiers  - Normal, Wood Texture, Repeating Pattern, Random, Lerp, Slope, Ellipse
5. Rate Modifiers - Normal, Random 
6. Direction Modifier (incase you loaded the filament into opposite extruders)
7. Final Flow setting for anything after the affected layers
8. Debug reporting to gcode file for troubleshooting user problems that may arise
9. Ability to only set the initial extruder rate and not shift through the print by setting change rate to 0
10. Multiple runs of script will allow you to shift from 1:0 to 0:1 for the first % of the print and then 0:1 to 1:0 for the next % of the print 
11. Option to wrap the shift back to the beginning nozzle with user input circular or linear to just end at the last extruder
12. Allows a gradient shift through any number of objects in the same direction.

## Possible Next Features
1. Ability to change at a specific layer once
2. Ability to Insert a pause at end of shift so that filaments can be removed and changed to create rainbow effect
3. Having the ability to apply both "fixed mix ratios" and "gradients" to different parts of a multi file print.
4. Dynamically display extruders to account for both the Dual Compound and QuadFusion extruders
5. Increasing the number of modifiers as long as they are unique, artistic or useful.
6. Ability to set start and end range values to each extruder
7. Ability to select which extruders to preform the interpolation with when using three or four extruders
8. Ability to extrude with both extruders on compound, and all four on QuadFusion at once to achieve faster print time.
9. Ability to define starting and stopping layers for mixes. Example: First 50% of print, shift between 0.5,0.0,0.0,0.5 to 0.0,0.5,0.5,0.0 and last 50% of print shift from 0.5,0.5,0.0,0.0 to 0.0,0.0,0.5,0.5

## Longer term goals (complex goals)
1. Ability to gradient from side to side, or bottom corner to opposing top corner.
2. Ability to paint the surface(even if low quality) and predict and split the gcode where needed to execute the change early enough to hit the mark.

## Known Bugs
1. Its possible to enter non numeral values for initial and final extruder values  but non numerals would break the code
2. Possibly need to be able to edit P0 part of line on each extruder adjustment
3. Lerp, Slope, Ellipse Modifiers may need touchups
4. 


