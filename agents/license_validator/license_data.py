# License code to permit validation data
# Source: license_code_permit_validations.xlsx

LICENSE_DATA = [
    {"license_number": "1045907", "license_code": "A",   "permits": ["Plumbing", "Pressure Vessel"]},
    {"license_number": "1092820", "license_code": "B",   "permits": ["Bldg-Alter/Repair", "Electrical", "EV Charger", "HVAC", "Plumbing", "Pressure Vessel"]},
    {"license_number": "1000061", "license_code": "C-4", "permits": ["Pressure Vessel"]},
    {"license_number": "1002480", "license_code": "C-7", "permits": ["Electrical"]},
    {"license_number": "1057929", "license_code": "C-9",  "permits": ["Bldg-Alter/Repair"]},
    {"license_number": "1045907", "license_code": "C10", "permits": ["Electrical", "EV charger", "Pressure Vessel"]},
    {"license_number": "808879",  "license_code": "C11", "permits": ["Elevator", "Pressure Vessel"]},
    {"license_number": "1042659", "license_code": "C16", "permits": ["Fire Sprinkler", "Pressure Vessel"]},
    {"license_number": "1000169", "license_code": "C20", "permits": ["Electrical", "HVAC", "Pressure Vessel"]},
    {"license_number": "1001177", "license_code": "C34", "permits": ["Pressure Vessel"]},
    {"license_number": "",        "license_code": "C35", "permits": ["Bldg-Alter/Repair"]},
    {"license_number": "1000098", "license_code": "C36", "permits": ["Plumbing", "Pressure Vessel"]},
    {"license_number": "999993",  "license_code": "C38", "permits": ["Electrical", "Pressure Vessel"]},
    {"license_number": "",        "license_code": "C39", "permits": ["Bldg-Alter/Repair"]},
    {"license_number": "1006709", "license_code": "C42", "permits": ["Pressure Vessel"]},
    {"license_number": "1071509", "license_code": "C43", "permits": ["HVAC"]},
    {"license_number": "1000366", "license_code": "C46", "permits": ["Plumbing"]},
    {"license_number": "1015870", "license_code": "C55", "permits": ["Pressure Vessel"]},
    {"license_number": "957084",  "license_code": "C61", "permits": ["Pressure Vessel"]},
    {"license_number": "", "license_code": "D21", "permits": ["Pressure Vessel"]},
    {"license_number": "1000868", "license_code": "D34", "permits": ["Pressure Vessel"]},
    {"license_number": "1001661", "license_code": "D35", "permits": ["Pressure Vessel"]},
    {"license_number": "",  "license_code": "D40", "permits": ["Pressure Vessel"]},
    {"license_number": "248449",  "license_code": "D57", "permits": ["Pressure Vessel"]},
]

# Only include licenses that have a license number (skipping C35, C39)
TESTABLE_LICENSES = [l for l in LICENSE_DATA if l["license_number"]]