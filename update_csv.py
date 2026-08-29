import pandas as pd
import re

contacts_raw = """
Aayush kansal	9528561277	Management
Amreshwar Singh	7457985646	Music performance
Shaurya tiwari	7065649910	tech
Yash Sharma	8178717474	PR and Social media
Ashish Kumar Singh	9334594802	tech
Sneha Vashisht	7838549641	PR and Social media
Siddhant Singh	7081258233	Fashion and modeling
Adarsh	9670861678	Film making
Deepesh Ojha	8545030877	Film making
Akshay Bhati	9389413541	Fashion and modeling
Akshay Mishra	7307278154	Film making
Aryan Pundir	7017065590	Fashion and modeling
Vaibhav saxena	7253841722	Film making
Akash kumar	7739727408	Fashion and modeling
Pranav bhaiiii😎	9464087349	PR and Social media
"""

template = "Hello {Name}, regarding your interest in *{Interest}*: You had filled the google form to the Vibeesta Creative Society GLB (official creative society of GL Bajaj, encompassing Film making, Fashion, Choreography, Music, PR, Tech, etc.). Join our Whatsapp community for further processes. https://chat.whatsapp.com/KcvR2jfB9jB5I1hNweW93U"

csv_path = r"c:\Users\amitm\OneDrive\Desktop\python script\contacts.csv"

# Read existing file to comment out
with open(csv_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if i == 0: # Header
        new_lines.append(line)
        continue
    if not line.strip() or line.startswith('#'):
        new_lines.append(line)
    else:
        new_lines.append('#' + line)

# Parse new contacts
for line in contacts_raw.strip().split('\n'):
    parts = line.split('\t')
    if len(parts) == 3:
        name = parts[0].strip()
        phone = parts[1].strip()
        interest = parts[2].strip()
        
        clean_phone = re.sub(r'\D', '', phone)
        if len(clean_phone) == 10:
            clean_phone = '91' + clean_phone
            
        message = template.format(Name=name, Interest=interest)
        new_lines.append(f'{name},{clean_phone},"{message}"\n')

# Write back
with open(csv_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Updated contacts.csv successfully.")
