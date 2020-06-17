# fit2gpx
#
# Copyright (c) 2020, Oleg Khudyakov <prcoder@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from ant.fs.commons import crc
from ctypes import *
import datetime
import logging
import struct
import array

_logger = logging.getLogger("ant.base.ant")

_data_type_names = ("enum", "int8", "uint8", "int16", "uint16", "int32", "uint32", "string", "float32", "float64", "uint8z", "uint16z", "uint32z", "bytes")

_message_type_names = {
    0 : "File Id", 1 : "Capabilities", 2 : "Device Settings", 3 : "User Profile", 4 : "HRM Profile", 5 : "SDM Profile", 6 : "Bike Profile", 7 : "Zones Target",
    8 : "Heart Rate Zone", 9 : "Power Zone", 10 : "Met Zone", 11 : "", 12 : "Sport", 13 : "", 14 : "", 15 : "Traning Goals", 16 : "", 17 : "", 18 : "Session",
    19 : "Lap", 20 : "Record", 21 : "Event", 22 : "", 23 : "Device Info", 24 : "", 25 : "", 26: "Workout", 27 : "Workout Step", 28 : "Schedule", 29 : "Way Point",
    30 : "Weight Scale", 31: "Course", 32 : "Course Point", 33 : "Totals", 34 : "Activity", 35 : "Software", 36 : "", 37 : "File Capabilities",
    38 : "Message Capabilities", 39 : "Field Capabilities", 49 : "File Creator", 51 : "Blood Pressure", 53 : "Speed Zone", 55 : "Monitoring",
    74 : "???", 78 : "HRV", 79 : "User Profile ?", 101: "Length", 103 : "Monitoring Info", 104 : "???", 105 : "PAD"
}

_message_field_names = {
    0 : ("Type", "Manufacturer", "Product", "Serial Number", "Creation Time", "Number"),
    1 : ("", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "Workout Supported"),
    2 : ("", "UTC Offset", "???", "???", "???", "???", "", "", "", "", "???", "???", "???", "???", "???", "???", "???", "???", "???", "", "", "???", "???", "???", "???", "???", "???"),
    3 : ("Name", "Gender", "Age", "Height", "Weight", "Language", "Elevation Units", "Weight Units", "HR Resting", "HR Running Max", "HR Biking Max", "HR Max", "HR Setting", "Speed Setting", "Dist Setting", "", "Power Setting", "Activity Class", "Position Setting", "", "", "???", "", "", "???"),
    4 : ("Enabled", "HRM ANT Id", "???", "???"),
    5 : ("", "", "", "???", "???", "???"),
    6 : ("Name", "Sport", "SubSport", "Odometer", "Bike Spd ANT Id", "Bike Cad ANT Id", "Bike Spd/Cad ANT Id", "Bike Power ANT Id", "Custom Wheel Size", "Auto Wheel Size", "Bike Weight", "Power Calibration Factor", "Auto Wheel Calibration", "Auto Power Zero", "Id", "Spd Enabled", "Cad Enabled", "Spd/Cad Enabled", "Power Enabled", "Crank Length", "Enabled", "Bike Spd ANT Id Trans Type", "Bike Cad ANT Id Trans Type", "Bike Spd/Cad ANT Id Trans Type", "Bike Power ANT Id Trans Type"),
    7 : ("", "Max Heart Rate", "Threshold Heart Rate", "Functional Threshold Power", "", "HR Calc Type", "PWR Calc Type", "", "???"),
    8 : ("", "High BPM", "Name"),
    9 : ("", "High Value", "Name"),
    10 : ("", "High BPM", "Calories", "Fat Calories"),
    11 : (),
    12 : ("Sport", "SubSport", "Name", "???", "???", "???"),
    13 : ("", "", "", "", "???", "???", "???", "", "???", "", "???", "", "", "", "", "", "", "", "", "", "", "", "???"),
    14 : ("", "", "", "", "???", "???"),
    15 : (),
    16 : ("", "", "???", "???"),
    17 : ("", "", "", "???", "", "???"),
    18 : ("Event", "Event Type", "Start Time", "Start Position Latitude", "Start Position Longitude", "Sport", "SubSport", "Total Elapsed Time", "Total Timer Time", "Total Distance", "Total Cycles", "Total Calories", "", "Total Fat Calories", "Average Speed", "Max Speed", "Average Heart Rate", "Max Heart Rate", "Average Cadence", "Max Cadence", "Average Power", "Max Power", "Total Ascent", "Total Descent", "Total Traning Effect", "First Lap Index", "Num Laps", "Event Group", "Trigger", "NEC Latitude", "NEC Longitude", "SWC Latitude", "SWC Longitude", "", "", "", "", "", "", "???", "", "???", "", "Swimming Stroke", "Pool Length", "", "Pool Length Unit", "", "???", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "???"),
    19 : ("Event", "Event Type", "Start Time", "Start Position Latitude", "Start Position Longitude", "End Position Latitude", "End Position Longitude", "Total Elapsed Time", "Total Timer Time", "Total Distance", "Total Cycles", "Total Calories", "Total Fat Calories", "Average Speed", "Max Speed", "Average Heart Rate", "Max Heart Rate", "Average Cadence", "Max Cadence", "Average Power", "Max Power", "Total Ascent", "Total Descent", "Intensity", "Lap Trigger", "Sport", "Event Group", "Nec Latitude", "Nec Longitude", "Swc Latitude", "Swc Longitude", "", "", "", "", "", "", "", "", "", "", "???", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "???" ),
    20 : ("Latitude", "Longitude", "Altitude", "Heart Rate", "Cadence", "Distance", "Speed", "Power", "Compressed Speed & Distance", "Grade", "Registance", "Time from Course", "Cycle Length", "Temperature", "Speed 1s", "Cycles", "Total Cycles", "Compressed Accumulated Power", "Accumulated Power", "Left-Right Balance"),
    21 : ("Event", "Event Type", "Data1", "Data2", "Event Group"),
    22 : ("???", "???", "???", "???", "???", "???", "???", "???", "???"),
    23 : ("Device Index", "Device Type", "Manufacturer", "Serial Number", "Product", "Software Version", "Hardware Version", "???", "???", "???", "Battery Voltage", "Battery Status", "", "", "", "???", "???"),
    24 : (),
    25 : (),
    26 : ("", "", "", "", "Sport", "Capabilities", "Valid Steps", "Protection", "Name"),
    27 : ("Step Name", "Duration Type", "Duration Value", "Target Type", "Target Value", "Custom Target Value Low", "Custom Target Value High", "Intensity"),
    28 : ("Manufacturer", "Product", "Serial Number", "Creation Time", "Completed", "Type", "Schedule Time"),
    29 : ("Name", "Latitude", "Longitude", "Symbol", "Altitude", "???", "Date"),
    30 : ("Weight", "Fat percent", "Hydration percent", "Visceral Fat Mass", "Bone Mass", "Muscle Mass", "Basal Met", "Physique Rating", "Active Met", "Metabolic Age", "Visceral Fat Rating"),
    31 : ("", "", "", "", "Sport", "Name", "Capabilities"),
    32 : ("", "Time", "Latitude", "Longitude", "Distance", "Type", "Name"),
    33 : ("Timer Time", "Distance", "Calories", "Sport", "", "???"),
    34 : ("Total Timer Time", "Number of Sessions", "Type", "Event", "Event Type", "Local Timestamp", "Event Group"),
    35 : ("", "", "", "Version", "", "Part No"),
    36 : (),
    37 : ("Type", "Flags", "Directory", "Max Count", "Max Size"),
    38 : ("File", "Message Num", "Count Type", "Count"),
    39 : ("File", "Message Num", "Field Num", "Count"),
    49 : ("Software Version", "Hardware Version"),
    53 : ("", "High Value", "Name"),
    74 : ("", "", "???", "", "???", "???"),
    79 : ("???", "Age", "Height", "Weight", "???", "???", "???", "???"),
    101 : ("Event", "Event Type", "Start Time", "Total Elapsed Time", "Total Timer Time", "Total Strokes", "Average Speed", "Swimming Stroke", "", "Average Swimming Cadence", "", "", "Length Type", ""),
    104 : ("???", "???", "???", "???")
}

_enum_file_type = { 1 : "Device", 2 : "Setting", 3 : "Sport", 4 : "Activity", 5 : "Workout", 6 : "Course", 7 : "Schedule", 8 : "Waypoints", 9 : "Monitoring", 10 : "Totals", 11 : "Goals", 32 : "Memory" }
_enum_gender = { 0 : "Female", 1 : "Male" }
_enum_language = { 0 : "English", 1 : "French", 2 : "Italian", 3 : "German", 4 : "Spanish", 5 : "Croatian", 6 : "Czech", 7 : "Danish", 8 : "Dutch", 9 : "Finnish", 10 : "Greek", 11 : "Hungarian", 12 : "Norwegian", 13 : "Polish", 14 : "Portuguese", 15 : "Slovakian", 16 : "Slovenian", 17 : "Swedish", 18 : "Russian", 254 : "Custom" }
_enum_sport = { 0 : "Generic", 1 : "Running", 2 : "Cycling", 3 : "Transition", 4 : "Fitness Equipment", 5 : "Swimming", 254 : "All" }
_enum_event = { 0 : "Timer", 3 : "Workout", 4 : "Workout Step", 5 : "Power Down", 6 : "Power Up", 7 : "Off Course", 8 : "Session", 9 : "Lap", 10 : "Course Point", 11 : "Battery", 12 : "Virtual Partner Pace", 13 : "HR High Alert", 14 : "HR Low Alert", 15 : "Speed High Alert", 16 : "Speed Low Alert", 17 : "Cadence High Alert", 18 : "Cadence Low Alert", 19 : "Power High Alert", 20 : "Power Low Alert", 21 : "Recovery HR", 22 : "Battery Low", 23 : "Time Duration Alert", 24 : "Distance Duration Alert", 25 : "Calorie Duration Alert", 26 : "Activity", 27 : "Fitness Equipment" }
_enum_event_type = { 0 : "Start", 1 : "Stop", 2 : "Consecutive Depreciated", 3 : "Marker", 4 : "Stop All", 5 : "Begin Depreciated", 6 : "End Depreciated", 7 : "End All Depreciated", 8 : "Stop Disable", 9 : "Stop Disable All" }
_enum_manufacturer = { 1 : "Garmin", 2 : "Garmin (FR405 ANTFS)", 3 : "Zephyr", 4 : "Dayton", 5 : "IDT", 6 : "SRM", 7 : "Quarq", 8 : "iBike", 9 : "Saris", 10 : "Spark HK", 11 : "Tanita", 12 : "Echowell", 13 : "Dynastream OEM", 14 : "Nautilus", 15 : "Dynastream", 16 : "Timex", 17 : "MetriGear", 18 : "Xelic", 19 : "Beurer", 20 : "CardioSport", 21 : "A&D", 22 : "HMM" }
_enum_products = {
    1 : { 1 : "Heart Rate Monitor", 2 : "AXH01 HRM Chipset", 3 : "AXB01 Chipset", 4 : "AXB02 Chipset", 5 : "HRM2SS", 717 : "Forerunner 405", 782 : "Forerunner 50", 988 : "Forerunner 60", 1018 : "Forerunner 310XT", 1036 : "EDGE 500", 1124 : "Forerunner 110", 20119: "Traning Center", 65534 : "Connect"}
}

_enums = {
    0  : { 0 : _enum_file_type, 1 : _enum_manufacturer },
    3  : { 1 : _enum_gender, 5 : _enum_language },
    12 : { 0 : _enum_sport },
    18 : { 0 : _enum_event, 1 : _enum_event_type, 5 : _enum_sport },
    19 : { 0 : _enum_event, 1 : _enum_event_type, 25 : _enum_sport },
    21 : { 0 : _enum_event, 1 : _enum_event_type },
    26 : { 4 : _enum_sport },
    31 : { 4 : _enum_sport },
    33 : { 3 : _enum_sport },
    34 : { 3 : _enum_event, 4 : _enum_event_type },
}

_symbols = { 1 : "(1)", 2 : "Beach", 3 : "Bike Trail", 4 : "Block, Blue", 5 : "Campground", 6 : "Car", 7 : "Hunting Area", 8 : "Drinking Water", 9 : "Fishing Area",
            10 : "Forest", 11 : "??? (11)",  12 : "Geocache", 13 : "Geocache Found", 14 : "Glider Area", 15 : "Golf Course", 16 : "Residence", 17 : "??? (17)",
            18 : "??? (18)", 19 : "City (Large)",  20 : "City (Medium)", 21 : "Parachute Area", 22 : "Park", 23 : "Bridge", 24 : "Flag, Red", 25 : "Pin, Green",
            26 : "Restroom", 27 : "RV Park", 28 : "Scenic Area", 29 : "Shower", 30 : "City (Small)", 31 : "Skiing Area", 32 : "Summit", 33 : "Swimming Area",
            34 : "Trail Head", 35 : "??? (35)", 36 : "Tunnel", 37 : "Ultralight Area"
}

def get_field_name(global_num, definition_num):
    if definition_num == 253:
        return "Timestamp"
    elif definition_num == 254:
        return "Index"
    return _message_field_names[global_num][definition_num]

def array_to_string(string_array):
    rv = "";
    for i in string_array:
        if i == 0:
            break
        rv += chr(i)
    return rv

def norm_coord(coord):
    return float(coord) * 180.0 / float(0x80000000)

def norm_alt(alt):
    return float(alt) / 5.0 - 500.0

def norm_odom(distance):
    return float(distance) / 100.0

def norm_speed(speed):
    return float(speed) * 0.0036

def norm_weight(weight):
    return float(weight) / 10.0

def norm_time(garmin_time):
    garmin_time += 631065600 # Garmin epoch offset
    return datetime.datetime.fromtimestamp(garmin_time).strftime('%Y-%m-%dT%H:%M:%SZ')

def fit_value_to_string(fit, offset, field_size, base_type_num, global_num, definition_num):
    rv = ""
    if base_type_num == 0: # enum
        value = struct.unpack('<B', fit[offset:offset+1])[0]
        enum_value = _enums.get(global_num)
        if enum_value != None:
            enum_value = enum_value.get(definition_num)
            if enum_value != None:
                enum_value = enum_value.get(value)
        if enum_value != None:
            rv = enum_value
        else:
            if value == 0xFF:
                rv = "<undefined>";
            else:
                rv += "["
                rv += str(value)
                rv += "]"
    elif base_type_num == 1: # int8
        value = struct.unpack('<b', fit[offset:offset+1])[0]
        if value == 0x7F:
            rv = "<undefined>"
        else:
            rv = str(value)
    elif base_type_num == 2 or base_type_num == 10: # uint8/uint8z
        value = struct.unpack('<B', fit[offset:offset+1])[0]
        if value == 0xFF:
            rv = "<undefined>"
        else:
            rv = str(value)
    elif base_type_num == 3: # int16
        value = struct.unpack('<h', fit[offset:offset+2])[0]
        if value == 0x7FFF:
            rv = "<undefined>"
        else:
            rv = str(value)
    elif base_type_num == 4 or base_type_num == 11: # uint16/uint16z
        value = struct.unpack('<H', fit[offset:offset+2])[0]
        if value == 0xFFFF:
            rv = "<undefined>"
        else:
            rv = str(value)
    elif base_type_num == 5: # int32
        value = struct.unpack('<l', fit[offset:offset+4])[0]
        if value == 0x7FFFFFFF:
            rv = "<undefined>"
        else:
            rv = str(value)
    elif base_type_num == 6 or base_type_num == 12: # uint32/uint32z
        value = struct.unpack('<L', fit[offset:offset+4])[0]
        if value == 0xFFFFFFFF:
            rv = "<undefined>"
        else:
            if definition_num == 253: # Timestamp
                rv = norm_time(value)
            else:
                rv = str(value)
    elif base_type_num == 7: # string
        rv += "\""
        rv += array_to_string(fit[offset:offset+field_size])
        rv += "\""
    return rv

def fit_to_gpx(fit):
    gpx = array.array('B', "<?xml version=\"1.0\"?>\n<gpx version=\"1.1\" creator=\"antf_cli\" xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd\"\nxmlns=\"http://www.topografix.com/GPX/1/1\"\nxmlns:gpxtpx=\"http://www.garmin.com/xmlschemas/TrackPointExtension/v1\"\nxmlns:gpxx=\"http://www.garmin.com/xmlschemas/GpxExtensions/v3\"\nxmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n")
    
    class FITHeader(LittleEndianStructure):
        _fields_ = [
            ("headerSize", c_uint8),
            ("protocolVersion", c_uint8),
            ("profileVersion", c_uint16),
            ("dataSize", c_uint32),
            ("signature", c_char * 4)
        ]
        _pack_ = 1
    
    class FITFooter(LittleEndianStructure):
        _fields_ = [
            ("crc", c_uint16),
        ]
        _pack_ = 1
        
    class RecordNormalHeader(LittleEndianStructure):
        _fields_ = [
            ("localMessageType", c_uint8, 4),
            ("reserved", c_uint8, 2),
            ("messageType", c_uint8, 1),
            ("headerType", c_uint8, 1)
        ]
        _pack_ = 1

    class RecordCompressedTimeStampHeader(LittleEndianStructure):
        _fields_ = [
            ("timeOffset", c_uint8, 5),
            ("localMessageType", c_uint8, 2),
            ("headerType", c_uint8, 1)
        ]
        _pack_ = 1

    class RecordFixed(LittleEndianStructure):
        _fields_ = [
            ("reserved", c_uint8),
            ("arch", c_uint8),
            ("globalNum", c_uint16),
            ("fieldsNum", c_uint8)
        ]
        _pack_ = 1

    class RecordField(LittleEndianStructure):
        _fields_ = [
            ("definitionNum", c_uint8),
            ("size", c_uint8),
            ("baseType", c_uint8)
        ]
        _pack_ = 1
    
    header_size = sizeof(FITHeader)
    footer_size = sizeof(FITFooter)
    record_header_size = sizeof(RecordNormalHeader)
    record_fixed_size = sizeof(RecordFixed)
    record_field_size = sizeof(RecordField)
    
    header_ptr = (c_uint8 * header_size)(*fit[0:header_size])
    header = cast(header_ptr, POINTER(FITHeader))[0]
    offset = header.headerSize
    
    if header.signature == ".FIT":
        fit_size = header.headerSize + header.dataSize 
        fit_crc = crc(fit[0:fit_size])
        
        footer_ptr = (c_uint8 * footer_size)(*fit[fit_size:fit_size+footer_size])
        footer = cast(footer_ptr, POINTER(FITFooter))[0]
        
        if fit_crc == footer.crc:
            _logger.debug("FIT Protocol=%d, Profile=%d, Data Size=%d bytes", header.protocolVersion, header.profileVersion, header.dataSize)
            
            tracks = {}
            waypoints = []
            record_definitions = {}
            file_type = 0xFF
            file_creation_time = 0
            track_name = ""
            
            while offset < fit_size:
                record_header_ptr = (c_uint8 * record_header_size)(*fit[offset:offset+record_header_size])
                record_header = cast(record_header_ptr, POINTER(RecordNormalHeader))[0]
                offset += record_header_size

                if record_header.headerType == 0:
                    if record_header.messageType == 0:
                        record_fixed = record_definitions[record_header.localMessageType][0]
                        record_fields = record_definitions[record_header.localMessageType][1]
                        global_num = record_fixed.globalNum

                        _logger.debug("Local Message: %s (%d), %d fields:", _message_type_names[global_num], global_num, record_fixed.fieldsNum)
                        
                        for field_num in range(record_fixed.fieldsNum):
                            base_type_num = record_fields[field_num].baseType & int('11111', 2)
                            definition_num = record_fields[field_num].definitionNum
                            field_size = record_fields[field_num].size

                            _logger.debug("\t%d.%d: %s (%s) = %s", global_num, definition_num, get_field_name(global_num, definition_num), _data_type_names[base_type_num],
                                          fit_value_to_string(fit, offset, field_size, base_type_num, global_num, definition_num))
                            
                            if global_num == 0: # File Id
                                if definition_num == 0: # Type
                                    file_type = struct.unpack('<B', fit[offset:offset+1])[0]
                                elif definition_num == 4: # Creation Time
                                    file_creation_tTime = struct.unpack('<L', fit[offset:offset+4])[0]
                            elif global_num == 20: # Record
                                if definition_num == 0: # Latitude
                                    tracks[track_name][-1][-1]["latitude"] = struct.unpack('<l', fit[offset:offset+4])[0]
                                elif definition_num == 1: # Longitude
                                    tracks[track_name][-1][-1]["longitude"] = struct.unpack('<l', fit[offset:offset+4])[0]
                                elif definition_num == 2: # Altitude
                                    tracks[track_name][-1][-1]["altitude"] = struct.unpack('<H', fit[offset:offset+2])[0]
                                elif definition_num == 3: # Heart Rate
                                    tracks[track_name][-1][-1]["heart_rate"] = struct.unpack('<B', fit[offset:offset+1])[0]
                                elif definition_num == 4: # Cadence
                                    tracks[track_name][-1][-1]["cadence"] = struct.unpack('<B', fit[offset:offset+1])[0]
                                elif definition_num == 253: # Timestamp
                                    tracks[track_name][-1].append({})
                                    tracks[track_name][-1][-1]["time"] = struct.unpack('<L', fit[offset:offset+4])[0]
                            elif global_num == 29: # WayPoint
                                if definition_num == 0: # Name
                                    waypoints[-1]["name"] = array_to_string(fit[offset:offset+16])
                                elif definition_num == 1: # Latitude
                                    waypoints[-1]["latitude"] = struct.unpack('<l', fit[offset:offset+4])[0]
                                elif definition_num == 2: # Longitude
                                    waypoints[-1]["longitude"] = struct.unpack('<l', fit[offset:offset+4])[0]
                                elif definition_num == 3: # Symbol
                                    waypoints[-1]["symbol"] = struct.unpack('<H', fit[offset:offset+2])[0]
                                elif definition_num == 4: # Altitude
                                    waypoints[-1]["altitude"] = struct.unpack('<H', fit[offset:offset+2])[0]
                                elif definition_num == 253: # Timestamp
                                    waypoints.append({})
                                    waypoints[-1]["time"] = struct.unpack('<L', fit[offset:offset+4])[0]
                            elif global_num == 31: # Course
                                if definition_num == 5: # Name
                                    track_name = array_to_string(fit[offset:offset+16])
                                    tracks[track_name] = [];
                                    tracks[track_name].append([])
                            offset += field_size
                        if global_num == 0: # File Id
                            if file_type == 4: # Activity
                                track_name = norm_time(file_creation_time)
                                tracks[track_name] = [];
                                tracks[track_name].append([])
                        elif global_num == 19: # Lap
                            tracks[track_name].append([])
                    else:
                        record_fixed_ptr = (c_uint8 * record_fixed_size)(*fit[offset:offset+record_fixed_size])
                        record_fixed = cast(record_fixed_ptr, POINTER(RecordFixed))[0]
                        offset += record_fixed_size
                        
                        record_fields = []
                        for field_num in range(record_fixed.fieldsNum):
                            record_field_ptr = (c_uint8 * record_field_size)(*fit[offset:offset+record_field_size])
                            record_field = cast(record_field_ptr, POINTER(RecordField))[0]
                            offset += record_field_size
                            record_fields.append(record_field)
                            
                        record_definitions[record_header.localMessageType] = (record_fixed, record_fields)
                else:
                    _logger.debug("<Compressed Timestamp Header>")
        
            for waypoint in waypoints:
                name = waypoint.get("name", norm_time(file_creation_time))
                time = waypoint.get("time", file_creation_time)
                latitude = waypoint.get("latitude", 0x7FFFFFFF)
                longitude = waypoint.get("longitude", 0x7FFFFFFF)
                altitude = waypoint.get("altitude", 0xFFFF)
                symbol = waypoint.get("symbol", 0xFFFF)
                
                if latitude != 0x7FFFFFFF and longitude != 0x7FFFFFFF:
                    gpx += array.array('B', "  <wpt lat=\"")
                    gpx += array.array('B', str(norm_coord(latitude)))
                    gpx += array.array('B', "\" lon=\"")
                    gpx += array.array('B', str(norm_coord(longitude)))
                    gpx += array.array('B', "\">\n")
                    gpx += array.array('B', "    <name>")
                    gpx += array.array('B', name)
                    gpx += array.array('B', "</name>\n")
                    if altitude != 0xFFFF:
                        gpx += array.array('B', "    <ele>")
                        gpx += array.array('B', str(norm_alt(altitude)))
                        gpx += array.array('B', "</ele>\n")
                    gpx += array.array('B', "    <time>")
                    gpx += array.array('B', norm_time(time))
                    gpx += array.array('B', "</time>\n")
                    if symbol != 0xFFFF:
                        gpx += array.array('B', "    <sym>")
                        gpx += array.array('B', _symbols.get(symbol, "Flag, Red"))
                        gpx += array.array('B', "</sym>\n")
                    gpx += array.array('B', "  </wpt>\n")
            
            for name in tracks:
                gpx += array.array('B', "<trk>\n")
                gpx += array.array('B', "  <name>")
                gpx += array.array('B', name)
                gpx += array.array('B', "</name>\n")
                
                for segment in tracks[name]:
                    gpx += array.array('B', "  <trkseg>\n")
                    for point in segment:
                        time = point.get("time", file_creation_time)
                        latitude = point.get("latitude", 0x7FFFFFFF)
                        longitude = point.get("longitude", 0x7FFFFFFF)
                        altitude = point.get("altitude", 0xFFFF)
                        heart_rate = point.get("heart_rate", 0xFF)
                        cadence = point.get("cadence", 0xFF)
                        if latitude != 0x7FFFFFFF and longitude != 0x7FFFFFFF:
                            gpx += array.array('B', "    <trkpt lat=\"")
                            gpx += array.array('B', str(norm_coord(latitude)))
                            gpx += array.array('B', "\" lon=\"")
                            gpx += array.array('B', str(norm_coord(longitude)))
                            gpx += array.array('B', "\">\n")
                            if altitude != 0xFFFF:
                                gpx += array.array('B', "      <ele>")
                                gpx += array.array('B', str(norm_alt(altitude)))
                                gpx += array.array('B', "</ele>\n")
                            gpx += array.array('B', "      <time>")
                            gpx += array.array('B', norm_time(time))
                            gpx += array.array('B', "</time>\n")
                            if heart_rate != 0xFF or cadence != 0xFF:
                                gpx += array.array('B', "      <extensions>\n")
                                gpx += array.array('B', "        <gpxtpx:TrackPointExtension>\n")
                                if heart_rate != 0xFF:
                                    gpx += array.array('B', "          <gpxtpx:hr>")
                                    gpx += array.array('B', str(heart_rate))
                                    gpx += array.array('B', "</gpxtpx:hr>\n")
                                if cadence  != 0xFF:
                                    gpx += array.array('B', "          <gpxtpx:cad>")
                                    gpx += array.array('B', str(cadence))
                                    gpx += array.array('B', "</gpxtpx:cad>\n")
                                gpx += array.array('B', "        </gpxtpx:TrackPointExtension>\n")
                                gpx += array.array('B', "      </extensions>\n")
                            gpx += array.array('B', "    </trkpt>\n")
                    gpx += array.array('B', "  </trkseg>\n")
                gpx += array.array('B', "</trk>\n")
    gpx += array.array('B', "</gpx>\n")
    return gpx
