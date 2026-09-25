import base64
import urllib.parse
from bs4 import BeautifulSoup
import requests
import streamlit as st
import tldextract

st.set_page_config(page_title="SEO & Technical Audit Tool", layout="wide")

st.title("SEO & Technical Audit Tool")
st.write("Enter your details and website URL to generate an in-depth audit report.")

def get_google_pagespeed(target_url):
    endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={urllib.parse.quote(target_url)}&strategy=mobile"
    try:
        res = requests.get(endpoint, timeout=30).json()
        lighthouse = res.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        perf_score = int(categories.get("performance", {}).get("score", 0) * 100) if categories.get("performance") else "N/A"
        seo_score = int(categories.get("seo", {}).get("score", 0) * 100) if categories.get("seo") else "N/A"
        audits = lighthouse.get("audits", {})
        fcp = audits.get("first-contentful-paint", {}).get("displayValue", "N/A")
        lcp = audits.get("largest-contentful-paint", {}).get("displayValue", "N/A")
        cls_val = audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A")
        return {"performance_score": perf_score, "seo_score": seo_score, "fcp": fcp, "lcp": lcp, "cls": cls_val}
    except Exception:
        return {"performance_score": "N/A", "seo_score": "N/A", "fcp": "N/A", "lcp": "N/A", "cls": "N/A"}

with st.form("audit_form"):
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name (Optional)", placeholder="e.g. Talha")
    with col2:
        last_name = st.text_input("Last Name (Optional)", placeholder="e.g. Mahmood")
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
        with st.spinner(f"Analyzing {target_url}... Generating report."):
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
            h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
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
            st.success(f"Audit completed successfully for {user_display_name}!")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Performance", f"{psi_data['performance_score']}/100")
            c2.metric("Lighthouse SEO", f"{psi_data['seo_score']}/100")
            c3.metric("H1 Tags", len(h1_tags))
            c4.metric("Missing ALT", len(missing_alt))
            report_lines = [
                "=" * 60,
                "COMPLETE SEO & TECHNICAL AUDIT REPORT",
                f"Client Name: {user_display_name}",
                f"Client Email: {email}",
                f"Target URL: {target_url}",
                "=" * 60,
                "[1] TECHNICAL & CORE WEB VITALS",
                f"- Performance Score: {psi_data['performance_score']}/100",
                f"- Google SEO Score: {psi_data['seo_score']}/100",
                f"- FCP: {psi_data['fcp']}",
                f"- LCP: {psi_data['lcp']}",
                f"- CLS: {psi_data['cls']}",
                f"- SSL: {'Yes' if target_url.startswith('https') else 'No'}",
                f"- Canonical: {canonical_url}",
                "[2] ON-PAGE SEO",
                f"- Title: {title} ({len(title)} chars)",
                f"- Description: {meta_desc if meta_desc else 'Missing'} ({len(meta_desc)} chars)",
                f"- H1 Count: {len(h1_tags)}",
                f"- Primary H1: {h1_tags[0] if h1_tags else 'None'}",
                f"- H2 Count: {len(h2_tags)}",
                f"- Total Images: {len(images)} (Missing ALT: {len(missing_alt)})",
                "[3] LINKS & SIGNALS",
                f"- Internal Links: {len(internal_links)}",
                f"- External Links: {len(external_links)}",
                f"- Google Index: https://www.google.com/search?q=site%3A{base_domain}",
                f"- Backlinks: https://ahrefs.com/backlink-checker/?input={base_domain}",
                "=" * 60,
                "ACTION ITEMS",
                "=" * 60
            ]
            if len(h1_tags) != 1:
                report_lines.append(f"- Heading Fix: Found {len(h1_tags)} H1 tags. Keep exactly 1 H1.")
            if not (50 <= len(title) <= 60):
                report_lines.append(f"- Title Fix: Length is {len(title)} chars (Ideal: 50-60).")
            if not (140 <= len(meta_desc) <= 160):
                report_lines.append(f"- Description Fix: Length is {len(meta_desc)} chars (Ideal: 140-160).")
            if len(missing_alt) > 0:
                report_lines.append(f"- Images: Add ALT text to {len(missing_alt)} images.")
            if isinstance(psi_data["performance_score"], int) and psi_data["performance_score"] < 70:
                report_lines.append(f"- Speed Fix: Mobile score is {psi_data['performance_score']}/100. Optimize assets.")
            full_report = "\n".join(report_lines)
            st.text_area("Audit Report Preview", full_report, height=360)
            st.download_button(
                label="Download Written Report (.TXT)",
                data=full_report,
                file_name=f"SEO_Audit_{base_domain}.txt",
                mime="text/plain"
            )
