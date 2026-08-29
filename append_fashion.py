import csv

new_data = [
    ("RAGHAV AGNIHOTRI", "9554048363", "LEAD", "RAMP WALK"),
    ("RAASHA SINGH", "9569777508", "CO LEAD", "RAMP WALK"),
    ("TUSHAR BHATI", "9667701789", "MEMBER", "RAMP WALK"),
    ("KANIKA MAKHLOGA", "9045117204", "MEMBER", "RAMP WALK"),
    ("AVNI CHAUDHARY", "8126086155", "MEMBER", "RAMP WALK"),
    ("SAMEER RAI", "9955140482", "MEMBER", "RAMP WALK"),
    ("MEHAK SINGHAL", "7037067464", "MEMBER", "RAMP WALK"),
    ("MANYA GUPTA", "9219520740", "MEMBER", "RAMP WALK"),
    ("PARIDHI YADAV", "9773519221", "MEMBER", "RAMP WALK"),
    ("PRAGATI MISHRA", "8765004315", "MEMBER", "RAMP WALK"),
    ("PRASHASTI PANDEY", "8299366945", "MEMBER", "RAMP WALK"),
    ("SIDD JAIN", "9897748929", "MEMBER", "RAMP WALK"),
    ("TANISHKA VARSHNEY", "7017101708", "MEMBER", "RAMP WALK"),
    ("DIPIKA", "9266214104", "MEMBER", "RAMP WALK"),
    ("SHAGUN CHAUDHARY", "8449182504", "MEMBER", "RAMP WALK"),
    ("VARNIKA MALIK", "9258351802", "MEMBER", "RAMP WALK"),
    ("ANUSHKA SHUKLA", "9369294167", "MEMBER", "RAMP WALK"),
    ("SIDDHANT SINGH", "7081258233", "MEMBER", "RAMP WALK"),
    
    ("AKSHITA DHINGRA", "8218633410", "MEMBER", "COSTUME DESIGN"),
    ("ARYAN PUNDIR", "7017065590", "MEMBER", "COSTUME DESIGN"),
    ("BOBBY BIST", "7451908796", "MEMBER", "COSTUME DESIGN"),
    ("ISHITA GUPTA", "9555871339", "MEMBER", "COSTUME DESIGN"),
    ("KHUSHI VERMA", "7042151714", "MEMBER", "COSTUME DESIGN"),
    ("PRAGYA PANDEY", "8858927400", "MEMBER", "COSTUME DESIGN"),
    
    ("BOBBY BIST", "7451908796", "MEMBER", "MAKEUP ARTIST"),
    ("RASHI KUNWAR", "7982821046", "MEMBER", "MAKEUP ARTIST"),
    
    ("SAKSHI SINHA", "9971081246", "MEMBER", "ALL DOMAIN")
]

venue = "FASHION AND MODELING"
community_link = "https://chat.whatsapp.com/IIv2hPwrJuM78V0OgQneV1"
csv_path = r"c:\Users\amitm\OneDrive\Desktop\python script\contacts.csv"

# Note: AKSHA SHARMA was omitted from the list due to no number.

with open(csv_path, "a", encoding="utf-8", newline='') as f:
    writer = csv.writer(f)
    for name, phone, position, sub_venue in new_data:
        clean_phone = '91' + phone
        message = f"Hello {name}, congratulations to be part of VIBEESTA CREATIVE SOCIETY GLB 2026! You have been selected for the position of {position} for {venue} - {sub_venue}. Please join your respective groups from this community: {community_link}"
        writer.writerow([name, clean_phone, message])

print(f"Finished appending {len(new_data)} contacts.")
