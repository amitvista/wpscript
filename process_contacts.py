import pandas as pd
import re

def parse_and_append_contacts(raw_file, csv_file):
    # Read raw file
    with open(raw_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_data = []
    
    # Message template
    template = "Hello {Name}, regarding your interest in *{Interest}*: You had filled the google form to the Vibeesta Creative Society GLB (official creative society of GL Bajaj, encompassing Film making, Fashion, Choreography, Music, PR, Tech, etc.). Join our Whatsapp community for further processes. https://chat.whatsapp.com/KcvR2jfB9jB5I1hNweW93U"

    for line in lines:
        if not line.strip() or line.startswith('| :') or 'Whatsapp Number' in line:
            continue
            
        parts = [p.strip() for p in line.split('|')]
        # Parts will look like ['', 'Name', 'Phone', 'Interest', ''] due to leading/trailing pipes
        
        if len(parts) >= 4:
            name = parts[1]
            phone = parts[2]
            interest = parts[3]
            
            if not name or not phone:
                continue

            # Clean phone number (remove spaces, - etc)
            clean_phone = re.sub(r'\D', '', phone)
            
            # Add 91 prefix if length is 10
            if len(clean_phone) == 10:
                clean_phone = '91' + clean_phone
            
            message = template.format(Name=name, Interest=interest)
            
            new_data.append({
                'Name': name,
                'Phone': clean_phone,
                'Message': message
            })
    
    if new_data:
        df_new = pd.DataFrame(new_data)
        # Append to csv without header
        df_new.to_csv(csv_file, mode='a', header=False, index=False)
        print(f"Successfully appended {len(new_data)} contacts to {csv_file}")
    else:
        print("No valid contacts found to append.")

if __name__ == "__main__":
    raw_file = "new_contacts_raw.txt"
    contacts_file = "contacts.csv"
    parse_and_append_contacts(raw_file, contacts_file)
