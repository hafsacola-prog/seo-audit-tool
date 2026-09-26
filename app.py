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

# Google Sheet Apps Script Webhook URL
GOOGLE_SHEET_WEBHOOK_URL = "YAHAN_APNA_WEBHOOK_URL_PASTE_KAREIN"

st.set_page_config(page_title="Deep Technical & SEO Audit Suite", layout="wide")
st.title("Agency Technical SEO & Authority Audit Suite")
st.write("Perform deep technical diagnostics (Robots, Sitemap, Schema, Broken Links) and link-building gap analysis with 1-click executive PDF delivery.")

def generate_health_donut_chart(overall_score):
    fig, ax = plt.subplots(figsize=(2.2, 2.2), subplot_kw=dict(aspect="equal"))
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
    ax.text(0, 0, f"{score}%", ha='center', va='center', fontsize=18, fontweight='bold', color='#0F172A')
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
    bar_colors = ['#6366F1', '#3B82F6', '#EF4444' if img_missing > 0 else '#10B981', '#06B6D4']
    
    bars = ax.barh(categories, values, color=bar_colors, height=0.55)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CBD5E1')
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.tick_params(axis='both', which='both', labelsize=7.5, colors='#475569')
    
    max_val = max(values) if values and max(values) > 0 else 1
    for bar in bars:
        width = bar.get_width()
        ax.text(width + (max_val * 0.03), bar.get_y() + bar.get_height() / 2,
                f'{int(width)}', ha='left', va='center', fontsize=7.5, fontweight='bold', color='#1E293B')
    
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

def audit_deep_technical(target_url, soup, internal_links, headers):
    parsed = urllib.parse.urlparse(target_url)
    base_root = f"{parsed.scheme}://{parsed.netloc}"
    
    # 1. Robots.txt Check
    robots_url = urllib.parse.urljoin(base_root, "/robots.txt")
    robots_status = "Missing (404 Not Found)"
    try:
        r_res = requests.get(robots_url, headers=headers, timeout=5)
        if r_res.status_code == 200:
            if "Disallow: /" in r_res.text and "\nDisallow: /\n" in r_res.text:
                robots_status = "Warning: Sitewide Disallow Detected"
            else:
                robots_status = "Configured (200 OK)"
    except Exception:
        robots_status = "Connection Timed Out"

    # 2. Sitemap.xml Check
    sitemap_url = urllib.parse.urljoin(base_root, "/sitemap.xml")
    sitemap_status = "Missing / Inaccessible"
    try:
        s_res = requests.get(sitemap_url, headers=headers, timeout=5)
        if s_res.status_code == 200:
           if res_check.status_code >= 400:
                    broken_count += 1
            except Exception:
                broken_count += 1

    if len(sample_links) == 0:
        broken_status = "No internal links found to test"
    elif broken_count == 0:
        broken_status = f"Healthy (0 broken of {len(sample_links)} tested)"
    else:
        broken_status = f"Alert: {broken_count} broken links of {len(sample_links)} tested"

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
    elif "High" in competition_tier:
        return {
            "tier": "High Competition / Global Niche",
            "benchmark_rd": "120 - 300+ Referring Domains",
            "gap_estimate": "60 - 150+ High-Authority Backlinks (DR 50+)",
            "strategy": "Aggressive guest outreach, digital PR, resource-page link building, and tiered contextual links."
        }
    else:
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
    pitch_txt = ParagraphStyle('PTxt', parent=styles['Normal'], fontSize=7, leading=9.5, textColor=colors.HexColor('#1E3A8A'))

    story = []

    # 1. Header
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

    # 2. Metadata Info
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

    # 3. Health & Visual Diagnostics
    story.append(Paragraph("Executive Performance & Structural Diagnostics", sec_title))
    calc_perf = data['psi']['perf'] if isinstance(data['psi']['perf'], int) else 65
    calc_seo = data['psi']['seo'] if isinstance(data['psi']['seo'], int) else 75
    h1_penalty = 15 if data['h1_count'] != 1 else 0
    img_penalty = 10 if data['missing_alt'] > 0 else 0
    calculated_health = max(10, int(((calc_perf * 0.4) + (calc_seo * 0.6)) - h1_penalty - img_penalty))

    donut_chart_buffer = generate_health_donut_chart(calculated_health)
    bar_chart_buffer = generate_metrics_bar_chart(data['int_links'], data['ext_links'], data['total_img'], data['missing_alt'])
    donut_img = Image(donut_chart_buffer, width=95, height=95)
    bar_img = Image(bar_chart_buffer, width=175, height=95)

    verdict_subtable_data = [
        [Paragraph("Audit Summary", cell_bold), Paragraph("", cell_txt)],
        [Paragraph("Mobile Performance:", cell_txt), Paragraph(f"{data['psi']['perf']}/100", cell_bold)],
        [Paragraph("Lighthouse SEO:", cell_txt), Paragraph(f"{data['psi']['seo']}/100", cell_bold)],
        [Paragraph("HTTPS Security:", cell_txt), Paragraph(data['ssl'], cell_txt)],
        [Paragraph("Canonical Mapping:", cell_txt), Paragraph(data['canonical'], cell_txt)]
    ]
    verdict_subtable = Table(verdict_subtable_data, colWidths=[105, 95])
    verdict_subtable.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

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

    # 4. Deep Technical Diagnostics
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

    # 5. On-Page Optimization
    story.append(Paragraph("2. On-Page Optimization & Core Web Vitals", sec_title))
    tech_data = [
        [Paragraph("Audit Check", cell_bold), Paragraph("Observed Value", cell_bold), Paragraph("Optimization Status", cell_bold)],
        [Paragraph("Page Title", cell_txt), Paragraph(f"{data['title'][:45]}... ({data['title_len']} chars)", cell_txt), Paragraph("Optimal" if 50 <= data['title_len'] <= 60 else "Review Length (50-60 chars)", cell_txt)],
        [Paragraph("Meta Description", cell_txt), Paragraph(f"{data['desc'][:45]}... ({data['desc_len']} chars)", cell_txt), Paragraph("Optimal" if 140 <= data['desc_len'] <= 160 else "Adjust to 140-160 chars", cell_txt)],
        [Paragraph("Primary H1 Tag", cell_txt), Paragraph(data['primary_h1'][:50] if data['primary_h1'] else "None detected", cell_txt), Paragraph("Optimal" if data['h1_count'] == 1 else f"Warning: {data['h1_count']} H1 detected", cell_txt)],
        [Paragraph("Core Web Vitals LCP", cell_txt), Paragraph(str(data['psi']['lcp']), cell_txt), Paragraph("Target under 2.5s", cell_txt)],
        [Paragraph("Image ALT Attributes", cell_txt), Paragraph(f"{data['missing_alt']} of {data['total_img']} images missing ALT", cell_txt), Paragraph("Optimal" if data['missing_alt'] == 0 else "Optimize ALT tags", cell_txt)]
    ]
    tech_table = Table(tech_data, colWidths=[130, 220, 198])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2F6')),
        ('PADDING', (0, 0), (-1, -1), 2.5),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 5))

    # 6. Off-Page Backlink Gap Analysis
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

    # 7. Outreach Pitch Box
    pitch_header = f"Ready to Close Your Authority Gap? {AGENCY_NAME} Outreach Solution"
    pitch_details = (
        f"Technical fixes establish crawling readiness, but authoritative backlinks drive top positions. "
        f"We execute tailored outreach campaigns, securing contextual dofollow guest posts on genuine traffic-verified domains (DR 40 to 80+). "
        f"Contact our outreach team at {AGENCY_EMAIL} or WhatsApp {AGENCY_PHONE} for a customized link-building campaign."
    )
    pitch_card = [
        [Paragraph(f"**{pitch_header}**", pitch_txt)],
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
    elif not website_url.strip():
        st.error("Please enter a valid Website URL.")
    else:
        target_url = website_url.strip()
        if not target_url.startswith("http"):
            target_url = "https://" + target_url
        user_display_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else "Website Owner"
        active_keyword = target_keyword.strip() if target_keyword.strip() else "Core Industry Keyword"

        with st.spinner(f"Crawling {target_url} (Checking Robots, Sitemap, Schema, Broken Links)..."):
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

            # 1. Deep Technical Checks
            tech_diag = audit_deep_technical(target_url, soup, internal_links, headers)

            # 2. Google PageSpeed
            psi_data = get_google_pagespeed(target_url)

            # 3. Backlink Gap
            gap_data = calculate_backlink_gap(competition_level)

            # Auto-save lead to Google Sheet via Webhook
            if GOOGLE_SHEET_WEBHOOK_URL and "script.google.com" in GOOGLE_SHEET_WEBHOOK_URL:
                try:
                    sheet_payload = {
                        "name": user_display_name,
                        "email": email,
                        "url": target_url,
                        "keyword": active_keyword,
                        "perf_score": psi_data['perf'],
                        "seo_score": psi_data['seo'],
                        "robots": tech_diag['robots'],
                        "sitemap": tech_diag['sitemap'],
                        "schema": tech_diag['schema'],
                        "broken_links": tech_diag['broken_status']
                    }
                    requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=sheet_payload, timeout=6)
                except Exception:
                    pass

            st.success(f"Audit completed successfully for {user_display_name}!")

            # Metric Cards
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Performance", f"{psi_data['perf']}/100")
            c2.metric("Lighthouse SEO", f"{psi_data['seo']}/100")
            c3.metric("Broken Links Checked", tech_diag['broken_status'].split()[0])
            c4.metric("Backlink Gap Est.", gap_data['gap_estimate'].split()[0])

            # Deep Technical Findings Card
            st.markdown("### 🛠️ Deep Technical Diagnostics")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.write(f"• **Robots.txt:** {tech_diag['robots']}")
                st.write(f"• **XML Sitemap:** {tech_diag['sitemap']}")
            with t_col2:
                st.write(f"• **Schema Markup:** {tech_diag['schema']}")
                st.write(f"• **Internal Link Integrity:** {tech_diag['broken_status']}")

            st.info(f"🎯 **Authority Gap for '{active_keyword}':** Niche competitors average **{gap_data['benchmark_rd']}**. We estimate an immediate requirement of **{gap_data['gap_estimate']}** to challenge top rankings.")

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
                label="📥 Download Executive Visual SEO & Technical Audit (PDF)",
                data=pdf_file_bytes,
                file_name=f"SEO_Audit_Deep_{base_domain}.pdf",
                mime="application/pdf"
            )
