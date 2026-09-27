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
# AGENCY BRANDING & INTEGRATION SETTINGS
# ==========================================================
AGENCY_NAME = "RankCentre SEO & Digital Outreach"
AGENCY_EMAIL = "contact@rankcentre.net"
AGENCY_PHONE = "+92 302 6264634"
AGENCY_WEBSITE = "https://rankcentre.net"
AGENCY_ADDRESS = "Office 402, Business Arcade, Gujrat / Lahore, Pakistan"

# Google Sheet Apps Script Webhook URL
GOOGLE_SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwetciC31Q-zSgylj7cFxnMN1IUs-B_-bSq3Zfs1Je3AHomk8Qg-IHKlWy2xeI1pyGw4g/exec"

# Moz API Free Credentials (Streamlit Secrets se ya direct enter karein)
MOZ_ACCESS_ID = st.secrets.get("mozscape-cv9i4P2xN5", "")
MOZ_SECRET_KEY = st.secrets.get("EeDU0VboQ7woMS7iwooeGpYWh4eHVxhQ", "")

# Gemini API Key
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

st.set_page_config(page_title="Deep Technical & Moz Authority Audit", layout="wide")
st.title("Agency Technical SEO & Live Moz Authority Audit Suite")
st.write("Perform deep technical diagnostics, live Moz DA/PA/Spam Score metrics, Google SERP simulation, and side-by-side competitor benchmarking with 1-click executive PDF delivery.")


def extract_clean_word_count(html_content):
    """HTML tags remove karke actual visible word count calculate karna"""
    try:
        temp_soup = BeautifulSoup(html_content, "html.parser")
        for bad_elem in temp_soup(["script", "style", "noscript", "svg", "head"]):
            bad_elem.extract()
        text = temp_soup.get_text(separator=' ', strip=True)
        return len(text.split())
    except Exception:
        return 0


def get_moz_metrics(target_url, access_id, secret_key):
    """Moz Links API v2: Domain Authority, Page Authority, aur Spam Score"""
    if not access_id or not secret_key:
        return {"da": "N/A", "pa": "N/A", "spam": "N/A", "status": "API Key Missing"}

    clean_target = target_url.replace("https://", "").replace("http://", "").strip("/")
    endpoint = "https://lsapi.seomoz.com/v2/url_metrics"
    payload = {"targets": [clean_target, target_url]}

    try:
        res = requests.post(endpoint, json=payload, auth=(access_id, secret_key), timeout=8)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results_by_target", {})
            metrics = results.get(clean_target) or results.get(target_url) or (data.get("results", [{}])[0] if data.get("results") else {})
            
            raw_da = metrics.get("domain_authority", "N/A")
            raw_pa = metrics.get("page_authority", "N/A")
            raw_spam = metrics.get("spam_score", "N/A")

            da_val = int(raw_da) if isinstance(raw_da, (int, float)) and raw_da >= 0 else "N/A"
            pa_val = int(raw_pa) if isinstance(raw_pa, (int, float)) and raw_pa >= 0 else "N/A"
            spam_val = int(raw_spam) if isinstance(raw_spam, (int, float)) and raw_spam >= 0 else "N/A"

            return {"da": da_val, "pa": pa_val, "spam": spam_val, "status": "Live Moz Verified"}
        return {"da": "N/A", "pa": "N/A", "spam": "N/A", "status": f"Status {res.status_code}"}
    except Exception:
        return {"da": "N/A", "pa": "N/A", "spam": "N/A", "status": "Connection Timed Out"}


def get_gemini_private_strategy(url, title, meta_desc, h1_count, psi, tech_diag, gap_data, keyword, moz_client, comp_data=None):
    if not GEMINI_API_KEY:
        return "Gemini API key not configured in Streamlit Secrets."

    comp_context = "No direct competitor comparison requested."
    if comp_data:
        comp_context = f"""
        Direct Competitor Comparison:
        - Competitor URL: {comp_data['url']}
        - Client DA: {moz_client['da']} vs Competitor DA: {comp_data.get('moz', {}).get('da', 'N/A')}
        - Client Speed: {psi.get('perf', 'N/A')}/100 vs Competitor Speed: {comp_data.get('speed', 'N/A')}/100
        - Client Word Count: {gap_data.get('client_words', 0)} vs Competitor Word Count: {comp_data.get('words', 0)}
        """

    prompt = f"""
    You are an expert SEO strategist. Analyze these live audit findings for client website {url}:
    - Target Keyword: {keyword}
    - Moz Authority: DA {moz_client['da']}, PA {moz_client['pa']}, Spam Score {moz_client['spam']}%
    - Title Tag: {title}
    - Meta Description: {meta_desc}
    - H1 Tag Count: {h1_count}
    - PageSpeed Mobile: {psi.get('perf', 'N/A')}/100, Lighthouse SEO: {psi.get('seo', 'N/A')}/100
    - Robots.txt: {tech_diag.get('robots', 'N/A')}
    - XML Sitemap: {tech_diag.get('sitemap', 'N/A')}
    - Schema Markup: {tech_diag.get('schema', 'N/A')}
    - Broken Links Tested: {tech_diag.get('broken_status', 'N/A')}
    - Estimated Backlink Gap: {gap_data.get('gap_estimate', 'N/A')}
    {comp_context}

    Write a private agency outreach brief containing:
    1. 2 high-impact technical or authority fixes to improve DA and overtake the competitor.
    2. A short personalized cold email pitch angle Saad can send to this client to sell high-authority backlinks and SEO retainers.
    Keep it strictly professional, concise, and actionable (maximum 150 words).
    """

    headers = {"Content-Type": "application/json"}
    body = {"contents": [{"parts": [{"text": prompt}]}]}

    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]
    try:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        list_res = requests.get(list_url, timeout=6).json()
        if "models" in list_res:
            active_supported = [
                m["name"].replace("models/", "") 
                for m in list_res["models"] 
                if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
            flash_models = [m for m in active_supported if "flash" in m]
            if flash_models:
                candidate_models = flash_models + candidate_models
            elif active_supported:
                candidate_models = active_supported + candidate_models
    except Exception:
        pass

    last_error_msg = ""
    for model_name in list(dict.fromkeys(candidate_models)):
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(endpoint, headers=headers, json=body, timeout=12)
            res_data = res.json()
            if "candidates" in res_data and len(res_data["candidates"]) > 0:
                parts = res_data["candidates"][0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            if "error" in res_data:
                last_error_msg = res_data["error"].get("message", "API Error")
        except Exception as e:
            last_error_msg = str(e)
            continue

    return f"Gemini generation skipped: {last_error_msg}"


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


def calculate_backlink_gap(competition_tier, client_words=0, comp_words=0, moz_da="N/A", comp_da="N/A"):
    word_diff = max(0, comp_words - client_words)
    
    # Calculate authority gap if Moz DA is available
    da_gap_note = ""
    if isinstance(moz_da, int) and isinstance(comp_da, int):
        diff_da = comp_da - moz_da
        if diff_da > 0:
            da_gap_note = f"Your competitor has a {diff_da}-point Moz DA advantage."
        else:
            da_gap_note = f"You hold a {abs(diff_da)}-point Moz DA lead over your competitor."

    if "Low" in competition_tier:
        gap_est = "10 - 25 High-Quality Backlinks"
        strat = "Local citations, niche business directories, and 2-3 contextual guest posts per month."
        rd_bench = "15 - 35 Referring Domains"
    elif "High" in competition_tier:
        gap_est = "60 - 150+ High-Authority Backlinks (DR 50+)"
        strat = "Digital PR link acquisition, high-tier editorial placements (DR 60+), and competitor backlink replication."
        rd_bench = "120 - 300+ Referring Domains"
    else:
        gap_est = "30 - 50 Contextual Editorial Links"
        strat = "Niche-targeted guest blogging on DR 40-70 platforms with targeted contextual anchor distribution."
        rd_bench = "45 - 90 Referring Domains"

    return {
        "tier": competition_tier,
        "benchmark_rd": rd_bench,
        "gap_estimate": gap_est,
        "strategy": strat,
        "word_diff": word_diff,
        "client_words": client_words,
        "comp_words": comp_words,
        "da_gap_note": da_gap_note
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

    serp_url_style = ParagraphStyle('SerpUrl', parent=styles['Normal'], fontSize=7, leading=9, textColor=colors.HexColor('#202124'))
    serp_title_style = ParagraphStyle('SerpTitle', parent=styles['Normal'], fontSize=9.5, leading=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#1A0DAB'))
    serp_desc_style = ParagraphStyle('SerpDesc', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#4D5156'))

    story = []

    # 1. Header Table
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

    # 2. Meta Table
    comp_url_str = data['comp_data']['url'] if data.get('comp_data') else "None (Single Site Audit)"
    meta_info = [
        [Paragraph("Target URL:", cell_bold), Paragraph(data['url'], cell_txt), Paragraph("Client Contact:", cell_bold), Paragraph(data['client'], cell_txt)],
        [Paragraph("Root Domain:", cell_bold), Paragraph(data['domain'], cell_txt), Paragraph("Client Email:", cell_bold), Paragraph(data['email'], cell_txt)],
        [Paragraph("Target Keyword:", cell_bold), Paragraph(data['keyword'], cell_txt), Paragraph("Competitor URL:", cell_bold), Paragraph(comp_url_str[:35], cell_txt)]
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

    # 3. Diagnostics & Moz Overview Card
    calc_perf = 65
    if isinstance(data['psi']['perf'], int):
        calc_perf = data['psi']['perf']

    calc_seo = 75
    if isinstance(data['psi']['seo'], int):
        calc_seo = data['psi']['seo']

    h1_pen = 15 if data['h1_count'] != 1 else 0
    img_pen = 10 if data['missing_alt'] != 0 else 0

    raw_health = int(((calc_perf * 0.4) + (calc_seo * 0.6)) - h1_pen - img_pen)
    calc_health = max(10, raw_health)

    donut_chart_buffer = generate_health_donut_chart(calc_health)
    bar_chart_buffer = generate_metrics_bar_chart(data['int_links'], data['ext_links'], data['total_img'], data['missing_alt'])
    donut_img = Image(donut_chart_buffer, width=95, height=95)
    bar_img = Image(bar_chart_buffer, width=175, height=95)

    moz = data['moz']
    spam_display = f"{moz['spam']}%" if moz['spam'] != "N/A" else "N/A"

    verdict_subtable_data = [
        [Paragraph("Executive Summary & Moz Metrics", cell_bold), Paragraph("", cell_txt)],
        [Paragraph("Moz Domain Authority (DA):", cell_txt), Paragraph(f"**{moz['da']}/100**", cell_bold)],
        [Paragraph("Moz Page Authority (PA):", cell_txt), Paragraph(f"**{moz['pa']}/100**", cell_bold)],
        [Paragraph("Moz Spam Score:", cell_txt), Paragraph(f"**{spam_display}**", cell_bold)],
        [Paragraph("Mobile Performance:", cell_txt), Paragraph(str(data['psi']['perf']) + "/100", cell_bold)],
        [Paragraph("HTTPS / SSL Status:", cell_txt), Paragraph(data['ssl'], cell_txt)]
    ]
    verdict_subtable = Table(verdict_subtable_data, colWidths=[115, 85])
    verdict_subtable.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(Paragraph("Executive Performance, Structural & Moz Metrics", sec_title))
    health_summary_card = [[donut_img, verdict_subtable, bar_img]]
    diag_table = Table(health_summary_card, colWidths=[105, 215, 228])
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

    # 4. Side-by-Side Competitor Comparison Table (including Moz Metrics)
    if data.get('comp_data'):
        comp = data['comp_data']
        comp_moz = comp.get('moz', {'da': 'N/A', 'pa': 'N/A', 'spam': 'N/A'})
        story.append(Paragraph("Direct Side-by-Side Competitor Benchmark (With Moz Authority)", sec_title))
        
        speed_gap = "Balanced"
        if isinstance(data['psi']['perf'], int) and isinstance(comp['speed'], int):
            diff = data['psi']['perf'] - comp['speed']
            speed_gap = f"{'+' if diff > 0 else ''}{diff} Points"

        content_gap = f"{data['gap_data']['word_diff']} Words Deficit" if data['gap_data']['word_diff'] > 0 else "Content Lead"

        da_gap_str = "Balanced"
        if isinstance(moz['da'], int) and isinstance(comp_moz['da'], int):
            da_diff = comp_moz['da'] - moz['da']
            da_gap_str = f"Competitor +{da_diff} DA" if da_diff > 0 else f"Client +{abs(da_diff)} DA"

        comp_table_rows = [
            [Paragraph("Benchmark Metric", cell_bold), Paragraph(f"Client ({data['domain']})", cell_bold), Paragraph(f"Competitor ({comp['domain']})", cell_bold), Paragraph("Competitive Gap / Advantage", cell_bold)],
            [Paragraph("Moz Domain Authority (DA)", cell_txt), Paragraph(f"{moz['da']}/100", cell_bold), Paragraph(f"{comp_moz['da']}/100", cell_bold), Paragraph(da_gap_str, cell_bold)],
            [Paragraph("Moz Page Authority (PA)", cell_txt), Paragraph(f"{moz['pa']}/100", cell_txt), Paragraph(f"{comp_moz['pa']}/100", cell_txt), Paragraph("Page Strength", cell_txt)],
            [Paragraph("Moz Spam Score", cell_txt), Paragraph(f"{moz['spam']}%", cell_txt), Paragraph(f"{comp_moz['spam']}%", cell_txt), Paragraph("Penalty Risk Assessment", cell_txt)],
            [Paragraph("Mobile PageSpeed", cell_txt), Paragraph(f"{data['psi']['perf']}/100", cell_txt), Paragraph(f"{comp['speed']}/100", cell_txt), Paragraph(speed_gap, cell_bold)],
            [Paragraph("Content Depth (Word Count)", cell_txt), Paragraph(f"{data['client_words']:,} words", cell_txt), Paragraph(f"{comp['words']:,} words", cell_txt), Paragraph(content_gap, cell_bold)],
            [Paragraph("Authority Gap to Overtake", cell_txt), Paragraph(data['gap_data']['benchmark_rd'], cell_txt), Paragraph("Market Leader Profile", cell_txt), Paragraph(f"Need {data['gap_data']['gap_estimate']}", cell_bold)]
        ]
        comp_table = Table(comp_table_rows, colWidths=[140, 130, 130, 148])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2F6')),
            ('PADDING', (0, 0), (-1, -1), 2.5),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('BACKGROUND', (3, 1), (3, -1), colors.HexColor('#F8FAFC')),
        ]))
        story.append(comp_table)
        story.append(Spacer(1, 5))

    # 5. Google SERP Snippet Preview
    story.append(Paragraph("Live Google SERP Display Simulation", sec_title))
    serp_sim_title = data['title'] if len(data['title']) <= 60 else data['title'][:57] + "..."
    serp_sim_desc = data['desc'] if len(data['desc']) <= 155 else data['desc'][:152] + "..."
    if not serp_sim_desc or serp_sim_desc == "Not Specified":
        serp_sim_desc = "No meta description defined. Google will dynamically extract snippet sentences from body content."

    clean_url_snippet = data['url'].replace('https://','').replace('http://','')[:45]
    serp_box_data = [
        [Paragraph(f"**{data['domain']}** › {clean_url_snippet}", serp_url_style)],
        [Paragraph(serp_sim_title, serp_title_style)],
        [Paragraph(serp_sim_desc, serp_desc_style)],
        [Paragraph(f"*Title Length: {data['title_len']}/60 chars ({'Google Cut-off Alert' if data['title_len'] > 60 else 'Optimal'}) | Description Length: {data['desc_len']}/160 chars*", cell_txt)]
    ]
    serp_table = Table(serp_box_data, colWidths=[548])
    serp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F8FAFC')),
    ]))
    story.append(serp_table)
    story.append(Spacer(1, 5))

    # 6. Deep Technical Table
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

    # 7. Pitch Box
    pitch_header = f"Ready to Boost Your Moz DA & Beat Your Competitors? {AGENCY_NAME}"
    pitch_details = (
        f"While on-page technical fixes ensure crawl readiness, Moz Domain Authority is driven by contextual, high-tier editorial backlinks. "
        f"We secure niche-relevant, high-traffic guest posts on real publisher websites (DR/DA 40 to 80+) to safely bridge your authority gap. "
        f"Contact our outreach specialists at {AGENCY_EMAIL} or WhatsApp {AGENCY_PHONE} for your customized link-building roadmap."
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
        target_keyword = st.text_input("Primary Target Keyword (Optional)", placeholder="e.g. SEO Agency Lahore")

    col5, col6 = st.columns(2)
    with col5:
        website_url = st.text_input("Client Website URL *", placeholder="https://example.com")
    with col6:
        competitor_input_url = st.text_input("Competitor Website URL (Optional - For Comparison)", placeholder="https://competitor.com")

    competition_level = st.selectbox(
        "Niche Competition Level",
        ["Medium Competition (Standard Commercial Niche)", "Low Competition (Local / Micro-Niche)", "High Competition (Global / Finance / SaaS)"]
    )

    submit_btn = st.form_submit_button("Generate Complete Technical & Moz Authority Audit 🚀")

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

    comp_url = competitor_input_url.strip()
    if comp_url and not comp_url.startswith("http"):
        comp_url = "https://" + comp_url

    name_str = f"{first_name} {last_name}".strip()
    user_display_name = name_str if name_str else "Website Owner"
    active_keyword = target_keyword.strip() if target_keyword.strip() else "Core Industry Keyword"

    with st.spinner("Crawling sites, querying Moz API & analyzing benchmarks..."):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        # 1. Crawl Client Website
        try:
            client_resp = requests.get(target_url, headers=headers, timeout=15)
            soup = BeautifulSoup(client_resp.text, "html.parser")
            client_word_count = extract_clean_word_count(client_resp.text)
        except Exception as e:
            st.error(f"Client website connection error: {e}")
            st.stop()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        meta_desc = desc_tag.get("content").strip() if desc_tag and desc_tag.get("content") else ""

        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
        canonical = soup.find("link", rel="canonical")
        canonical_url = canonical.get("href") if canonical and canonical.get("href") else "Missing"

        images = soup.find_all("img")
        missing_alt = [img.get("src", "Unknown") for img in images if not img.get("alt") or img.get("alt").strip() == ""]

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

        # Deep Technical & PageSpeed for Client
        tech_diag = audit_deep_technical(target_url, soup, internal_links, headers)
        psi_data = get_google_pagespeed(target_url)

        # ⚡ LIVE MOZ METRICS FOR CLIENT
        moz_client = get_moz_metrics(target_url, MOZ_ACCESS_ID, MOZ_SECRET_KEY)

        # 2. Crawl Competitor (Agar URL diya gaya ho)
        comp_data = None
        if comp_url:
            try:
                comp_resp = requests.get(comp_url, headers=headers, timeout=15)
                comp_soup = BeautifulSoup(comp_resp.text, "html.parser")
                comp_words = extract_clean_word_count(comp_resp.text)
                comp_h1s = [h.get_text(strip=True) for h in comp_soup.find_all("h1")]
                comp_domain = tldextract.extract(comp_url).registered_domain
                comp_psi = get_google_pagespeed(comp_url)
                comp_moz = get_moz_metrics(comp_url, MOZ_ACCESS_ID, MOZ_SECRET_KEY)
                
                comp_ext = [
                    a["href"] for a in comp_soup.find_all("a", href=True)
                    if tldextract.extract(a["href"]).registered_domain not in [comp_domain, "", None]
                ]

                comp_data = {
                    "url": comp_url,
                    "domain": comp_domain,
                    "speed": comp_psi.get("perf", "N/A"),
                    "words": comp_words,
                    "h1": comp_h1s[0] if comp_h1s else "None detected",
                    "h1_count": len(comp_h1s),
                    "ext_links": len(comp_ext),
                    "moz": comp_moz
                }
            except Exception as comp_err:
                st.warning(f"Competitor crawl skipped due to connection limit: {comp_err}")

        # Gap calculation
        client_words = client_word_count
        comp_words_val = comp_data['words'] if comp_data else 0
        comp_da_val = comp_data['moz']['da'] if comp_data else "N/A"
        gap_data = calculate_backlink_gap(competition_level, client_words=client_words, comp_words=comp_words_val, moz_da=moz_client['da'], comp_da=comp_da_val)

        # Gemini AI Pitch
        gemini_strategy = get_gemini_private_strategy(
            target_url, title, meta_desc, len(h1_tags), psi_data, tech_diag, gap_data, active_keyword, moz_client, comp_data=comp_data
        )

        # Sheet Webhook (with Moz Metrics)
        if GOOGLE_SHEET_WEBHOOK_URL and "script.google.com" in GOOGLE_SHEET_WEBHOOK_URL:
            try:
                sheet_payload = {
                    "name": user_display_name,
                    "email": email,
                    "url": target_url,
                    "competitor_url": comp_url if comp_data else "N/A",
                    "moz_da": moz_client['da'],
                    "moz_pa": moz_client['pa'],
                    "moz_spam": moz_client['spam'],
                    "perf_score": psi_data['perf'],
                    "comp_speed": comp_data['speed'] if comp_data else "N/A",
                    "client_words": client_words,
                    "comp_words": comp_words_val,
                    "ai_strategy": gemini_strategy
                }
                requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=sheet_payload, timeout=6)
            except Exception:
                pass

        st.success(f"Audit completed successfully for {user_display_name}!")

        # ==========================================================
        # 📊 LIVE MOZ & SPEED METRICS CARDS (UI)
        # ==========================================================
        st.markdown("### 🏆 Live Moz Authority & Performance Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Moz Domain Authority (DA)", f"{moz_client['da']}/100")
        m2.metric("Moz Page Authority (PA)", f"{moz_client['pa']}/100")
        m3.metric("Moz Spam Score", f"{moz_client['spam']}%" if moz_client['spam'] != "N/A" else "N/A")
        m4.metric("Mobile PageSpeed", f"{psi_data['perf']}/100")

        # ==========================================================
        # ⚔️ SIDE-BY-SIDE COMPETITOR COMPARISON (UI)
        # ==========================================================
        if comp_data:
            st.markdown("### ⚔️ Side-by-Side Competitor Benchmark (With Moz Authority)")
            cmp_col1, cmp_col2 = st.columns(2)
            
            with cmp_col1:
                with st.container(border=True):
                    st.markdown(f"#### 🌐 Your Site: `{base_domain}`")
                    st.write(f"• **Moz DA:** {moz_client['da']}/100 | **PA:** {moz_client['pa']}/100")
                    st.write(f"• **Moz Spam Score:** {moz_client['spam']}%")
                    st.write(f"• **Mobile Speed:** {psi_data['perf']}/100")
                    st.write(f"• **Word Count:** {client_words:,} words")
                    st.write(f"• **H1 Headings:** {len(h1_tags)} detected")

            with cmp_col2:
                with st.container(border=True):
                    comp_m = comp_data['moz']
                    st.markdown(f"#### 🎯 Competitor: `{comp_data['domain']}`")
                    st.write(f"• **Moz DA:** {comp_m['da']}/100 | **PA:** {comp_m['pa']}/100")
                    st.write(f"• **Moz Spam Score:** {comp_m['spam']}%")
                    st.write(f"• **Mobile Speed:** {comp_data['speed']}/100")
                    st.write(f"• **Word Count:** {comp_data['words']:,} words")
                    st.write(f"• **Primary Heading:** {comp_data['h1'][:40]}...")

            if gap_data['da_gap_note']:
                st.info(f"⚡ **Moz DA Analysis:** {gap_data['da_gap_note']}")

            if gap_data['word_diff'] > 0:
                st.warning(f"⚠️ **Content Depth Gap:** Competitor has **{gap_data['word_diff']:,} more words** on their target page. Expand your topical coverage.")
            else:
                st.success("✅ **Content Depth:** Your page has equal or higher word count than your direct competitor.")

        # Google SERP Snippet Preview
        st.markdown("### 🔎 Live Google SERP Snippet Simulation")
        display_title = title if title else "Untitled Page"
        is_title_truncated = len(display_title) > 60
        serp_preview_title = (display_title[:57] + "...") if is_title_truncated else display_title
        
        display_desc = meta_desc if meta_desc else "No meta description specified. Search engine algorithms will automatically pull content snippets from the page."
        is_desc_truncated = len(display_desc) > 155
        serp_preview_desc = (display_desc[:152] + "...") if is_desc_truncated else display_desc

        with st.container(border=True):
            st.caption(f"🌐 **{base_domain}** › {target_url[:65]}")
            st.markdown(f"#### :blue[{serp_preview_title}]")
            st.write(serp_preview_desc)

        # Technical Diagnostics
        st.markdown("### 🛠️ Deep Technical Diagnostics")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.write(f"• **Robots.txt:** {tech_diag['robots']}")
            st.write(f"• **XML Sitemap:** {tech_diag['sitemap']}")
        with t_col2:
            st.write(f"• **Schema Markup:** {tech_diag['schema']}")
            st.write(f"• **Internal Link Integrity:** {tech_diag['broken_status']}")

        st.info(f"🎯 **Authority Gap for '{active_keyword}':** Top ranking competitors average **{gap_data['benchmark_rd']}**. We estimate an immediate requirement of **{gap_data['gap_estimate']}** to challenge top rankings.")

        pri_h1 = h1_tags[0] if h1_tags else "None detected"
        ssl_val = "Active (Secure)" if target_url.startswith("https") else "Missing (Insecure)"

        pdf_payload = {
            'client': user_display_name,
            'email': email,
            'url': target_url,
            'domain': base_domain,
            'keyword': active_keyword,
            'comp_tier': competition_level,
            'gap_data': gap_data,
            'comp_data': comp_data,
            'client_words': client_words,
            'moz': moz_client,
            'tech_diag': tech_diag,
            'psi': psi_data,
            'ssl': ssl_val,
            'canonical': canonical_url,
            'title': title if title else "Not Specified",
            'title_len': len(title),
            'desc': meta_desc if meta_desc else "Not Specified",
            'desc_len': len(meta_desc),
            'h1_count': len(h1_tags),
            'primary_h1': pri_h1,
            'total_img': len(images),
            'missing_alt': len(missing_alt),
            'int_links': len(internal_links),
            'ext_links': len(external_links)
        }

        # Build PDF
        pdf_file_bytes = build_pdf_report(pdf_payload)
        st.download_button(
            label="📥 Download Executive Visual SEO & Moz Authority Audit (PDF)",
            data=pdf_file_bytes,
            file_name=f"SEO_Audit_Moz_{base_domain}.pdf",
            mime="application/pdf"
        )
