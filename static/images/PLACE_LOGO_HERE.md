# ⚠️ ADD YOUR COMPANY LOGO HERE

## Instructions:

1. **Save your company logo as:** `company_logo.png`
2. **Place it in this folder:** `static/images/`
3. **Full path should be:** `static/images/company_logo.png`

## Logo Requirements:

- **Format:** PNG (recommended for transparency)
- **Recommended size:** 400 x 200 pixels (2:1 aspect ratio)
- **Background:** Transparent PNG preferred
- **File size:** Keep under 500 KB for best performance
- **File name:** MUST be exactly `company_logo.png` (case-sensitive)

## How to Add Your Logo:

### On Windows:
```
1. Find your logo file (must be PNG format)
2. Rename it to: company_logo.png
3. Copy it to: static\images\company_logo.png
4. Restart the app
5. Generate a PDF to see your logo
```

### On Linux/Mac:
```
1. Find your logo file (must be PNG format)
2. Rename it to: company_logo.png
3. Copy it to: static/images/company_logo.png
4. Restart the app
5. Generate a PDF to see your logo
```

## Testing:

After adding the logo:
1. Go to any Purchase Order
2. Click "📄 Download PDF"
3. Your logo should appear at the top of the PDF

## Current Company Information in PDFs:

```
OLSTRAL
VGP PARK BRASOV – HALL A
Bucegi Street, No. 2
500053 Brasov
Romania
```

## Troubleshooting:

**Logo not appearing?**
- Check file name is exactly `company_logo.png`
- Check file is in `static/images/` folder
- Check file is valid PNG format
- Try clearing browser cache
- Restart the Flask app

**Logo looks distorted?**
- Use 2:1 aspect ratio (width:height)
- Recommended: 400x200, 600x300, or 800x400 pixels

**Logo too big/small?**
- Edit `pdf_generator.py`
- Find: `def get_logo(self, width=2*inch):`
- Change `width=2*inch` to adjust size
- For example: `width=3*inch` for larger logo
