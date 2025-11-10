import os
import re
import pandas as pd
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance

# ✅ 1. Set up Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

folder_path = r"C:\Users\ASUS\UniBonds"
image_files = [os.path.join(folder_path, f"page_{i}.webp") for i in range(40, 290)]

# ✅ Output CSV
OUTPUT_CSV = "finalt.csv"

# ✅ 3. Preprocess image for better OCR
def preprocess_image(image_path):
    try:
        img = Image.open(image_path)
        img = img.convert("L")
        img = img.filter(ImageFilter.MedianFilter())
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        return img
    except Exception as e:
        print(f"⚠️ Error reading {image_path}: {e}")
        return None

# ✅ 4. Extract fields from text block
def extract_fields(text):
    # First non-empty line assumed to be company name
    lines_nonempty = [line.strip() for line in text.splitlines() if line.strip()]
    company = lines_nonempty[0] if lines_nonempty else ""
    text = re.sub(r'\s+', ' ', text)

    entry = {
        "Company Name": company,
        "Membership No": "",
        "Contact Name": "",
        "Address": "",
        "Telephone": "",
        "Mobile": "",
        "Email": "",
        "Website": "",
        "Category": "",
        "Profile": ""
    }

    patterns = {
        "Membership No": r'Membership\s*No[:>\.\s]*([A-Z0-9-]+)',
        "Contact Name": r'Contact\s*Name[:>\.\s]*(.*?)(?=Communication|Address|Telephone|Mobile|Email|Website|Category|Profile|$)',
        "Address": r'Communication\s*Address[:>\.\s]*(.*?)(?=Telephone|Mobile|Email|Website|Category|Profile|$)',
        "Telephone": r'Telephone[:>\.\s]*(.*?)(?=Mobile|Email|Website|Category|Profile|$)',
        "Mobile": r'Mobile[:>\.\s]*(.*?)(?=Email|Website|Category|Profile|$)',
        "Email": r'[\w\.-]+@[\w\.-]+',
        "Website": r'Website[:>\.\s]*(\S+)',
        "Category": r'Category[:>\.\s]*(.*?)(?=Profile|$)',
        "Profile": r'Company\s*Brief\s*Profile[:>\.\s]*(.*)'
    }

    for field, pattern in patterns.items():
        if field == "Email":
            emails = re.findall(pattern, text)
            entry[field] = ", ".join(set(emails))
        else:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entry[field] = match.group(1).strip(" :>.")

    return entry

# ✅ 5. Process all images
records = []
for i, img_path in enumerate(image_files, start=1):
    print(f"[{i}/{len(image_files)}] Processing {img_path}...")
    processed_img = preprocess_image(img_path)
    if processed_img is None:
        continue

    ocr_text = pytesseract.image_to_string(processed_img, config="--psm 6")
    lines = ocr_text.splitlines()
    idx = []
    for i, line in enumerate(lines):
        if re.search(r"Membership No", line, flags=re.IGNORECASE):
            # Check if the previous line is blank (only whitespace or empty)
            if i > 0 and lines[i-1].strip() == "":
                idx.append(i - 2)
            else:
                idx.append(i - 1)
    idx.append(len(lines))
    company_blocks = ["\n".join(lines[idx[i]:idx[i+1]-1]) for i in range(len(idx)-1)]

    for block in company_blocks:
        entry = extract_fields(block)
        if entry["Company Name"] or entry["Membership No"]:
            records.append(entry)
# ✅ 6. Convert to CSV
if records:
    df = pd.DataFrame(records)
    df.replace({r'\n': ' ', r',': ' '}, regex=True, inplace=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"\n✅ Extraction completed successfully! Data saved to: {OUTPUT_CSV}")
    print(f"📊 Total companies extracted: {len(df)}")
else:
    print("\n⚠️ No valid company data found. Check OCR output or image clarity.")
