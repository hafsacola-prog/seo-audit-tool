import io
import urllib.parse
from bs4 import BeautifulSoup
import requests
import streamlit as st
import tldextract
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================================
# 🔗 APNI GOOGLE SHEET KA WEBHOOK URL YAHAN PASTE KAREIN:
# ==========================================================
GOOGLE_SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwetciC31Q-zSgylj7cFxnMN1IUs-B_-bSq3Zfs1Je3AHomk8Qg-IHKlWy2xeI1pyGw4g/exec"

st.set_page_config(page_title="SEO & Technical Audit Tool", layout="wide")
st.title("SEO & Technical Audit Tool")
st.write("Enter your details and website URL to generate an in-depth audit report with a branded PDF download.")

def get_google_pagespeed(target_url):
    endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={urllib.parse.quote(target_url)}&strategy=mobile"
    try:
        res = requests.get(endpoint, timeout=30).json()
        lighthouse = res.get("lighthouseResult", {})
        cats = lighthouse.get("categories", {})
        perf_score = int(cats.get("performance", {}).get("score", 0) * 100) if cats.get("performance") else "N/A"
        seo_score = int(cats.get("seo", {}).get("score", 0) * 100) if cats.get("seo") else "N/A"
        audits = lighthouse.get("audits", {})
        fcp = audits.get("first-contentful-paint", {}).get("displayValue", "N/A")
        lcp = audits.get("largest-contentful-paint", {}).get("displayValue", "N/A")
        cls_val = audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A")
        return {"perf": perf_score, "seo": seo_score, "fcp": fcp, "lcp": lcp, "cls": cls_val}
    except Exception:
        return {"perf": "N/A", "seo": "N/A", "fcp": "N/A", "lcp": "N/A", "cls": "N/A"}

def build_pdf_report(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'))
    sec_style = ParagraphStyle('SStyle', parent=styles['Heading2'], fontSize=11, leading=15, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=4)
    c_text = ParagraphStyle('CText', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor('#334155'))
    c_bold = ParagraphStyle('CBold', parent=styles['Normal'], fontSize=8.5, leading=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#0F172A'))

    story = []

    h_data = [[Paragraph("AGENCY SEO AND TECHNICAL AUDIT REPORT", title_style), Paragraph("CONFIDENTIAL REPORT", c_bold)]]
    h_tbl = Table(h_data, colWidths=[380, 160])
    h_tbl.setStyle(TableStyle([('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor('#2563EB')), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    story.append(h_tbl)
    story.append(Spacer(1, 8))

    m_data = [
        [Paragraph("Target URL:", c_bold), Paragraph(data['url'], c_text), Paragraph("Audited For:", c_bold), Paragraph(data['client'], c_text)],
        [Paragraph("Domain:", c_bold), Paragraph(data['domain'], c_text), Paragraph("Email:", c_bold), Paragraph(data['email'], c_text)]
    ]
    m_tbl = Table(m_data, colWidths=[70, 200, 70, 200])
    m_tbl.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')), ('PADDING', (0,0), (-1,-1), 5), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))]))
    story.append(m_tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Technical Performance and Core Web Vitals", sec_style))
    t_data = [
        [Paragraph("Metric", c_bold), Paragraph("Observed Value", c_bold), Paragraph("Industry Benchmark", c_bold)],
        [Paragraph("Mobile Performance Score", c_text), Paragraph(f"{data['psi']['perf']}/100", c_bold), Paragraph("Target: 80+ / 100", c_text)],
        [Paragraph("Google Lighthouse SEO Score", c_text), Paragraph(f"{data['psi']['seo']}/100", c_bold), Paragraph("Target: 90+ / 100", c_text)],
        [Paragraph("First Contentful Paint (FCP)", c_text), Paragraph(str(data['psi']['fcp']), c_text), Paragraph("Under 1.8s (Good)", c_text)],
        [Paragraph("Largest Contentful Paint (LCP)", c_text), Paragraph(str(data['psi']['lcp']), c_text), Paragraph("Under 2.5s (Good)", c_text)],
        [Paragraph("Cumulative Layout Shift (CLS)", c_text), Paragraph(str(data['psi']['cls']), c_text), Paragraph("Under 0.1 (Optimal)", c_text)],
        [Paragraph("SSL / HTTPS Security", c_text), Paragraph(data['ssl'], c_text), Paragraph("HTTPS Encryption Required", c_text)],
        [Paragraph("Canonical Tag Verification", c_text), Paragraph(data['canonical'], c_text), Paragraph("Self-referencing canonical", c_text)]
    ]
    t_tbl = Table(t_data, colWidths=[180, 180, 180])
    t_tbl.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEF2F6')), ('PADDING', (0,0), (-1,-1), 4.5), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))]))
    story.append(t_tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. On-Page Architecture and Content Analysis", sec_style))
    o_data = [
        [Paragraph("Element", c_bold), Paragraph("Audit Finding", c_bold), Paragraph("Recommendation", c_bold)],
        [Paragraph("Page Title", c_text), Paragraph(f"{data['title'][:50]} ({data['title_len']} chars)", c_text), Paragraph("Optimal (50-60 chars)" if 50 <= data['title_len'] <= 60 else "Adjust to 50-60 chars", c_text)],
        [Paragraph("Meta Description", c_text), Paragraph(f"{data['desc'][:50]} ({data['desc_len']} chars)", c_text), Paragraph("Optimal (140-160 chars)" if 140 <= data['desc_len'] <= 160 else "Adjust to 140-160 chars", c_text)],
        [Paragraph("H1 Tag Count", c_text), Paragraph(f"{data['h1_count']} found", c_text), Paragraph("Optimal" if data['h1_count'] == 1 else "Exactly 1 primary H1 required", c_text)],
        [Paragraph("Primary H1 Text", c_text), Paragraph(data['primary_h1'][:65], c_text), Paragraph("Include target keyword", c_text)],
        [Paragraph("Image Optimization", c_text), Paragraph(f"{data['missing_alt']} of {data['total_img']} missing ALT", c_text), Paragraph("Optimal" if data['missing_alt'] == 0 else "Add keyword-rich ALT tags", c_text)],
        [Paragraph("Link Distribution", c_text), Paragraph(f"Internal: {data['int_links']} | External: {data['ext_links']}", c_text), Paragraph("Maintain topical silo structure", c_text)]
    ]
    o_tbl = Table(o_data, colWidths=[130, 230, 180])
    o_tbl.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEF2F6')), ('PADDING', (0,0), (-1,-1), 4.5), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))]))
    story.append(o_tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph("3. Priority Action Plan", sec_style))
    act_rows = []
    if data['h1_count'] != 1:
        act_rows.append([Paragraph(f"- Heading Issue: Found {data['h1_count']} H1 tags. Consolidate into 1 primary H1 tag.", c_text)])
    if not (50 <= data['title_len'] <= 60):
        act_rows.append([Paragraph(f"- Title Optimization: Current length is {data['title_len']} chars. Adjust to 50-60 characters.", c_text)])
    if not (140 <= data['desc_len'] <= 160):
        act_rows.append([Paragraph(f"- Description Optimization: Current length is {data['desc_len']} chars. Target 140-160 characters.", c_text)])
    if data['missing_alt'] > 0:
        act_rows.append([Paragraph(f"- Image SEO: Add descriptive ALT attributes to {data['missing_alt']} images.", c_text)])
    if isinstance(data['psi']['perf'], int) and data['psi']['perf'] < 70:
        act_rows.append([Paragraph(f"- Speed Optimization: Mobile score is {data['psi']['perf']}/100. Compress media assets and defer scripts.", c_text)])
    if not act_rows:
        act_rows.append([Paragraph("- Solid Baseline: No critical technical blockers detected. Proceed with backlink acquisition.", c_text)])

    act_tbl = Table(act_rows, colWidths=[540])
    act_tbl.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')), ('PADDING', (0,0), (-1,-1), 5), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))]))
    story.append(act_tbl)
    story.append(Spacer(1, 10))

    pitch_row = [[Paragraph("Need help implementing these fixes? We specialize in technical SEO, high-authority link building, and on-page optimization. Reply to our message to schedule a strategy call.", c_text)]]
    pitch_tbl = Table(pitch_row, colWidths=[540])
    pitch_tbl.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')), ('PADDING', (0,0), (-1,-1), 6), ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#3B82F6'))]))
    story.append(pitch_tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

with st.form("audit_form"):
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name (Optional)", placeholder="Talha")
    with col2:
        last_name = st.text_input("Last Name (Optional)", placeholder="Mahmood")
    email = st.text_input("Business Email *", placeholder="name@company.com")
    website_url = st.text_input("Website URL *", placeholder="https://example.com")
    submit_btn = st.form_submit_button("Generate Audit Report")

if submit_btn:
    if not email.strip() or "@" not in email or "." not in email:
        st.error("Please enter a valid Business Email address.")
    elif not website_url.strip():
        st.error("Please enter a valid Website URL.")
    else:
        target_url = website_url.strip()
        if not target_url.startswith("http"):
            target_url = "https://" + target_url
        user_display_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else "Website Owner"

        with st.spinner(f"Analyzing {target_url}... Generating branded PDF report."):
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            try:
                response = requests.get(target_url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, "html.parser")
            except Exception as e:
                st.error(f"Target website error: {e}")
                st.stop()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            meta_desc = desc_tag.get("content", "").strip() if desc_tag else ""
            h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
            canonical = soup.find("link", rel="canonical")
            canonical_url = canonical.get("href") if canonical else "Missing"
            images = soup.find_all("img")
            missing_alt = [img.get("src", "Unknown") for img in images if not img.get("alt") or img.get("alt").strip() == ""]
            base_domain = tldextract.extract(target_url).registered_domain

            internal_links, external_links = [], []
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith(("#", "javascript:", "mailto:", "tel:")) or not href:
                    continue
                link_domain = tldextract.extract(href).registered_domain
                if not link_domain or link_domain == base_domain:
                    internal_links.append(href)
                else:
                    external_links.append(href)

            psi_data = get_google_pagespeed(target_url)

            # --- LEAD AUTO-SAVE TO GOOGLE SHEET ---
            if GOOGLE_SHEET_WEBHOOK_URL and "script.google.com" in GOOGLE_SHEET_WEBHOOK_URL:
                try:
                    sheet_payload = {
                        "name": user_display_name,
                        "email": email,
                        "url": target_url,
                        "perf_score": psi_data['perf'],
                        "seo_score": psi_data['seo'],
                        "h1_count": len(h1_tags),
                        "missing_alt": len(missing_alt)
                    }
                    requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=sheet_payload, timeout=6)
                except Exception:
                    pass

            st.success(f"Audit completed successfully for {user_display_name}!")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Performance", f"{psi_data['perf']}/100")
            c2.metric("Lighthouse SEO", f"{psi_data['seo']}/100")
            c3.metric("H1 Tags", len(h1_tags))
            c4.metric("Missing ALT", len(missing_alt))

            pdf_payload = {
                'client': user_display_name,
                'email': email,
                'url': target_url,
                'domain': base_domain,
                'psi': psi_data,
                'ssl': 'Active (Secure)' if target_url.startswith('https') else 'Missing (Insecure)',
                'canonical': canonical_url,
                'title': title if title else "Not Specified",
                'title_len': len(title),
                'desc': meta_desc if meta_desc else "Not Specified",
                'desc_len': len(meta_desc),
                'h1_count': len(h1_tags),
                'primary_h1': h1_tags[0] if h1_tags else "None detected",
                'total_img': len(images),
                'missing_alt': len(missing_alt),
                'int_links': len(internal_links),
                'ext_links': len(external_links)
            }

            pdf_file_bytes = build_pdf_report(pdf_payload)
            st.download_button(
                label="Download Branded SEO Audit Report (PDF)",
                data=pdf_file_bytes,
                file_name=f"SEO_Audit_{base_domain}.pdf",
                mime="application/pdf"
            )
