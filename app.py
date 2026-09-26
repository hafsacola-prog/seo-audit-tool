import io
import urllib.parse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
import streamlit as st
import tldextract
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ==========================================================
# AGENCY BRANDING SETTINGS
# ==========================================================
AGENCY_NAME = "RankCentre SEO & Digital Outreach"
AGENCY_EMAIL = "contact@rankcentre.net"
AGENCY_PHONE = "+92 300 1234567"
AGENCY_WEBSITE = "https://rankcentre.net"
AGENCY_ADDRESS = "Office 402, Business Arcade, Lahore / Gujrat, Pakistan"

# Google Sheet Webhook URL
GOOGLE_SHEET_WEBHOOK_URL = "YAHAN_APNA_WEBHOOK_URL_PASTE_KAREIN"

st.set_page_config(page_title="Executive SEO & Technical Audit Engine", layout="wide")
st.title("Agency SEO & Technical Audit Suite")
st.write("Enter your details and website URL to generate an in-depth visual audit report with branded PDF download.")

def generate_health_donut_chart(overall_score):
    fig, ax = plt.subplots(figsize=(2.4, 2.4), subplot_kw=dict(aspect="equal"))
    score = max(0, min(100, int(overall_score)))
    remaining = 100 - score
    chart_color = '#10B981' if score >= 80 else ('#F59E0B' if score >= 50 else '#EF4444')
    
    ax.pie(
        [score, remaining],
        colors=[chart_color, '#E2E8F0'],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2)
    )
    ax.text(0, 0, f"{score}%", ha='center', va='center', fontsize=20, fontweight='bold', color='#0F172A')
    ax.text(0, -0.32, "HEALTH", ha='center', va='center', fontsize=8, fontweight='bold', color='#64748B')
    
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=160)
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_metrics_bar_chart(links_internal, links_external, img_total, img_missing):
    fig, ax = plt.subplots(figsize=(3.8, 2.2))
    categories = ['Ext Links', 'Int Links', 'Missing ALT', 'Images']
    values = [links_external, links_internal, img_missing, img_total]
    bar_colors = ['#6366F1', '#3B82F6', '#EF4444' if img_missing > 0 else '#10B981', '#06B6D4']
    
    bars = ax.barh(categories, values, color=bar_colors, height=0.55)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CBD5E1')
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.tick_params(axis='both', which='both', labelsize=8, colors='#475569')
    
    max_val = max(values) if values and max(values) > 0 else 1
    for bar in bars:
        width = bar.get_width()
        ax.text(width + (max_val * 0.03), bar.get_y() + bar.get_height() / 2,
                f'{int(width)}', ha='left', va='center', fontsize=8, fontweight='bold', color='#1E293B')
    
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=160)
    plt.close(fig)
    buf.seek(0)
    return buf

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
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32)
    styles = getSampleStyleSheet()

    c_primary = colors.HexColor('#1E3A8A')
    c_dark = colors.HexColor('#0F172A')
    c_slate = colors.HexColor('#475569')
    c_light = colors.HexColor('#F8FAFC')
    c_border = colors.HexColor('#E2E8F0')

    title_agency = ParagraphStyle('TAgency', parent=styles['Heading1'], fontSize=14, leading=17, fontName='Helvetica-Bold', textColor=c_primary)
    agency_sub = ParagraphStyle('ASub', parent=styles['Normal'], fontSize=8, leading=10, textColor=c_slate)
    sec_title = ParagraphStyle('STitle', parent=styles['Heading2'], fontSize=10.5, leading=14, fontName='Helvetica-Bold', textColor=c_dark, spaceBefore=6, spaceAfter=4)
    cell_txt = ParagraphStyle('CTxt', parent=styles['Normal'], fontSize=8, leading=10.5, textColor=c_dark)
    cell_bold = ParagraphStyle('CBld', parent=styles['Normal'], fontSize=8, leading=10.5, fontName='Helvetica-Bold', textColor=c_dark)
    pitch_txt = ParagraphStyle('PTxt', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#1E3A8A'))

    story = []

    # 1. Clean Agency Letterhead Table (Zero HTML Tags)
    header_table_data = [
        [Paragraph(AGENCY_NAME, title_agency), Paragraph("Email:", cell_bold), Paragraph(AGENCY_EMAIL, agency_sub)],
        [Paragraph("Search Engine Optimization & Outreach Consultancy", agency_sub), Paragraph("Phone:", cell_bold), Paragraph(AGENCY_PHONE, agency_sub)],
        [Paragraph("", agency_sub), Paragraph("Website:", cell_bold), Paragraph(AGENCY_WEBSITE, agency_sub)],
        [Paragraph("", agency_sub), Paragraph("HQ:", cell_bold), Paragraph(AGENCY_ADDRESS, agency_sub)]
    ]
    hdr_table = Table(header_table_data, colWidths=[290, 50, 208])
    hdr_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, c_primary),
    ]))
    story.append(hdr_table)
    story.append(Spacer(1, 8))

    # 2. Metadata Info
    meta_info = [
        [Paragraph("Target URL:", cell_bold), Paragraph(data['url'], cell_txt), Paragraph("Client Contact:", cell_bold), Paragraph(data['client'], cell_txt)],
        [Paragraph("Root Domain:", cell_bold), Paragraph(data['domain'], cell_txt), Paragraph("Client Email:", cell_bold), Paragraph(data['email'], cell_txt)]
    ]
    meta_table = Table(meta_info, colWidths=[70, 204, 75, 199])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F1F5F9')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # 3. Overall Site Health & Visual Diagnostics
    story.append(Paragraph("Executive Performance & Structural Diagnostics", sec_title))
    
    calc_perf = data['psi']['perf'] if isinstance(data['psi']['perf'], int) else 65
    calc_seo = data['psi']['seo'] if isinstance(data['psi']['seo'], int) else 75
    h1_penalty = 15 if data['h1_count'] != 1 else 0
    img_penalty = 10 if data['missing_alt'] > 0 else 0
    calculated_health = max(10, int(((calc_perf * 0.4) + (calc_seo * 0.6)) - h1_penalty - img_penalty))

    donut_chart_buffer = generate_health_donut_chart(calculated_health)
    bar_chart_buffer = generate_metrics_bar_chart(data['int_links'], data['ext_links'], data['total_img'], data['missing_alt'])

    donut_img = Image(donut_chart_buffer, width=115, height=115)
    bar_img = Image(bar_chart_buffer, width=195, height=115)

    verdict_subtable_data = [
        [Paragraph("Audit Verdict Summary", cell_bold), Paragraph("", cell_txt)],
        [Paragraph("Mobile Performance:", cell_txt), Paragraph(f"{data['psi']['perf']}/100", cell_bold)],
        [Paragraph("Lighthouse SEO:", cell_txt), Paragraph(f"{data['psi']['seo']}/100", cell_bold)],
        [Paragraph("HTTPS Security:", cell_txt), Paragraph(data['ssl'], cell_txt)],
        [Paragraph("Canonical Mapping:", cell_txt), Paragraph(data['canonical'], cell_txt)]
    ]
    verdict_subtable = Table(verdict_subtable_data, colWidths=[110, 100])
    verdict_subtable.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    health_summary_card = [[donut_img, verdict_subtable, bar_img]]
    diag_table = Table(health_summary_card, colWidths=[120, 220, 208])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 8))

    # 4. Technical Core Web Vitals Table
    story.append(Paragraph("1. Core Web Vitals & Loading Metrics", sec_title))
    t_data = [
        [Paragraph("Metric", cell_bold), Paragraph("Observed Value", cell_bold), Paragraph("Benchmark", cell_bold)],
        [Paragraph("First Contentful Paint (FCP)", cell_txt), Paragraph(str(data['psi']['fcp']), cell_txt), Paragraph("Under 1.8s (Fast)", cell_txt)],
        [Paragraph("Largest Contentful Paint (LCP)", cell_txt), Paragraph(str(data['psi']['lcp']), cell_txt), Paragraph("Under 2.5s (Target)", cell_txt)],
        [Paragraph("Cumulative Layout Shift (CLS)", cell_txt), Paragraph(str(data['psi']['cls']), cell_txt), Paragraph("Under 0.1 (Optimal)", cell_txt)]
    ]
    t_table = Table(t_data, colWidths=[182, 182, 184])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2F6')),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(t_table)
    story.append(Spacer(1, 8))

    # 5. On-Page Optimization & Tag Quality
    story.append(Paragraph("2. On-Page Optimization & Tag Quality", sec_title))
    o_data = [
        [Paragraph("Tag Element", cell_bold), Paragraph("Observed Audit Data", cell_bold), Paragraph("Optimization Status", cell_bold)],
        [Paragraph("Page Title", cell_txt), Paragraph(f"{data['title'][:48]}... ({data['title_len']} chars)", cell_txt), Paragraph("Optimal (50-60 chars)" if 50 <= data['title_len'] <= 60 else "Review Length (50-60 chars)", cell_txt)],
        [Paragraph("Meta Description", cell_txt), Paragraph(f"{data['desc'][:48]}... ({data['desc_len']} chars)", cell_txt), Paragraph("Optimal (140-160 chars)" if 140 <= data['desc_len'] <= 160 else "Adjust to 140-160 chars", cell_txt)],
        [Paragraph("Primary H1 Tag", cell_txt), Paragraph(data['primary_h1'][:55] if data['primary_h1'] else "None detected", cell_txt), Paragraph("Optimal (1 H1)" if data['h1_count'] == 1 else f"Warning: {data['h1_count']} H1 detected", cell_txt)],
        [Paragraph("Image ALT Attributes", cell_txt), Paragraph(f"{data['missing_alt']} of {data['total_img']} images missing ALT tags", cell_txt), Paragraph("Pass" if data['missing_alt'] == 0 else "Optimize ALT tags", cell_txt)]
    ]
    o_table = Table(o_data, colWidths=[130, 240, 178])
    o_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2F6')),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(o_table)
    story.append(Spacer(1, 8))

    # 6. Strategic Action Checklist
    story.append(Paragraph("3. Immediate Recommended Fixes", sec_title))
    act_rows = []
    if data['h1_count'] != 1:
        act_rows.append([Paragraph(f"- Hierarchy: Found {data['h1_count']} H1 tags. Consolidate to 1 primary keyword-focused H1.", cell_txt)])
    if not (50 <= data['title_len'] <= 60):
        act_rows.append([Paragraph(f"- Title Length: Title is {data['title_len']} chars. Revise to 50-60 characters for SERP CTR.", cell_txt)])
    if not (140 <= data['desc_len'] <= 160):
        act_rows.append([Paragraph(f"- Meta Description: Description is {data['desc_len']} chars. Adjust to 140-160 characters.", cell_txt)])
    if data['missing_alt'] > 0:
        act_rows.append([Paragraph(f"- Image ALT: Add descriptive ALT tags containing secondary keywords to {data['missing_alt']} images.", cell_txt)])
    if isinstance(data['psi']['perf'], int) and data['psi']['perf'] < 70:
        act_rows.append([Paragraph(f"- Speed: Mobile score is {data['psi']['perf']}/100. Minify assets, optimize next-gen images, and leverage browser caching.", cell_txt)])
    if not act_rows:
        act_rows.append([Paragraph("- Technical Baseline Strong: No critical technical blockers detected. Prioritize off-page link building.", cell_txt)])

    act_tbl = Table(act_rows, colWidths=[548])
    act_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(act_tbl)
    story.append(Spacer(1, 8))

    # 7. Agency Pitch & Booking Callout
    pitch_msg = f"Need Help Executing These Optimization Tasks? {AGENCY_NAME} manages technical website fixes, silo architecture, and high-impact digital PR and guest outreach. Contact us at {AGENCY_EMAIL} or call {AGENCY_PHONE} to schedule a complimentary strategy session."
    pitch_row = [[Paragraph(pitch_msg, pitch_txt)]]
    pitch_tbl = Table(pitch_row, colWidths=[548])
    pitch_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3B82F6')),
    ]))
    story.append(pitch_tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================================
# STREAMLIT UI
# ==========================================================
with st.form("audit_form"):
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name (Optional)", placeholder="Talha")
    with col2:
        last_name = st.text_input("Last Name (Optional)", placeholder="Mahmood")
    email = st.text_input("Business Email *", placeholder="name@company.com")
    website_url = st.text_input("Website URL *", placeholder="https://example.com")
    submit_btn = st.form_submit_button("Generate Audit Report & Visual PDF")

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

        with st.spinner(f"Auditing {target_url}... Generating visual charts & PDF."):
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

            # Auto-save lead to Google Sheet via Webhook
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
                label="Download Executive Visual SEO Audit (PDF)",
                data=pdf_file_bytes,
                file_name=f"SEO_Audit_{base_domain}.pdf",
                mime="application/pdf"
            )
