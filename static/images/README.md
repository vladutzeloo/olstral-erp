# Company Logo for PDFs

This folder contains company branding assets used in PDF documents.

## Adding Your Company Logo

To add your company logo to Purchase Orders and Receipt PDFs:

1. **Prepare your logo:**
   - Format: PNG (recommended for best quality)
   - Recommended dimensions: 400x200 pixels (2:1 ratio)
   - Background: Transparent preferred
   - File size: Keep under 500KB for best performance

2. **Add the logo file:**
   - Save your logo as `company_logo.png` in this folder
   - Path: `static/images/company_logo.png`

3. **File name is important:**
   - Must be named exactly: `company_logo.png`
   - Case-sensitive on Linux servers

4. **Test the PDFs:**
   - Generate a Purchase Order PDF
   - Generate a Receipt PDF
   - Verify the logo appears correctly

## Customizing Company Information

To customize the company name, address, and contact info in PDFs:

1. Open `pdf_generator.py`
2. Find the `create_header()` method
3. Update the company_info section:
   ```python
   company_info = Paragraph(
       "<b>YOUR COMPANY NAME</b><br/>"
       "Your Address Line 1<br/>"
       "Your Address Line 2<br/>"
       "Phone: Your Phone<br/>"
       "Email: your@email.com",
       self.styles['InfoText']
   )
   ```

## Troubleshooting

**Logo not appearing:**
- Check file name is exactly `company_logo.png`
- Verify file is in `static/images/` folder
- Check file permissions (must be readable by web server)
- Clear browser cache and regenerate PDF

**Logo looks distorted:**
- Use a 2:1 aspect ratio (e.g., 400x200, 600x300)
- Save as high-quality PNG
- Avoid very large files (keep under 500KB)

**Logo too big/small:**
- Edit `pdf_generator.py`
- In `get_logo()` method, adjust the width parameter:
  ```python
  return Image(logo_path, width=2*inch, height=1*inch)
  ```
