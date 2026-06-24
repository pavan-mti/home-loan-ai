import re
import datetime

# ─── CONFIDENCE LEVELS ───
TABLE_EXACT = 0.99
BOUNDARY = 0.98
SAME_LINE = 0.97
ADDRESS = 0.96
NEXT_LINE = 0.95
EXACT = 0.95
MULTILINE = 0.94
FUZZY = 0.85
REGEX = 0.80

# ─── MULTILINE FIELDS ───
MULTILINE_FIELDS = {
    "postal_address_of_the_property",
    "owner_address",
    "purchaser_address",
    "property_description",
    "brief_description_of_property",
    "remarks",
    "comments",
    "legal_opinion",
    "mortgage_details",
    "construction_specifications"
}

# ─── BOUNDARY FIELDS ───
BOUNDARY_FIELDS = {
    "north_boundary",
    "south_boundary",
    "east_boundary",
    "west_boundary",
    "boundaries_north",
    "boundaries_south",
    "boundaries_east",
    "boundaries_west"
}

# ─── FIELD CLEANERS ───
def clean_name(val: str) -> str:
    if not val:
        return ""
    # Strip common title prefixes: Mr., Mrs., Ms., Sri, Smt., Dr., Shri
    val_clean = re.sub(r'\b(Mr|Mrs|Ms|Sri|Smt|Dr|Shri)\.?\s+', '', val, flags=re.IGNORECASE)
    # Normalize spaces: multiple spaces to single space
    val_clean = re.sub(r'\s+', ' ', val_clean).strip()
    return val_clean.title()

def clean_address_str(val: str) -> str:
    if not val:
        return ""
    # Normalize spaces and replace line breaks with comma
    val_clean = val.replace('\n', ', ').replace('\r', ', ')
    val_clean = re.sub(r'\s+', ' ', val_clean)
    # Remove duplicate commas/spaces
    val_clean = re.sub(r',(\s*,)+', ',', val_clean)
    val_clean = re.sub(r'\s*,\s*', ', ', val_clean)
    val_clean = re.sub(r',+', ',', val_clean)
    val_clean = val_clean.strip(', ')
    return val_clean

def clean_generic(val: str) -> str:
    if not val:
        return ""
    val_clean = re.sub(r'\s+', ' ', val)
    # Remove duplicate commas
    val_clean = re.sub(r',(\s*,)+', ',', val_clean)
    val_clean = re.sub(r'\s*,\s*', ', ', val_clean)
    return val_clean.strip()

FIELD_CLEANERS = {
    "name_of_the_owner_s": clean_name,
    "purchaser_name": clean_name,
    "developer_name": clean_name,
    "vendor_name": clean_name,
    "power_of_attorney_holder": clean_name,
    "witness_1": clean_name,
    "witness_2": clean_name,
    "valuer_name": clean_name,
    "owner_address": clean_address_str,
    "purchaser_address": clean_address_str,
    "residential_address": clean_address_str,
    "postal_address_of_the_property": clean_address_str,
}

# ─── FIELD VALIDATORS ───
def validate_date(val: str) -> bool:
    if not val:
        return False
    # Regex match first
    m = re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', val)
    if not m:
        m = re.search(r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', val)
    if not m:
        return False
    date_str = m.group(0)
    # Try parsing
    for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%y", "%d-%m-%y", "%Y-%m-%d", "%Y/%m/%d"]:
        try:
            datetime.datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            pass
    return False

def validate_pan(val: str) -> bool:
    if not val:
        return False
    val_clean = re.sub(r'\s+', '', val).upper()
    return bool(re.search(r'[A-Z]{5}[0-9]{4}[A-Z]', val_clean))

def validate_aadhaar(val: str) -> bool:
    if not val:
        return False
    val_clean = "".join(ch for ch in val if ch.isdigit())
    return len(val_clean) == 12

def validate_mobile(val: str) -> bool:
    if not val:
        return False
    digits = "".join(ch for ch in val if ch.isdigit())
    if len(digits) >= 10:
        return digits[-10][0] in "6789"
    return False

def validate_pincode(val: str) -> bool:
    if not val:
        return False
    digits = "".join(ch for ch in val if ch.isdigit())
    return len(digits) == 6

def validate_survey_no(val: str) -> bool:
    if not val:
        return False
    return len(val.strip()) > 2

FIELD_VALIDATORS = {
    "inspection_date": validate_date,
    "valuation_date": validate_date,
    "agreement_date": validate_date,
    "registration_date": validate_date,
    "sale_deed_date": validate_date,
    "possession_date": validate_date,
    "work_order_date": validate_date,
    "layout_approval_date": validate_date,
    "pan_number": validate_pan,
    "aadhar_number": validate_aadhaar,
    "pin_code": validate_pincode,
    "pincode": validate_pincode,
    "cell_number": validate_mobile,
    "purchaser_phone": validate_mobile,
    "survey_no": validate_survey_no,
    "survey_number": validate_survey_no,
}

# ─── ALIAS DICTIONARY ───
FIELD_LABELS_EXT = {
    # ─── PARTIES ───────────────────────────────────────────────────────────────
    "name_of_the_owner_s": [
        "Name of Owner", "Name of the Owner", "Name of the Owner(s)",
        "Owner Name", "Owner's Name", "Owners Name", "Name of Owners",
        "Applicant Name", "Borrower Name", "Mortgagor Name",
        "Land Owner Name", "Property Owner", "Title Holder",
        "Name of Proprietor", "Vendor Name", "First Party Name",
        "Land Owner", "Owner / Applicant", "Malik Ka Naam",
        "Bhu Swami", "Bhuswami", "Swami Ka Naam",
        "Name of the Vendor", "Seller Name", "Grantor Name",
        "Name of Applicant", "Customer Name", "Account Holder Name",
        "Naame of Owner", "Nmae of Owner", "Ownr Name",
        "Owenr Name", "Nam of Owner", "Onwer Name",
        # AOS-specific
        "First Party", "Land Owner / Vendor", "Vendor",
        "Name of the First Party", "FIRST PARTY / LAND OWNER / VENDOR",
        "Absolute Owner", "Peaceful Possessor",
        "W/o", "S/o", "D/o", "H/o",  # relation prefixes often parsed as labels
    ],

    "purchaser_name": [
        "Name of Purchaser", "Name of the Purchaser", "Purchaser Name",
        "Name of the Purchaser(s)", "Vendee Name", "Buyer Name",
        "Name of Buyer", "Name of Vendee", "Second Party Name",
        "Allottee Name", "Name of Allottee", "Transferee Name",
        "Name of Transferee", "Name of Borrower", "Loan Applicant",
        "Name of Applicant", "Co-Applicant Name", "Name of Co-Applicant",
        "Khareedaar Ka Naam", "Krideta", "Purchaser / Vendee",
        "Purchasr Name", "Purchaser Nmae", "Puchaser Name",
        # AOS-specific
        "Vendee", "IN FAVOUR OF", "In Favour Of", "In favor of",
        "Name of the Vendee", "VENDEE", "Purchaser / Allottee",
        "Second Party", "Name of Second Party",
    ],

    "developer_name": [
        "Developer Name", "Name of Developer", "Builder Name",
        "Name of Builder", "Promoter Name", "Name of Promoter",
        "Contractor Name", "Second Party", "Developer / Builder",
        "Construction Company", "Project Developer", "Society Name",
        "Name of Society", "Housing Society", "Nirman Karta",
        # AOS/WO-specific
        "Developer / Second Party", "DEVELOPER", "Name of the Developer",
        "M/s", "M/S", "Company Name", "Pvt Ltd", "Private Limited",
        "Second Party(ies)", "SECOND PARTY(IES)/CONTRACTOR(S)",
        "Contractor", "Registered Company", "Company",
        "Rep. by its Manager", "Authorised Signatory", "Authorized Signatory",
    ],

    "vendor_name": [
        "Vendor Name", "Name of Vendor", "Seller", "First Party",
        "Grantor", "Transferor", "Seller Name", "Vikretha",
        "Vikreta Ka Naam",
        # AOS-specific
        "VENDOR", "Vendor", "Land Owner / Vendor",
        "FIRST PARTY / LAND OWNER / VENDOR",
        "Sole Owner", "Absolute Owner and Peaceful Possessor",
        "Name of Land Owner",
    ],

    "power_of_attorney_holder": [
        "Power of Attorney Holder", "POA Holder", "GPA Holder",
        "General Power of Attorney Holder", "Attorney Holder",
        "Authorized Signatory", "Authorised Signatory",
        "PA Holder", "Attorney Name", "Agent Name",
        "Power of Attorney", "GPA", "GPOA",
        # AOS-specific
        "Development Agreement cum General Power of Attorney Holder",
        "DA cum GPA Holder", "REPRESENTED BY HER DEVELOPMENT AGREEMENT",
        "Rep. by Manager", "Manager", "Represented By",
        "Development Agreement cum GPA", "DA-GPA Holder",
        "Rep. by its Manager",
    ],

    "relation": [
        "W/o", "S/o", "D/o", "H/o", "C/o",
        "Wife of", "Son of", "Daughter of", "Husband of",
        "Care of", "Relative of",
        "Late", "L/o",
    ],

    "witness_1": [
        "Witness 1", "Witness No. 1", "First Witness", "Sakshi 1",
        "Gawah 1", "Witness-1", "W1", "Witness Name 1",
        "WITNESSES: 1", "Witnesses 1.", "Witnesss 1",
    ],

    "witness_2": [
        "Witness 2", "Witness No. 2", "Second Witness", "Sakshi 2",
        "Gawah 2", "Witness-2", "W2", "Witness Name 2",
        "WITNESSES: 2", "Witnesses 2.", "Witnesss 2",
    ],

    "aadhar_number": [
        "Aadhar No", "Aadhaar No", "Aadhar Number", "Aadhaar Number",
        "UIDAI No", "UID No", "Aadhar Card No", "Aadhaar Card Number",
        "Aadhar No.", "AADHAR NO", "AADHAAR NO", "Adhar No",
        "Aadhar ID", "UID", "Unique ID", "Aadhar", "Aadhaar",
        # AOS-specific OCR patterns
        "AADHAR NO:", "Aadhaar No.", "Aadhaar No:",
        "Aadhar No :", "(AADHAR NO:", "(Aadhaar No.",
        "Aadhar Number:", "UIDAI Number",
    ],

    "pan_number": [
        "PAN No", "PAN Number", "PAN Card No", "Permanent Account Number",
        "PAN No.", "PAN", "IT PAN", "Income Tax PAN",
        "PAN Card Number", "PAN-No", "PAN Num",
        "(PAN No.", "(PAN No:", "PAN No:", "PAN No :",
        "PAN Number:", "PAN Card No:",
    ],

    "age": [
        "Age", "Aged About", "Age of Person", "Date of Birth",
        "DOB", "Age (Years)", "Age in Years",
        "aged about", "Aged about", "aged",
        "years", "Age:", "Age :",
    ],

    "occupation": [
        "Occupation", "Profession", "Vyavsay", "Occupation/Profession",
        "Nature of Work", "Employment", "Job",
        "Occupation:", "Occupation :", "Business",
        "Pvt Employee", "Private Employee", "Government Employee",
        "Self Employed", "Retired", "Housewife",
    ],

    "cell_number": [
        "Cell", "Cell No", "Mobile", "Mobile No", "Phone No",
        "Contact No", "Mobile Number", "Phone Number",
        "Cell Number", "Contact Number", "Tel No", "Telephone No",
        "Ph No", "Mob No", "Contact", "Mobile / Phone",
        "Cell:", "Cell No:", "Cell No.",
        "Cell: 8008806408",  # OCR may pick up value inline
    ],

    "residential_address": [
        "Residential Address", "Address", "R/o", "Resident of",
        "Permanent Address", "Home Address", "Residing at",
        "Address of Owner", "Address of Applicant",
        "House Address", "Current Address", "Present Address",
        "Correspondence Address", "Niwas Sthal",
        "Resident of", "Residing at", "R/o.",
        "Address of Vendee", "Address of Vendor",
        "Residing", "Resident", "Resides at",
        "H. No.", "H No", "House No",
    ],

    # ─── PROPERTY IDENTIFICATION ───────────────────────────────────────────────
    "survey_no": [
        "Survey No", "Survey No.", "Survey Number", "Sy No",
        "Sy. No", "Survey Nos", "S.No", "S. No.",
        "Svy No", "Khasra No", "Khasra Number", "Plot Survey No",
        "Survey / Khasra No", "Dag No", "Daag No",
        "Bhoomi Survey No", "Field No", "Gunta No",
        "Hissa No", "Sub-Division No", "RS No", "TS No",
        "Revenue Survey No", "Sruvey No", "Survay No",
        "Survy No", "Survey N0",
        # AOS-specific
        "Survey Nos.", "Survey Nos", "in Survey Nos.",
        "Survey Nos. 90", "Sy Nos", "Survey No 90",
        "Survey No. 90", "Survey Nos.90",
        "90/ఄ", "92/ఄ",  # Telugu script survey numbers
    ],

    "plot_no": [
        "Plot No", "Plot No.", "Plot Number", "Plot Nos",
        "Door No", "Door No.", "House No", "House Number",
        "Door No / House No", "Door / House No",
        "Municipal No", "Municipal Door No", "Property No",
        "Flat No", "Unit No", "Shop No", "Site No",
        "Block No", "Lot No", "Premises No",
        "Bhukhand Sankhya", "Khasra Plot No",
        "Plt No", "Plto No", "Door Noo", "H No", "H. No",
        # AOS-specific
        "Door No.17-3-131", "Door No.17-3-131/B",
        "Door No 17-3-131", "Premises bearing Door No",
        "Municipal Premises Door No", "Municipal Premises",
        "Premises Door No", "Door No (Old)", "Door No (New)",
        "Old PTIN", "New PTIN",
    ],

    "ptin_no": [
        "PTIN No", "PTIN", "PTIN Number", "Property Tax ID",
        "Property Tax Identification No", "Tax ID No",
        "GHMC PTIN", "Municipal PTIN", "Patta No",
        # AOS-specific
        "PTIN No.", "PTIN:", "PTIN No:",
        "PTIN: 1220310604", "PTIN: 1221700489",
        "PTIN (Old)", "PTIN (New)", "Old PTIN", "New PTIN",
    ],

    "t_s_no_village": [
        "T.S. No", "T.S. No.", "TS No", "TS Number",
        "T.S. No / Village", "Village", "Village Name",
        "Gram", "Gaon", "Panchayat Village",
        "Revenue Village", "Mandal / Village", "Hobli",
        "T S No", "TS No / Village", "Township Survey No",
        "Town Survey No", "Municipal Survey No",
        "T.S No", "T.S.No", "TS. No",
        # AOS-specific
        "situated at", "Situated at", "situated at BANDLAGUDA",
        "Location", "Place", "Locality Name",
    ],

    "ward_taluka": [
        "Ward", "Taluka", "Ward / Taluka", "Ward/Taluka",
        "Taluk", "Tehsil", "Tahsil", "Tahasil",
        "Ward No", "Ward Number", "Revenue Taluka",
        "Mandal", "Circle", "Zone", "Division",
        "Municipal Ward", "Corporation Ward",
        "Wrd / Taluka", "Ward / Taluk",
        # AOS-specific
        "under GHMC", "GHMC", "GHMC Ramachandrapuram",
        "under GHMC Ramachandrapuram",
    ],

    "mandal_district": [
        "Mandal", "District", "Mandal / District", "Mandal/District",
        "Dist", "Dist.", "Revenue District", "Revenue Mandal",
        "Mandal Name", "District Name", "Zila",
        "Zilah", "Jilla", "Revenue Circle",
        "Tehsil / District", "Block / District",
        "Mandal / Dist", "Mandal-District",
        # AOS-specific
        "Sanga Reddy District", "Sangareddy District",
        "Sangareddy Dt", "Sangareddy", "Sanga Reddy",
        "K.V.Rangareddy District", "Rangareddy District",
        "Rangareddy Dt", "Medak", "Medak TG",
    ],

    "city_town": [
        "City", "City / Town", "Town", "City/Town",
        "Municipality", "Municipal Area", "Corporation",
        "Urban Area", "Nagar", "Sheher",
        "Gram Panchayat", "Taluk HQ", "District HQ",
        "City Name", "Town Name", "Locality",
        "Cty / Town", "Cit / Town",
        # AOS-specific
        "Hyderabad", "Bandlaguda", "BANDLAGUDA",
        "Narsingi", "Puppalaguda", "Patancheru",
        "Kokapet", "Goshala",
    ],

    "postal_address_of_the_property": [
        "Postal Address of the Property", "Property Address",
        "Address of Property", "Address of the Property",
        "Site Address", "Flat Address", "House Address",
        "Location Address", "Property Location",
        "Registered Address", "Situated At",
        "Postal Address", "Full Address",
        "Complete Address", "Asset Address",
        "Sampatti Ka Pata", "Postal Adress",
        "Proprty Address", "Addres of Property",
        # AOS-specific
        "situated at BANDLAGUDA", "Premises bearing",
        "in Premises bearing", "in Survey Nos.",
        "under GHMC Ramachandrapuram",
        "Sanga Reddy District, Telangana State",
        "Telangana State", "Telangana",
    ],

    "flat_no": [
        "Flat No", "Flat No.", "Flat Number", "Unit No",
        "Unit Number", "Apartment No", "Apartment Number",
        "Flat / Unit No", "Flat Nos", "Flat No (East)",
        "Flat No (West)", "Flat No (North)", "Flat No (South)",
        # AOS-specific
        "Semi-Finished Flat No.", "Semi-Finished Flat No",
        "Flat No.502", "Flat No.502(EAST)", "Flat 502",
        "Flat No 502", "Unit 502", "Flat No.502 (EAST)",
        "Semi-Finished Flat", "Flat No(East)", "Flat No(West)",
    ],

    "building_name": [
        "Building Name", "Project Name", "Name of Building",
        "Name of Project", "Apartment Name", "Complex Name",
        "Society Name", "Colony Name", "Layout Name",
        "Housing Project", "Scheme Name", "Tower Name",
        # AOS-specific
        "GBR Barcelona", "\"GBR Barcelona\"",
        "building names as", "building named as",
        "the building names as", "Residential Complex",
        "Name of Complex", "Project",
    ],

    "floor_no": [
        "Floor No", "Floor Number", "Floor", "Level",
        "Storey", "Floor / Level", "Ground Floor",
        "Stilt Floor", "Upper Floor", "Basement",
        "G+F", "Floor Nos",
        # AOS-specific
        "5th Floor", "5th floor", "Fifth Floor",
        "Stilt / Parking + Upper 5 Floors",
        "Stilt + Upper 5 Floors",
        "Upper 5 Floors",
        "G+5", "G + 5", "Stilt+5",
    ],

    "property_description": [
        "Brief Description of Property", "Description of Property",
        "Property Description", "Brief Description",
        "Property Details", "Asset Description",
        "Description of the Property", "Schedule of Property",
        "Schedule Property", "Property Particulars",
        "Nature of Property", "Type of Property",
        "Sampatti Ka Vivaran", "Description",
        "Proprty Description", "Descripton of Property",
        # AOS-specific
        "Open Plot", "Open Land Municipal Premises",
        "All that the", "All that the Open Land",
        "Semi-Finished Flat", "Residential Apartment",
        "Residential Complex",
    ],

    "schedule_of_property": [
        "Schedule of Property", "Schedule A Property",
        "Schedule B Property", "Schedule 'A'", "Schedule 'B'",
        "Schedule A", "Schedule B", "Property Schedule",
        "Schedule of the Property", "Anusoochi",
        "Schedule-A", "Schedule-B",
        # AOS-specific
        "SCHEDULE \"A\" PROPERTY", "SCHEDULE \"B\" PROPERTY",
        "Schedule A Property", "Schedule B Property",
        "SCHEDULE OF THE FLAT HEREBY SOLD",
        "Schedule of the Flat Hereby Sold",
        "SCHEDULE OF THE PROPERTY",
        "the Schedule", "Schedule Property",
    ],

    # ─── BOUNDARIES ───────────────────────────────────────────────────────────
    "boundaries_north": [
        "North", "North Boundary", "Bounded on North",
        "Northern Boundary", "N", "NORTH",
        "North Side", "North Direction",
        "As Per Deed (North)", "As Per Actuals (North)",
        "Uttar", "Uttari Seema", "Nroth", "Norht",
        "NORTH :", "NORTH:", "North :",
        # AOS-specific
        "Gayam Motor Works Pvt Ltd",  # the value, often parsed with key
        "Corridor.",  # flat north boundary value
    ],

    "boundaries_south": [
        "South", "South Boundary", "Bounded on South",
        "Southern Boundary", "S", "SOUTH",
        "South Side", "South Direction",
        "As Per Deed (South)", "As Per Actuals (South)",
        "Dakshin", "Dakshini Seema", "Soth", "Souht",
        "SOUTH :", "SOUTH:", "South :",
        # AOS-specific
        "Limitless Synergy Pvt Ltd",  # south boundary value
        "Open To Sky.",  # flat south boundary value
    ],

    "boundaries_east": [
        "East", "East Boundary", "Bounded on East",
        "Eastern Boundary", "E", "EAST",
        "East Side", "East Direction",
        "As Per Deed (East)", "As Per Actuals (East)",
        "Purv", "Purvi Seema", "Esst", "Eatst",
        "EAST :", "EAST:", "East :",
        # AOS-specific
        "30 Feet Wide Road",  # east boundary value (open plot)
        "Corridor & Staircase",  # east boundary value (flat)
    ],

    "boundaries_west": [
        "West", "West Boundary", "Bounded on West",
        "Western Boundary", "W", "WEST",
        "West Side", "West Direction",
        "As Per Deed (West)", "As Per Actuals (West)",
        "Paschim", "Pashchimi Seema", "Wets", "Weest",
        "WEST :", "WEST:", "West :",
        # AOS-specific
        "Sy No. 83 & 84", "Sy No 83 & 84",  # west boundary value
        "Duct & Lift",  # flat west boundary value
    ],

    "north_boundary": [
        "North", "North Boundary", "Northern Boundary",
        "N. Boundary", "Bounded North", "North Side",
        "North:", "NORTH:", "Uttar Seema",
        "NORTH : ", "NORTH :",
    ],

    "south_boundary": [
        "South", "South Boundary", "Southern Boundary",
        "S. Boundary", "Bounded South", "South Side",
        "South:", "SOUTH:", "Dakshin Seema",
        "SOUTH : ", "SOUTH :",
    ],

    "east_boundary": [
        "East", "East Boundary", "Eastern Boundary",
        "E. Boundary", "Bounded East", "East Side",
        "East:", "EAST:", "Purv Seema",
        "EAST : ", "EAST :",
    ],

    "west_boundary": [
        "West", "West Boundary", "Western Boundary",
        "W. Boundary", "Bounded West", "West Side",
        "West:", "WEST:", "Paschim Seema",
        "WEST : ", "WEST :",
    ],

    "boundaries_as_per_deed": [
        "As Per Deed", "As Per Sale Deed", "As Per Document",
        "Document Boundaries", "Deed Boundaries",
        "As Per Records", "As Per Title",
        "and bounded as follows", "bounded as follows:",
        "bounded as follows:-", "and bounded as follows:",
    ],

    "boundaries_as_per_actuals": [
        "As Per Actuals", "Actual Boundaries", "Physical Boundaries",
        "On Ground", "As Measured", "As Per Site",
        "As Per Inspection", "Physical Verification",
        "As per Actual", "As per actual measurement",
    ],

    # ─── DATES ────────────────────────────────────────────────────────────────
    "agreement_date": [
        "Agreement Date", "Date of Agreement", "Date of Execution",
        "Execution Date", "Date of This Agreement",
        "Agreement Dated", "Date:", "Dated:",
        "Made on", "Executed on", "Entered into on",
        # AOS-specific
        "made and executed on this", "executed on",
        "on this 17th day of Feb 2026",
        "on this", "Date: 17-02-2026", "Date: 17/02/2026",
        "FEB-17-2026", "17-02-2026", "17/02/2026",
        "Agreement dated:", "Agreement dated",
    ],

    "inspection_date": [
        "Date of Inspection", "Inspection Date", "Date of Site Visit",
        "Site Visit Date", "Date of Survey", "Survey Date",
        "Date of Physical Verification", "Visited On",
        "Inspection Dt", "Dt of Inspection",
        "Date of Field Visit", "Visited Date",
        "Nirikshan Tithi", "Date of Inspection:",
        "Dat of Inspection", "Date Of Inspecton",
    ],

    "valuation_date": [
        "Date of Valuation", "Valuation Date", "Date of Report",
        "Report Date", "As on Date", "Valued On",
        "Dt of Valuation", "Valuation Dt",
        "Date of Assessment", "Assessment Date",
        "Mulyankan Tithi", "Date of Valuation:",
        "Date of Valuaton", "Dat of Valuation",
    ],

    "registration_date": [
        "Registration Date", "Date of Registration",
        "Registered On", "Reg Date", "Date of Reg",
        "Date Registered", "Doc Date",
        # AOS-specific
        "dated", "Dated:", "Dated :", "dated 14-03-2023",
        "dated: 14.03.2023", "registered at", "Registered at",
    ],

    "sale_deed_date": [
        "Sale Deed Date", "Date of Sale Deed",
        "Date of Purchase", "Purchase Date",
        "Date of Acquisition", "Acquired On",
        # AOS-specific
        "vide document no.", "vide document no",
        "dated 14-03-2023", "dated: 14.03.2023",
    ],

    "possession_date": [
        "Date of Possession", "Possession Date",
        "Handover Date", "Date of Handover",
        "Date of Delivery", "Delivery Date",
        # AOS-specific
        "within 1 to 6 months", "within 1 to 6 months of",
        "handed over within", "Flat will be handed over",
    ],

    "work_order_date": [
        "Work Order Date", "Date of Work Order",
        "WO Date", "Work Order Dated",
        "Work Order Agreement Date",
        "made and executed on 17/02/2026",
        "in terms of Work Order dated",
        "Work Order dated:", "WO dated",
    ],

    # ─── AREAS ────────────────────────────────────────────────────────────────
    "built_up_area": [
        "Built Up Area", "Built-Up Area", "Builtup Area",
        "BUA", "Build Up Area", "Built Area",
        "Plinth Area", "Floor Area", "Carpet Area",
        "Super Built Up Area", "Super BUA", "Covered Area",
        "Total Built Up Area", "Total BUA",
        "Construction Area", "Constructed Area",
        "sq ft", "sq. ft", "sq feet", "sqft",
        "Sq Feet", "Sq.Ft", "Square Feet",
        "Nirman Kshetrafal", "Nirman Area",
        "Bult Up Area", "Buit Up Area", "Bulit Up Area",
        # AOS-specific
        "admeasuring 1130 sq. feet", "1130 sq. feet",
        "admeasuring", "sq. feet of built up area",
        "built up area (including common areas, balconies)",
        "including common areas, balconies",
        "sq feet of built up area",
        "admeasuring 1130", "1130 sq ft",
    ],

    "land_area": [
        "Land Area", "Plot Area", "Site Area",
        "Total Land Area", "Extent of Land",
        "Land Extent", "Total Extent", "Admeasuring",
        "Measuring Area", "Land Admeasuring",
        "Plot Size", "Site Size", "Land Size",
        "Total Area", "Open Plot Area",
        "sq yards", "sq. yards", "sqyards",
        "Sq Yards", "Square Yards",
        "sq mtrs", "sq. mtrs", "sqmtrs",
        "Sq Meters", "Square Meters",
        "Acres", "Guntas", "Cents",
        "Bhumi Kshetrafal", "Zameen Ka Rukba",
        "Lnd Area", "Lad Area",
        # AOS-specific
        "790 sq. yards", "790 Square yards",
        "admeasuring area 790 sq. yards",
        "660.44 Sq Mtrs", "660.44 Sq. Mtrs",
        "total extent of admeasuring 790",
        "out of total extent of admeasuring",
        "total extent", "Extent",
    ],

    "undivided_share_of_land": [
        "Undivided Share of Land", "UDS", "UDS of Land",
        "Undivided Share", "UDS Area", "Land UDS",
        "Share of Land", "Proportionate Share",
        "Proportionate Land Share", "Common Land Share",
        "Apairth Bhoomi Hissa", "UDS in Sq Yards",
        "UDS in Sq Mtrs",
        # AOS-specific
        "undivided share of land admeasuring",
        "undivided share of land admeasuring 42.61 sq. yards",
        "42.61 sq. yards", "42.61 sq yards",
        "equivalent to 35.627 Sq. meters",
        "35.627 Sq. meters", "35.627 Sq Mtrs",
        "undivided share of land",
        "along with an undivided share of land",
    ],

    "carpet_area": [
        "Carpet Area", "Net Floor Area", "Net Area",
        "Usable Area", "Living Area",
        "Galicha Kshetrafal",
    ],

    "plinth_area": [
        "Plinth Area", "PA", "Ground Coverage",
        "Footprint Area", "Floor Plate",
    ],

    "super_built_up_area": [
        "Super Built Up Area", "Super BUA", "SBUA",
        "Gross Area", "Total Floor Area",
        "Including Common Areas", "Including Common Areas and Balconies",
        # AOS-specific
        "including common areas, balconies",
        "sq. feet of built up area (including common areas, balconies)",
    ],

    "parking": [
        "Parking", "Car Parking", "No of Parking",
        "Parking Space", "Covered Parking",
        "Open Parking", "Stilt Parking",
        "One Car Parking", "Two Car Parking",
        "Parking Slots", "Garage",
        # AOS-specific
        "One Car Parking", "1 Car Parking",
        "and One Car Parking",
        "Stilt / Parking", "Stilt Parking",
    ],

    # ─── FINANCIAL ────────────────────────────────────────────────────────────
    "total_sale_consideration": [
        "Total Sale Consideration", "Sale Consideration",
        "Total Consideration", "Sale Price",
        "Total Sale Price", "Purchase Price",
        "Total Purchase Price", "Agreement Value",
        "Contract Value", "Deal Amount",
        "Total Amount", "Property Value",
        "Vikray Mulya", "Keemat",
        "Ttal Sale Consideration", "Sale Consiedration",
        # AOS-specific
        "total sale consideration of Rs.",
        "Rs. 28,25,000/-", "28,25,000/-",
        "Rupees Twenty-Eight Lakh Twenty-Five Only",
        "Rs.28,25,000/-",
        "total sale consideration",
        "for a total sale consideration of",
    ],

    "advance_amount": [
        "Advance Amount", "Advance", "Token Amount",
        "Booking Amount", "Earnest Money",
        "Earnest Money Deposit", "EMD",
        "Initial Payment", "Upfront Payment",
        "Advance Payment", "Part Payment",
        "Advance Paid", "Amount Paid",
        "Peshgi", "Bayana", "Advance Sum",
        # AOS-specific
        "Rs. 2,82,500/-", "2,82,500/-",
        "Rupees Two Lakh Eighty-Two Thousand Five Hundred",
        "advance by way of online Transfer",
        "paid a sum of", "sum of Rs.",
        "Towards advance", "towards advance",
        "advance as part sale consideration",
    ],

    "balance_amount": [
        "Balance Amount", "Balance Sale Consideration",
        "Remaining Amount", "Balance Payment",
        "Balance Due", "Outstanding Amount",
        "Remaining Balance", "Balance to be Paid",
        "Due Amount", "Pending Amount",
        "Shesh Rakam", "Baaki Rakam",
        # AOS-specific
        "Rs. 25,42,500/-", "25,42,500/-",
        "Rupees Twenty-Five Lakh Forty-Two Thousand Five Hundred Only",
        "remaining balance of Rs.",
        "balance sale consideration",
        "subjected to Loan", "will be subjected to Loan",
    ],

    "loan_amount": [
        "Loan Amount", "Loan", "Mortgage Amount",
        "Home Loan Amount", "Finance Amount",
        "Bank Loan", "Term Loan", "Housing Loan",
        "Credit Amount", "Financed Amount",
        "HL Amount", "Loan Sanctioned",
        "Rin Rakam", "Karz",
        # AOS-specific
        "loan amount from FI/Bank",
        "The loan amount from FI/Bank",
        "Loan", "subjected to Loan",
        "loan will be directly released",
        "balance amount in favor of",
    ],

    "market_value": [
        "Market Value", "Fair Market Value", "FMV",
        "Current Market Value", "Present Market Value",
        "Market Rate", "Market Price",
        "Realizable Value", "Prevailing Market Value",
        "Value as per Market", "Open Market Value",
        "Estimated Market Value", "MV",
        "Bazaar Mulya", "Bajar Mulya",
        "Mkt Value", "Markt Value",
    ],

    "distress_value": [
        "Distress Value", "Forced Sale Value", "FSV",
        "Liquidation Value", "Auction Value",
        "Forced Liquidation Value", "FLV",
        "Minimum Realizable Value",
        "Vikray Mulya (Vivastha)", "FSV Value",
        "Distress Val", "Distres Value",
    ],

    "guideline_value": [
        "Guideline Value", "Government Value", "Govt Value",
        "Ready Reckoner Rate", "Circle Rate",
        "Stamp Duty Value", "Registration Value",
        "Sub-Registrar Value", "SRO Value",
        "Collector's Rate", "Guidance Value",
        "Basic Value", "Standard Value",
        "DC Rate", "Collector Rate",
        "Sarkari Mulya", "Sarkaari Dar",
        "Guidline Value", "Guideline Val",
    ],

    "work_order_value": [
        "Work Order Value", "Work Order Amount",
        "Total Work Value", "Contract Amount",
        "Construction Cost", "Work Value",
        "Total", "Total Amount",
        "TOTAL", "Total Value",
        # AOS/WO-specific
        "Rs. 28,25,000/-", "28,25,000/-",
        "Rupees Twenty-Eight Lakh Twenty-Five Thousand Only",
        "above works to the tune of Rs.",
        "tune of Rs.", "VALUE", "Item Value",
        "3,00,000", "3,50,000",  # individual work order line values
    ],

    "stamp_duty_value": [
        "Stamp Duty Value", "Stamp Duty",
        "Stamp Duty Paid", "Registration Charges",
        "Stamp Duty & Registration", "SD Value",
        # AOS-specific (stamp paper)
        "₹ 0000200/-", "0000200/-",
        "ZERO ZERO ZERO ZERO TWO ZERO ZERO",
        "Stamp Paper Value", "Non-Judicial Stamp",
        "India Non Judicial", "STATE BANK OF INDIA",
    ],

    # ─── LEGAL / DOCUMENT DETAILS ─────────────────────────────────────────────
    "document_no": [
        "Document No", "Document Number", "Doc No",
        "Doc. No", "Doc Number", "Registration No",
        "Registration Number", "Reg No", "Reg. No",
        "Deed No", "Sale Deed No", "Agreement No",
        "Document Bearing No", "Document No.",
        "Dastavez Sankhya",
        # AOS-specific
        "document bearing No.7085 of 2024",
        "document bearing No.8610 of 2023",
        "No. 8610 of 2023", "No. 7085 of 2024",
        "document no. 8610-2023", "vide document no.",
        "document bearing No", "document no",
        "File No.", "File No",
        "3816242", "48/2023",
    ],

    "book_no": [
        "Book No", "Book Number", "Book-I", "Book 1",
        "Book-II", "Book 2", "Book No.",
        "Register Book", "Volume No",
        # AOS-specific
        "Book-1", "Book-I", "Book 1",
        "Book-1, and Dated:", "Book-I,",
    ],

    "registered_at": [
        "Registered At", "Registered At RO",
        "Registration Office", "Sub Registrar Office",
        "SRO", "Registrar Office", "R.O.",
        "Office of Sub-Registrar", "Panjiyan Karyalay",
        # AOS-specific
        "registered at R.O Sangareddy",
        "registered at RO Sanga Reddy",
        "registered at RO Sangareddy",
        "R.O Sangareddy", "R.O. Sangareddy",
        "RO Sangareddy", "Sanga Reddy R.O.",
    ],

    "sale_deed_no": [
        "Sale Deed No", "Sale Deed Number", "Deed No",
        "Deed Number", "Sale Deed Document No",
        "Document No of Sale Deed",
        "Vikray Patra Sankhya",
        # AOS-specific
        "8610 of 2023", "No. 8610 of 2023",
        "vide document bearing No. 8610 of 2023",
        "Sale Deed vide document no. 8610-2023",
        "registered Sale Deed vide document no.",
    ],

    "development_agreement": [
        "Development Agreement", "DA",
        "Development Agreement cum GPA",
        "Joint Development Agreement", "JDA",
        "Development Agreement No", "DA No",
        # AOS-specific
        "Development Agreement cum General Power of Attorney",
        "DA cum GPA", "vide registered Development Agreement",
        "document bearing No.7085 of 2024",
        "7085 of 2024", "DA-GPA",
        "Development Agreement cum General Power of Attorney document bearing No.",
    ],

    "building_permission": [
        "Building Permission", "Building Plan Approval",
        "Construction Permission", "BP No",
        "Building Permit No", "Plan No",
        "Permit No", "Permission No",
        "File No", "GHMC File No",
        "BP File No", "Permit Number",
        # AOS-specific
        "File No. 012383/GHMC/6103/SLP2/2023-BP",
        "012383/GHMC/6103/SLP2/2023-BP",
        "permit No. 5741/GHMC/SLP/2024-BP",
        "5741/GHMC/SLP/2024-BP",
        "dt. 04-03-2024",
        "building permission from the Greater Hyderabad Municipal Corporation",
        "obtained building permission",
        "GHMC building permission",
    ],

    "layout_approval": [
        "Layout Approval", "Approved Layout",
        "Layout Plan Approval", "LP No",
        "Layout Permission", "Planning Permission",
        "Date of Issue and Validity of Layout of Approved Map / Plan",
        "Approved Map / Plan",
        "Layout Approval No", "Approved Plan",
        "mutually agreed plan", "as per the mutually agreed plan",
    ],

    "layout_approving_authority": [
        "Approved Map / Plan Issuing Authority",
        "Layout Issuing Authority",
        "Plan Sanctioning Authority",
        "Sanctioned By", "Approved By",
        "GHMC", "HMDA", "DTCP", "BDA", "CMDA",
        "Municipality", "Gram Panchayat",
        "Planning Authority", "Development Authority",
        # AOS-specific
        "Greater Hyderabad Municipal Corporation",
        "GHMC Ramachandrapuram",
        "obtained construction permission from GHMC Ramachandrapuram",
    ],

    "mortgage_details": [
        "Mortgage Details", "Mortgage", "Mortgage Information",
        "Encumbrance Details", "Encumbrances",
        "Charge Details", "Lien Details",
        "Hypothecation Details", "Pledge Details",
        "Mortgage Status", "Existing Mortgage",
        "Bandhan Vivaran", "Bhaar Vivaran",
        "Mortgge Details", "Mortgage Detials",
        # AOS-specific
        "not subject to any attachments",
        "not done anything whereby the said property may be subject to",
        "litigations, mortgages, tenancy claims",
        "dues or lien of any court",
        "legal embargo", "legal impediment",
        "Nil Encumbrance", "free from encumbrance",
    ],

    "legal_opinion": [
        "Legal Opinion", "Legal Report", "Advocate Opinion",
        "Lawyer Opinion", "Title Opinion", "Title Certificate",
        "Title Report", "Legal Clearance", "Legal Status",
        "Legal Scrutiny", "Legal Verification",
        "Advocate's Opinion", "Title Search Report",
        "Legal Opinion Certificate", "Vidhik Raay",
        "Legl Opinion", "Legel Opinion",
        # AOS-specific
        "not entered into any prior agreement for sale",
        "no agreement of sale at present",
        "neither any legal embargo",
        "no legal impediment",
        "title to the said property",
        "perfect title",
    ],

    "encumbrance_certificate": [
        "Encumbrance Certificate", "EC",
        "Encumbrance Certificate Details",
        "EC Details", "EC Period",
        "Nil Encumbrance", "Clear EC",
        "Bhaar Praman Patra",
    ],

    "patta_details": [
        "Patta Details", "Patta No", "Patta Number",
        "Patta", "Revenue Record", "Pahani",
        "Adangal", "RoR", "Record of Rights",
        "Land Records", "Revenue Extract",
    ],

    "prohibited_properties_details": [
        "Prohibited Properties Details", "Prohibited Property",
        "Prohibited Details", "Schedule Tribe Land",
        "Agency Area", "Inam Land", "Endowment Land",
        "Government Land", "Wakf Land", "Forest Land",
        "CRZ Area", "Notified Area", "Embargo",
        "Prohibited Transaction", "Transfer Prohibition",
        # AOS-specific
        "Schedule of Property is not subject matter of any kind of prohibition",
        "not subject matter of any kind of prohibition",
        "prohibition of Transfer of properties",
        "Act 9 of 1977", "prohibition",
    ],

    # ─── PROPERTY CHARACTERISTICS ─────────────────────────────────────────────
    "property_type": [
        "Property Type", "Type of Property", "Nature of Property",
        "Asset Type", "Property Category",
        "Residential", "Commercial", "Industrial",
        "Agricultural", "Mixed Use", "Open Plot",
        "Flat", "Apartment", "House", "Villa",
        "Independent House", "Row House", "Bungalow",
        "Shop", "Office", "Warehouse", "Factory",
        "Sampatti Ka Prakar",
        "Prperty Type", "Properrty Type",
        # AOS-specific
        "Semi-Finished Flat", "Residential Apartment",
        "Residential Complex", "Open Land",
        "Open Plot in Municipal Premises",
    ],

    "occupancy_status": [
        "Occupancy Status", "Occupation Status",
        "Occupancy", "Occupied By", "Occupied Status",
        "Possession Status", "Tenant Status",
        "Self Occupied", "Rented", "Vacant",
        "Owner Occupied", "Tenant Occupied",
        "Status of Occupancy", "Use Status",
        "Adhikaar Sthiti", "Qabza Sthiti",
        "Occupncy Status", "Ocupancy Status",
        # AOS-specific
        "vacant and peaceful physical possession",
        "peaceful physical possession",
        "Possession", "Semi-Finished",
    ],

    "age_of_property": [
        "Age of Property", "Age of Building",
        "Age of Structure", "Age of Construction",
        "Year of Construction", "Year Built",
        "Construction Year", "Built Year",
        "Age (Years)", "Building Age",
        "Remaining Life", "Expected Life",
        "Useful Life", "Life of Building",
        "Sampatti Ki Aayu", "Bhavan Ki Aayu",
        "Age of Proprty", "Age Of Buildng",
    ],

    "construction_type": [
        "Construction Type", "Type of Construction",
        "Structure Type", "Building Type",
        "RCC", "Load Bearing", "Steel Structure",
        "Framed Structure", "Composite",
        "Kutcha", "Pucca", "Semi-Pucca",
        "Construction Quality", "Quality of Construction",
        "Nirman Prakar",
        # AOS-specific
        "Residential Apartment Stilt / Parking + Upper 5 Floors",
        "construction of residential Apartment",
        "for constructing Residential Complex",
    ],

    "no_of_floors": [
        "No of Floors", "Number of Floors",
        "Total Floors", "No. of Floors",
        "G+", "Stilt + Upper Floors",
        "Floors", "No of Storeys",
        "Number of Storeys", "Total Storeys",
        # AOS-specific
        "Stilt / Parking + Upper 5 Floors",
        "Upper 5 Floors", "5 Floors",
        "G+5", "Stilt+5", "5th Floor",
    ],

    "road_width": [
        "Road Width", "Width of Road", "Road Facing",
        "Road Access", "Approach Road",
        "Road Size", "Road Frontage",
        "Feet Wide Road", "Meter Wide Road",
        "30 Feet Wide Road", "40 Feet Wide Road",
        # AOS-specific
        "30 Feet Wide Road",  # east boundary value
        "30 Feet Wide", "30ft Road",
    ],

    # ─── VALUATION SPECIFICS ──────────────────────────────────────────────────
    "purpose_of_valuation": [
        "Purpose for which the valuation is made",
        "Purpose of Valuation", "Purpose",
        "Reason for Valuation", "Valuation Purpose",
        "Object of Valuation", "Valuation For",
        "Loan Purpose", "Mortgage Purpose",
        "Mulyankan Ka Uddeshya",
        "Purpse of Valuation", "Purpose of Valuaton",
        # AOS/WO-specific
        "Home Loan", "Housing Loan",
        "Bank Loan Purpose", "SBI Loan",
    ],

    "list_of_documents": [
        "List of Documents", "Documents Produced",
        "Documents Submitted", "List of Documents Produced for Perusal",
        "Documents Verified", "Documents for Perusal",
        "Title Documents", "Property Documents",
        "Supporting Documents", "Documents Furnished",
        "Dastavej Soochi",
        # AOS-specific
        "requisite documents", "all the requisite documents",
        "requisite formalities and certificates",
    ],

    "rate_per_sqft": [
        "Rate per Sq Ft", "Rate / Sq Ft",
        "Rate Per Square Feet", "Per Sqft Rate",
        "Market Rate per Sqft", "Prevailing Rate",
        "Rate", "Unit Rate",
        "Dar Pratishath Varg Feet",
    ],

    "rate_per_sqyard": [
        "Rate per Sq Yard", "Rate / Sq Yard",
        "Rate Per Square Yard", "Per Sqyard Rate",
        "Land Rate", "Plot Rate",
        "Rate per Sqyd",
    ],

    # ─── WORK ORDER SPECIFICS ─────────────────────────────────────────────────
    "item_description": [
        "Item", "Item Description", "Work Item",
        "Description of Work", "Particulars",
        "Nature of Work", "Scope of Work",
        "ITEM", "Work Description",
        # WO-specific
        "S.No. ITEM VALUE", "Sl.No", "ITEM",
        "item wise", "item-wise",
    ],

    "item_value": [
        "Value", "Amount", "Cost",
        "Item Value", "Item Cost", "Work Cost",
        "Rate", "Total Value", "VALUE",
        "Item Amount",
        # WO-specific
        "3,00,000", "3,50,000", "2,50,000",
        "1,50,000", "2,25,000", "1,00,000",
        "2,00,000",
    ],

    "serial_no": [
        "S.No.", "S.No", "Sr. No", "Serial No",
        "Serial Number", "Sl No", "Sl. No",
        "No.", "No", "Item No", "S No",
        # WO-specific
        "S.No. (table column)", "1", "2", "3",
    ],

    "flooring": [
        "Flooring", "Floor Work", "Floor Finishing",
        "Tiles", "Marble", "Granite Flooring",
        "Floor Type",
        "Flooring - 3,00,000",
    ],

    "wall_finishing": [
        "Internal & External Wall Finishing in Lappam",
        "Wall Finishing", "Wall Plastering",
        "Internal Finishing", "External Finishing",
        "Lappam Finishing", "Wall Work",
        "Internal & External Wall Finishing",
        "Lappam", "Wall Finishing in Lappam",
    ],

    "painting": [
        "Painting", "Paint Work", "Interior Painting",
        "Exterior Painting", "Paint",
        "Painting - 3,50,000",
    ],

    "doors_windows": [
        "Doors/windows Shutters in Best Teak Wood",
        "Doors and Windows", "Doors / Windows",
        "Door Work", "Window Work", "Shutters",
        "Teak Wood Doors",
        "Doors/windows Shutters",
        "Best Teak Wood Doors",
    ],

    "kitchen_shelves": [
        "Kitchen and Bed Rooms Selves",
        "Kitchen Shelves", "Bedroom Shelves",
        "Shelves", "Cupboards", "Wardrobes",
        "Kitchen and Bed Rooms Shelves",
        "Kitchen Selves", "Bed Rooms Selves",
    ],

    "kitchen_platform": [
        "Kitchen Platform", "Kitchen Counter",
        "Kitchen Work", "Modular Kitchen",
        "Kitchen Platform - 1,50,000",
    ],

    "pop_ceiling": [
        "POP Ceiling with light fittings",
        "POP Ceiling", "False Ceiling",
        "Ceiling Work", "Gypsum Ceiling",
        "POP Ceiling with light fittings",
        "Light Fittings", "POP with light",
    ],

    "upvc_windows": [
        "UPVC Windows and Sliding Doors",
        "UPVC Windows", "UPVC", "Sliding Doors",
        "Aluminum Windows", "Window Frames",
        "UPVC Windows and Sliding Doors - 2,25,000",
    ],

    "electrical_works": [
        "Electrical Works", "Electrical Work",
        "Wiring", "Electrical Fitting",
        "Electrical Installation", "Electrification",
        "Electrical Works - 2,50,000",
    ],

    "electrical_piping": [
        "Electrical Piping & Wring",
        "Electrical Piping & Wiring",
        "Electrical Piping", "Piping",
        "Conduit Work", "Electrical Conduit",
        "Electrical Piping & Wring - 1,00,000",
    ],

    "sanitary_fittings": [
        "Quality sanitary fittings",
        "Sanitary Fittings", "Plumbing",
        "Sanitary Work", "Plumbing Work",
        "Sanitation", "Water Fittings",
        "Quality Sanitary Fittings",
        "Sanitary - 2,00,000",
    ],

    "pooja_room": [
        "Pooja Room Area", "Pooja Room",
        "Prayer Room", "Puja Ghar",
        "Pooja Room Area - 1,00,000",
    ],

    "bathroom_fittings": [
        "Bathroom Fittings", "Bath Fittings",
        "WC Fittings", "Toilet Fittings",
        "Bathroom Accessories",
        "Bathroom Fittings - 1,00,000",
    ],

    # ─── BANK / LOAN DETAILS ─────────────────────────────────────────────────
    "bank_name": [
        "Bank Name", "Name of Bank", "Lender Name",
        "Financial Institution", "FI Name",
        "Housing Finance Company", "HFC",
        "NBFC Name", "Lending Institution",
        "Bank / FI", "State Bank of India", "SBI",
        # AOS/WO-specific
        "The Manager, State Bank of India, Hyderabad",
        "State Bank of India, Hyderabad",
        "SBI Hyderabad", "FI/Bank",
        "loan amount from FI/Bank",
        "To The Manager, State Bank of India",
    ],

    "branch_name": [
        "Branch Name", "Branch", "Bank Branch",
        "Branch Office", "Branch Location",
        "Branch Code",
        # AOS/WO-specific
        "State Bank of India, Hyderabad",
        "Hyderabad Branch",
    ],

    "loan_account_no": [
        "Loan Account No", "Loan No",
        "Account Number", "Loan Account Number",
        "Reference No", "File No",
        "Application No", "Case No",
    ],

    "valuer_name": [
        "Valuer Name", "Name of Valuer",
        "Empanelled Valuer", "Registered Valuer",
        "Approved Valuer", "Panel Valuer",
        "Valuation Officer", "Valuer",
    ],

    "report_no": [
        "Report No", "Report Number", "Valuation Report No",
        "Reference No", "File Reference",
        "Case Reference", "Job No",
    ],

    # ─── LOCATION ─────────────────────────────────────────────────────────────
    "state": [
        "State", "State Name", "Province",
        "Telangana", "Andhra Pradesh", "Karnataka",
        "Rajya", "Prantheeya",
        "Telangana State", "T.S.",
        "Telangana State.", "TS",
    ],

    "pin_code": [
        "PIN Code", "Pin Code", "Postal Code",
        "ZIP Code", "PIN", "Pincode",
        "Area Code", "Postal PIN",
        # AOS-specific
        "500089", "502305", "502319", "507209",
    ],

    "locality": [
        "Locality", "Area", "Neighborhood",
        "Colony", "Nagar", "Extension",
        "Layout", "Sector", "Phase",
        "Mohalla", "Basti",
        # AOS-specific
        "Goutham Nagar Colony", "Narsingi",
        "Puppalaguda", "Bandlaguda",
        "BANDLAGUDA", "Bhanoor Village",
        "Chinna Korukondi", "Kokapet Road",
        "Srikirshna Goshala",
    ],

    "landmark": [
        "Landmark", "Near", "Opposite to",
        "Adjacent to", "Nearby Landmark",
        # AOS-specific
        "Srikirshna Goshala", "Kokapet Road",
        "7Hills (Pws)",
    ],

    # ─── RECEIPT / PAYMENT ───────────────────────────────────────────────────
    "receipt_no": [
        "Receipt No", "Receipt Number",
        "Payment Receipt", "Challan No",
        "Transaction ID", "Transaction Reference",
        "UTR No", "IMPS Ref No",
        "RECEIPT", "Receipt",
    ],

    "payment_mode": [
        "Payment Mode", "Mode of Payment",
        "By Online Transfer", "NEFT", "RTGS",
        "IMPS", "Cheque", "Cash", "DD",
        "Online Transfer", "Net Banking",
        # AOS-specific
        "by way of online Transfer",
        "by way of Online",
        "online transfer", "Online Transfer",
        "by way of online",
    ],

    "receipt_amount": [
        "Receipt Amount", "Amount Received",
        "Received Amount", "Amount Acknowledged",
        "Sum Received", "Received a sum of",
        # AOS-specific
        "Received a sum of Rs. 2,82,500/-",
        "Rs. 2,82,500/-", "2,82,500/-",
        "Two Lakh Eighty-Two Thousand Five Hundred",
    ],

    "no_objection_certificate": [
        "No Objection Certificate", "NOC",
        "No Objection", "NOC Letter",
        "No Objection Letter", "Clearance Letter",
        "Clearance Certificate", "Anaapatty Praman Patra",
        # AOS-specific (page 6)
        "No objection to getting the additional works",
        "We have no objection",
        "no objection to getting",
        "no objection to releasing the balance amount",
        "SUBJ: No objection",
        "Subject: No objection",
        "Subject: No Objection",
        "SUBJ: No Objection",
    ],
    
    # ─── BACKWARD COMPATIBILITY ───
    "high_middle_poor": ["High / Middle / Poor", "High Middle Poor", "High/Middle/Poor"],
    "urban_semi_urban_rural": ["Urban / Semi Urban / Rural", "Urban/Semi Urban/Rural", "Urban Semi Urban Rural"],
    "coming_under_municipality_limits_village_panchayat_corporation": ["Coming under Municipality limits / Village Panchayat/ Corporation", "Municipality limits"],
    "whether_covered_under_any_state_central_govt_enactments_e_g_urban_land_ceiling_act_or_notified_under_agency_area_scheduled_area_cantonment_area": ["Whether covered under any State / Central Govt. enactments (e.g. Urban Land Ceiling Act) or notified under agency area / scheduled area / cantonment area"],
}
