import io
import json
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
AGENCY_PHONE = "+92 302 6264634"
AGENCY_WEBSITE = "https://rankcentre.net"
AGENCY_ADDRESS = "Office 402, Business Arcade, Gujrat / Lahore, Pakistan"

# ✅ AAP KA GOOGLE SHEET WEBHOOK LINK YAHAN CONNECT HO GAYA HAI:
GOOGLE_SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwetciC31Q-zSgylj7cFxnMN1IUs-B_-bSq3Zfs1Je3AHomk8Qg-IHKlWy2xeI1pyGw4g/exec"

st.set_page_config(page_title="Deep Technical & SEO Audit Suite", layout="wide")
st.title("Agency Technical SEO & Authority Audit Suite")
st.write("Perform deep technical diagnostics (Robots, Sitemap, Schema, Broken Links) and link-building gap analysis with 1-click executive PDF delivery.")

def generate_health_donut_chart(overall_score):
    fig, ax = plt.subplots(figsize=(2.2, 2.2), subplot_kw=dict(aspect="equal"))
    score = int(overall_score)
    if score not in range(0, 101):
        score = 50
    remaining = 100 - score
    
    if score in range(80, 101):
        chart_color = '#10B981'
    elif score in range(50, 80):
        chart_color = '#F59E0B'
    else:
        chart_color = '#EF4444'
    
    ax.pie(
        [score, remaining],
        colors=[chart_color, '#E2E8F0'],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2)
    )
    ax.text(0, 0, str(score) + "%", ha='center', va='center', fontsize=18, fontweight='bold', color='#0F172A')
    ax.text(0, -0.32, "HEALTH", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#64748B')
    
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=160)
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_metrics_bar_chart(links_internal, links_external, img_total, img_missing):
    fig, ax = plt.subplots(figsize=(3.6, 2.0))
    categories = ['Ext Links', 'Int Links', 'Missing ALT', 'Images']
    values = [links_external, links_internal, img_missing, img_total]
    
    missing_color = '#10B981'
    if img_missing != 0:
        missing_color = '#EF4444'
    bar_colors = ['#6366F1', '#3B82F6', missing_color, '#06B6D4']
    
    bars = ax.barh(categories, values, color=bar_colors, height=0.55)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CBD5E1')
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.tick_params(axis='both', which='both', labelsize=7.5, colors='#475569')
    
    max_val = 1
    if values and max(values) != 0:
        max_val = max(values)
        
    for bar in bars:
        width = bar.get_width()
        ax.text(width + (max_val * 0.03), bar.get_y() + bar.get_height() / 2,
                str(int(width)), ha='left', va='center', fontsize=7.5, fontweight='bold', color='#1E293B')
    
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
        perf_score = "N/A"
        seo_score = "N/A"
        if cats.get("performance"):
            perf_score = int(cats.get("performance", {}).get("score", 0) * 100)
        if cats.get("seo"):
            seo_score = int(cats.get("seo", {}).get("score", 0) * 100)
            
        audits = lighthouse.get("audits", {})
        fcp = audits.get("first-contentful-paint", {}).get("displayValue", "N/A")
        lcp = audits.get("largest-contentful-paint", {}).get("displayValue", "N/A")
        cls_val = audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A")
        return {"perf": perf_score, "seo": seo_score, "fcp": fcp, "lcp": lcp, "cls": cls_val}
    except Exception:
        return {"perf": "N/A", "seo": "N/A", "fcp": "N/A", "lcp": "N/A", "cls": "N/A"}

def check_broken_links(internal_links, base_url, headers):
    clean_internals = []
    for l in internal_links:
        full_l = urllib.parse.urljoin(base_url, l)
        if full_l.startswith("http") and full_l not in clean_internals:
            clean_internals.append(full_l)

    sample = clean_internals[:10]
    if not sample:
        return "No internal links found to test", 0

    broken = 0
    for link in sample:
        try:
            res = requests.get(link, headers=headers, timeout=4, stream=True)
            if res.status_code in range(400, 600):
                broken = broken + 1
        except Exception:
            broken = broken + 1

    if broken == 0:
        return f"Healthy (0 broken of {len(sample)} tested)", 0
    return f"Alert: {broken} broken links of {len(sample)} tested", broken

def audit_deep_technical(target_url, soup, internal_links, headers):
    parsed = urllib.parse.urlparse(target_url)
    base_root = f"{parsed.scheme}://{parsed.netloc}"
    
    # Robots.txt Check
    robots_url = urllib.parse.urljoin(base_root, "/robots.txt")
    robots_status = "Missing (404 Not Found)"
    try:
        r_res = requests.get(robots_url, headers=headers, timeout=5)
        if r_res.status_code == 200:
            if "Disallow: /" in r_res.text:
                robots_status = "Warning: Sitewide Disallow Detected"
            else:
                robots_status = "Configured (200 OK)"
    except Exception:
        robots_status = "Connection Timed Out"

    # Sitemap.xml Check
    sitemap_url = urllib.parse.urljoin(base_root, "/sitemap.xml")
    sitemap_status = "Missing / Inaccessible"
    try:
        s_res = requests.get(sitemap_url, headers=headers, timeout=5)
        if s_res.status_code == 200:
            if "urlset" in s_res.text or "sitemapindex" in s_res.text:
                sitemap_status = "Valid XML Sitemap (200 OK)"
            else:
                sitemap_status = "Accessible (200 OK)"
    except Exception:
        sitemap_status = "Connection Timed Out"

    # Schema Markup Check
    schemas_detected = []
    schema_tags = soup.find_all("script", type="application/ld+json")
    for st_tag in schema_tags:
        try:
            raw_text = st_tag.string
            if raw_text:
                payload = json.loads(raw_text)
                if isinstance(payload, dict) and payload.get("@type"):
                    schemas_detected.append(str(payload.get("@type")))
                elif isinstance(payload, list):
                    for itm in payload:
                        if isinstance(itm, dict) and itm.get("@type"):
                            schemas_detected.append(str(itm.get("@type")))
        except Exception:
            pass

    if schemas_detected:
        unique_schemas = list(dict.fromkeys(schemas_detected))
        schema_status = f"Detected: {', '.join(unique_schemas[:3])}"
    elif schema_tags:
        schema_status = "JSON-LD Tag Present"
    else:
        schema_status = "Missing (No JSON-LD Detected)"

    broken_status, broken_count = check_broken_links(internal_links, target_url, headers)

    return {
        "robots": robots_status,
        "sitemap": sitemap_status,
        "schema": schema_status,
        "broken_status": broken_status,
        "broken_count": broken_count
    }

def calculate_backlink_gap(competition_tier):
    if "Low" in competition_tier:
        return {
            "tier": "Low Competition / Local Niche",
            "benchmark_rd": "15 - 35 Referring Domains",
            "gap_estimate": "10 - 25 High-Quality Backlinks",
            "strategy": "Local citations, foundational niche backlinks, and 2-3 guest posts per month."
        }
    if "High" in competition_tier:
        return {
            "tier": "High Competition / Global Niche",
            "benchmark_rd": "120 - 300+ Referring Domains",
            "gap_estimate": "60 - 150+ High-Authority Backlinks (DR 50+)",
            "strategy": "Aggressive guest outreach, digital PR, resource-page link building, and tiered contextual links."
        }
    return {
        "tier": "Medium Competition / Standard Commercial Niche",
        "benchmark_rd": "45 - 90 Referring Domains",
        "gap_estimate": "30 - 50 Contextual Editorial Links",
        "strategy": "Niche-relevant guest blogging on DR 40-70 sites with contextual anchors."
    }

def build_pdf_report(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=32, leftMargin=32, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()

    c_primary = colors.HexColor('#1E3A8A')
    c_dark = colors.HexColor('#0F172A')
    c_slate = colors.HexColor('#475569')
    c_light = colors.HexColor('#F8FAFC')
    c_border = colors.HexColor('#E2E8F0')

    title_agency = ParagraphStyle('TAgency', parent=styles['Heading1'], fontSize=13, leading=16, fontName='Helvetica-Bold', textColor=c_primary)
    agency_sub = ParagraphStyle('ASub', parent=styles['Normal'], fontSize=7.5, leading=9.5, textColor=c_slate)
    sec_title = ParagraphStyle('STitle', parent=styles['Heading2'], fontSize=9.5, leading=12, fontName='Helvetica-Bold', textColor=c_dark, spaceBefore=4, spaceAfter=2)
    cell_txt = ParagraphStyle('CTxt', parent=styles['Normal'], fontSize=7, leading=9, textColor=c_dark)
    cell_bold = ParagraphStyle('CBld', parent=styles['Normal'], fontSize=7, leading=9, fontName='Helvetica-Bold', textColor=c_dark)
    pitch_title = ParagraphStyle('PTitle', parent=styles['Normal'], fontSize=7.5, leading=10, fontName='Helvetica-Bold', textColor=colors.HexColor('#1E3A8A'))
    pitch_txt = ParagraphStyle('PTxt', parent=styles['Normal'], fontSize=7, leading=9.5, textColor=colors.HexColor('#1E3A8A'))

    story = []

    # Header
    header_table_data = [
        [Paragraph(AGENCY_NAME, title_agency), Paragraph("Email:", cell_bold), Paragraph(AGENCY_EMAIL, agency_sub)],
        [Paragraph("Search Engine Optimization & Outreach Consultancy", agency_sub), Paragraph("Phone:", cell_bold), Paragraph(AGENCY_PHONE, agency_sub)],
        [Paragraph("", agency_sub), Paragraph("Website:", cell_bold), Paragraph(AGENCY_WEBSITE, agency_sub)],
        [Paragraph("", agency_sub), Paragraph("HQ:", cell_bold), Paragraph(AGENCY_ADDRESS, agency_sub)]
    ]
    hdr_table = Table(header_table_data, colWidths=[290, 50, 208])
    hdr_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('LINEBELOW', (0, -1), (-1, -1), 1.2, c_primary),
    ]))
    story.append(hdr_table)
    story.append(Spacer(1, 5))

    # Meta
    meta_info = [
        [Paragraph("Target URL:", cell_bold), Paragraph(data['url'], cell_txt), Paragraph("Client Contact:", cell_bold), Paragraph(data['client'], cell_txt)],
        [Paragraph("Root Domain:", cell_bold), Paragraph(data['domain'], cell_txt), Paragraph("Client Email:", cell_bold), Paragraph(data['email'], cell_txt)],
        [Paragraph("Target Keyword:", cell_bold), Paragraph(data['keyword'], cell_txt), Paragraph("Niche Competition:", cell_bold), Paragraph(data['comp_tier'], cell_txt)]
    ]
    meta_table = Table(meta_info, colWidths=[75, 200, 75, 198])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F1F5F9')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 5))

    # Diagnostics Calculation
    calc_perf = 65
    if isinstance(data['psi']['perf'], int):
        calc_perf = data['psi']['perf']
        
    calc_seo = 75
    if isinstance(data['psi']['seo'], int):
        calc_seo = data['psi']['seo']
        
    h1_pen = 0
    if data['h1_count'] != 1:
        h1_pen = 15
        
    img_pen = 0
    if data['missing_alt'] != 0:
        img_pen = 10
        
    raw_health = int(((calc_perf * 0.4) + (calc_seo * 0.6)) - h1_pen - img_pen)
    calc_health = max(10, raw_health)

    donut_chart_buffer = generate_health_donut_chart(calc_health)
    bar_chart_buffer = generate_metrics_bar_chart(data['int_links'], data['ext_links'], data['total_img'], data['missing_alt'])
    donut_img = Image(donut_chart_buffer, width=95, height=95)
    bar_img = Image(bar_chart_buffer, width=175, height=95)

    verdict_subtable_data = [
        [Paragraph("Audit Summary", cell_bold), Paragraph("", cell_txt)],
        [Paragraph("Mobile Performance:", cell_txt), Paragraph(str(data['psi']['perf']) + "/100", cell_bold)],
        [Paragraph("Lighthouse SEO:", cell_txt), Paragraph(str(data['psi']['seo']) + "/100", cell_bold)],
        [Paragraph("HTTPS Security:", cell_txt), Paragraph(data['ssl'], cell_txt)],
        [Paragraph("Canonical Mapping:", cell_txt), Paragraph(data['canonical'], cell_txt)]
    ]
    verdict_subtable = Table(verdict_subtable_data, colWidths=[105, 95])
    verdict_subtable.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(Paragraph("Executive Performance & Structural Diagnostics", sec_title))
    health_summary_card = [[donut_img, verdict_subtable, bar_img]]
    diag_table = Table(health_summary_card, colWidths=[110, 210, 228])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 2.5),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 5))

    # Deep Technical Table
    story.append(Paragraph("1. Deep Technical Crawlability & Architecture", sec_title))
    tech_diag = data['tech_diag']
    d_data = [
        [Paragraph("Technical Parameter", cell_bold), Paragraph("Observed Status", cell_bold), Paragraph("Health Benchmark", cell_bold)],
        [Paragraph("Robots.txt Status", cell_txt), Paragraph(tech_diag['robots'], cell_txt), Paragraph("200 OK without Sitewide Disallow", cell_txt)],
        [Paragraph("XML Sitemap Status", cell_txt), Paragraph(tech_diag['sitemap'], cell_txt), Paragraph("Valid sitemap.xml required for indexing", cell_txt)],
        [Paragraph("Schema Markup (JSON-LD)", cell_txt), Paragraph(tech_diag['schema'], cell_txt), Paragraph("Rich Snippet structured data enabled", cell_txt)],
        [Paragraph("Internal Link Integrity", cell_txt), Paragraph(tech_diag['broken_status'], cell_txt), Paragraph("Zero 404 broken links on critical pages", cell_txt)]
    ]
    d_table = Table(d_data, colWidths=[130, 220, 198])
    d_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2F6')),
        ('PADDING', (0, 0), (-1, -1), 2.5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(d_table)
    story.append(Spacer(1, 5))

    # On-Page Table
    story.append(Paragraph("2. On-Page Optimization & Core Web Vitals", sec_title))
    title_status = "Optimal"
    if data['title_len'] not in range(50, 61):
        title_status = "Review Length (50-60 chars)"
        
    desc_status = "Optimal"
    if data['desc_len'] not in range(140, 161):
        desc_status = "Adjust to 140-160 chars"
        
    h1_status = "Optimal"
    if data['h1_count'] != 1:
        h1_status = f"Warning: {data['h1_count']} H1 detected"
        
    alt_status = "Optimal"
    if data['missing_alt'] != 0:
        alt_status = "Optimize ALT tags"

    tech_data = [
        [Paragraph("Audit Check", cell_bold), Paragraph("Observed Value", cell_bold), Paragraph("Optimization Status", cell_bold)],
        [Paragraph("Page Title", cell_txt), Paragraph(f"{data['title'][:45]}... ({data['title_len']} chars)", cell_txt), Paragraph(title_status, cell_txt)],
        [Paragraph("Meta Description", cell_txt), Paragraph(f"{data['desc'][:45]}... ({data['desc_len']} chars)", cell_txt), Paragraph(desc_status, cell_txt)],
        [Paragraph("Primary H1 Tag", cell_txt), Paragraph(data['primary_h1'][:50], cell_txt), Paragraph(h1_status, cell_txt)],
        [Paragraph("Core Web Vitals LCP", cell_txt), Paragraph(str(data['psi']['lcp']), cell_txt), Paragraph("Target: under 2.5s", cell_txt)],
        [Paragraph("Image ALT Attributes", cell_txt), Paragraph(f"{data['missing_alt']} of {data['total_img']} images missing ALT", cell_txt), Paragraph(alt_status, cell_txt)]
    ]
    tech_table = Table(tech_data, colWidths=[130, 220, 198])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2F6')),
        ('PADDING', (0, 0), (-1, -1), 2.5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 5))

    # Gap Table
    story.append(Paragraph("3. Off-Page Authority & Link-Building Gap", sec_title))
    gap = data['gap_data']
    gap_table_data = [
        [Paragraph("Authority Parameter", cell_bold), Paragraph("Audit Finding & Benchmark", cell_bold)],
        [Paragraph("Target Keyword Target", cell_txt), Paragraph(f"{data['keyword']} (Competitiveness: {gap['tier']})", cell_txt)],
        [Paragraph("Page 1 RD Benchmark", cell_txt), Paragraph(f"Top ranking competitors average {gap['benchmark_rd']}", cell_txt)],
        [Paragraph("Estimated Backlink Gap", cell_txt), Paragraph(f"Estimated requirement: {gap['gap_estimate']} to challenge Page 1", cell_txt)],
        [Paragraph("Outreach Action Strategy", cell_txt), Paragraph(gap['strategy'], cell_txt)]
    ]
    gap_table = Table(gap_table_data, colWidths=[150, 398])
    gap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2F6')),
        ('PADDING', (0, 0), (-1, -1), 2.5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(gap_table)
    story.append(Spacer(1, 5))

    # Pitch Box
    pitch_header = f"Ready to Close Your Authority Gap? {AGENCY_NAME} Outreach Solution"
    pitch_details = (
        f"Technical fixes establish crawling readiness, but authoritative backlinks drive top positions. "
        f"We execute tailored outreach campaigns, securing contextual dofollow guest posts on genuine traffic-verified domains (DR 40 to 80+). "
        f"Contact our outreach team at {AGENCY_EMAIL} or WhatsApp {AGENCY_PHONE} for a customized link-building campaign."
    )
    pitch_card = [
        [Paragraph(pitch_header, pitch_title)],
        [Paragraph(pitch_details, pitch_txt)]
    ]
    pitch_table = Table(pitch_card, colWidths=[548])
    pitch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3B82F6')),
    ]))
    story.append(pitch_table)

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
    
    col3, col4 = st.columns(2)
    with col3:
        email = st.text_input("Business Email *", placeholder="name@company.com")
    with col4:
        website_url = st.text_input("Website URL *", placeholder="https://example.com")
        
    col5, col6 = st.columns(2)
    with col5:
        target_keyword = st.text_input("Primary Target Keyword (Optional)", placeholder="e.g. SEO Agency Lahore / Best CRM Software")
    with col6:
        competition_level = st.selectbox(
            "Niche Competition Level",
            ["Medium Competition (Standard Commercial Niche)", "Low Competition (Local / Micro-Niche)", "High Competition (Global / Finance / SaaS)"]
        )
        
    submit_btn = st.form_submit_button("Generate Complete Technical & Authority Audit")

if submit_btn:
    if not email.strip() or "@" not in email or "." not in email:
        st.error("Please enter a valid Business Email address.")
        st.stop()
    
    if not website_url.strip():
        st.error("Please enter a valid Website URL.")
        st.stop()

    target_url = website_url.strip()
    if not target_url.startswith("http"):
        target_url = "https://" + target_url
    
    name_str = f"{first_name} {last_name}".strip()
    user_display_name = "Website Owner"
    if name_str:
        user_display_name = name_str
        
    active_keyword = "Core Industry Keyword"
    if target_keyword.strip():
        active_keyword = target_keyword.strip()

    with st.spinner(f"Crawling {target_url} (Checking Robots, Sitemap, Schema, Broken Links)..."):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            response = requests.get(target_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            st.error(f"Target website error: {e}")
            st.stop()

        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            
        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        meta_desc = ""
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag.get("content").strip()
            
        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
        canonical = soup.find("link", rel="canonical")
        canonical_url = "Missing"
        if canonical and canonical.get("href"):
            canonical_url = canonical.get("href")
            
        images = soup.find_all("img")
        missing_alt = []
        for img in images:
            alt_val = img.get("alt")
            if not alt_val or alt_val.strip() == "":
                missing_alt.append(img.get("src", "Unknown"))
                
        base_domain = tldextract.extract(target_url).registered_domain

        internal_links = []
        external_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("#", "javascript:", "mailto:", "tel:")) or not href:
                continue
            link_domain = tldextract.extract(href).registered_domain
            if not link_domain or link_domain == base_domain:
                internal_links.append(href)
            else:
                external_links.append(href)

        # Deep Technical Diagnostics
        tech_diag = audit_deep_technical(target_url, soup, internal_links, headers)

        # Google PageSpeed
        psi_data = get_google_pagespeed(target_url)

        # Backlink Gap
        gap_data = calculate_backlink_gap(competition_level)

        # 🚀 AUTO-SAVE LEAD TO GOOGLE SHEET (WEBHOOK)
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

        # Metrics Row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Performance", f"{psi_data['perf']}/100")
        c2.metric("Lighthouse SEO", f"{psi_data['seo']}/100")
        c3.metric("Broken Links Status", str(tech_diag['broken_count']) + " Broken")
        c4.metric("Backlink Gap Est.", gap_data['gap_estimate'].split()[0])

        # Technical Output Box
        st.markdown("### 🛠️ Deep Technical Diagnostics")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.write(f"• **Robots.txt:** {tech_diag['robots']}")
            st.write(f"• **XML Sitemap:** {tech_diag['sitemap']}")
        with t_col2:
            st.write(f"• **Schema Markup:** {tech_diag['schema']}")
            st.write(f"• **Internal Link Integrity:** {tech_diag['broken_status']}")

        st.info(f"🎯 **Authority Gap for '{active_keyword}':** Niche competitors average **{gap_data['benchmark_rd']}**. We estimate an immediate requirement of **{gap_data['gap_estimate']}** to challenge top rankings.")

        pri_h1 = "None detected"
        if h1_tags:
            pri_h1 = h1_tags[0]

        ssl_val = "Missing (Insecure)"
        if target_url.startswith("https"):
            ssl_val = "Active (Secure)"

        title_display = "Not Specified"
        if title:
            title_display = title

        desc_display = "Not Specified"
        if meta_desc:
            desc_display = meta_desc

        pdf_payload = {
            'client': user_display_name,
            'email': email,
            'url': target_url,
            'domain': base_domain,
            'keyword': active_keyword,
            'comp_tier': competition_level,
            'gap_data': gap_data,
            'tech_diag': tech_diag,
            'psi': psi_data,
            'ssl': ssl_val,
            'canonical': canonical_url,
            'title': title_display,
            'title_len': len(title),
            'desc': desc_display,
            'desc_len': len(meta_desc),
            'h1_count': len(h1_tags),
            'primary_h1': pri_h1,
            'total_img': len(images),
            'missing_alt': len(missing_alt),
            'int_links': len(internal_links),
            'ext_links': len(external_links)
        }

        pdf_file_bytes = build_pdf_report(pdf_payload)
        st.download_button(
            label="📥 Download Executive Visual SEO & Technical Audit (PDF)",
            data=pdf_file_bytes,
            file_name=f"SEO_Audit_Deep_{base_domain}.pdf",
            mime="application/pdf"
        )
