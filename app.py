Python
import base64
import urllib.parse
from bs4 import BeautifulSoup
import requests
import streamlit as st
import tldextract

st.set_page_config(page_title="Free SEO Audit Tool", layout="wide")

st.markdown(
    '
🔍 Free SEO & Technical Audit Tool
',
unsafe_allow_html=True,
)
st.markdown(
'
Apni'
" details aur website URL enter karein taake complete written on-page,"
" speed aur technical report hasil ki ja sake.
",
unsafe_allow_html=True,
)
def get_google_pagespeed(target_url):
endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={urllib.parse.quote(target_url)}&strategy=mobile"
try:
res = requests.get(endpoint, timeout=30).json()
lighthouse = res.get("lighthouseResult", {})
categories = lighthouse.get("categories", {})

perf_score = (
    int(categories.get("performance", {}).get("score", 0) * 100)
    if categories.get("performance")
    else "N/A"
)
seo_score = (
    int(categories.get("seo", {}).get("score", 0) * 100)
    if categories.get("seo")
    else "N/A"
)
audits = lighthouse.get("audits", {})
fcp = audits.get("first-contentful-paint", {}).get("displayValue", "N/A")
lcp = audits.get("largest-contentful-paint", {}).get("displayValue", "N/A")
cls_val = audits.get("cumulative-layout-shift", {}).get(
    "displayValue", "N/A"
)
return {
    "performance_score": perf_score,
    "seo_score": seo_score,
    "fcp": fcp,
    "lcp": lcp,
    "cls": cls_val,
}
except Exception:
return {
"performance_score": "N/A",
"seo_score": "N/A",
"fcp": "N/A",
"lcp": "N/A",
"cls": "N/A",
}
with st.form("lead_form"):
col1, col2 = st.columns(2)
with col1:
first_name = st.text_input("First Name *", placeholder="e.g. Talha")
with col2:
last_name = st.text_input("Last Name *", placeholder="e.g. Mahmood")

email = st.text_input("Business Email *", placeholder="e.g. name@company.com")
website_url = st.text_input(
"Website URL *", placeholder="https://example.com"
)
submit_btn = st.form_submit_button("Generate Audit Report 🚀")
if submit_btn:
if not first_name.strip():
st.error("⚠️ Please enter your First Name.")
elif not last_name.strip():
st.error("⚠️ Please enter your Last Name.")
elif not email.strip() or "@" not in email or "." not in email:
st.error("⚠️ Please enter a valid Email address.")
elif not website_url.strip():
st.error("⚠️ Please enter a Website URL.")
else:
target_url = website_url.strip()
if not target_url.startswith("http"):
target_url = "https://" + target_url
with st.spinner(
    f"Analyzing {target_url} for {first_name}... Please wait ~15 seconds."
):
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  try:
    response = requests.get(target_url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")
  except Exception as e:
    st.error(f"❌ Failed to reach website: {e}")
    st.stop()

  title = (
      soup.title.string.strip() if soup.title and soup.title.string else ""
  )
  meta_desc = ""
  desc_tag = soup.find(
      "meta", attrs={"name": "description"}
  ) or soup.find("meta", attrs={"property": "og:description"})
  if desc_tag:
    meta_desc = desc_tag.get("content", "").strip()

  h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
  h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]

  canonical = soup.find("link", rel="canonical")
  canonical_url = canonical.get("href") if canonical else "Missing"

  images = soup.find_all("img")
  missing_alt = [
      img.get("src", "Unknown")
      for img in images
      if not img.get("alt") or img.get("alt").strip() == ""
  ]

  base_domain = tldextract.extract(target_url).registered_domain
  internal_links, external_links = [], []
  for a in soup.find_all("a", href=True):
    href = a["href"].strip()
    if href.startswith("#") or href.startswith("javascript:") or not href:
      continue
    link_domain = tldextract.extract(href).registered_domain
    if not link_domain or link_domain == base_domain:
      internal_links.append(href)
    else:
      external_links.append(href)

  psi_data = get_google_pagespeed(target_url)

  st.success(f"Audit Completed Successfully for {first_name} {last_name}!")

  m1, m2, m3, m4 = st.columns(4)
  m1.metric("Performance Score", f"{psi_data['performance_score']}/100")
  m2.metric("Google SEO Score", f"{psi_data['seo_score']}/100")
  m3.metric("H1 Tags Count", len(h1_tags))
  m4.metric("Images Missing ALT", len(missing_alt))

  report_lines = [
      "=" * 70,
      "COMPLETE SEO & TECHNICAL AUDIT REPORT".center(70),
      f"Client Name: {first_name} {last_name}",
      f"Client Email: {email}",
      f"Target URL : {target_url}",
      "=" * 70,
      "",
      "[1] TECHNICAL & CORE WEB VITALS (Google PageSpeed API)",
      "-" * 70,
      f"• Mobile Performance Score : {psi_data['performance_score']}/100",
      f"• Google SEO Audit Score   : {psi_data['seo_score']}/100",
      f"• First Contentful Paint   : {psi_data['fcp']}",
      f"• Largest Contentful Paint : {psi_data['lcp']} (Target: < 2.5s)",
      f"• Cumulative Layout Shift  : {psi_data['cls']} (Target: < 0.1)",
      (
          "• SSL / HTTPS Active       : Yes (Secure)"
          if target_url.startswith("https")
          else "• SSL / HTTPS Active       : No (Insecure)"
      ),
      f"• Canonical Tag            : {canonical_url}",
      "",
      "[2] ON-PAGE SEO & CONTENT ARCHITECTURE",
      "-" * 70,
      f'• Meta Title: "{title}"',
      (
          f"  - Length: {len(title)} characters ("
          + ("Optimal" if 50 <= len(title) <= 60 else "Needs Optimization")
          + ")"
      ),
      f'• Meta Description: "{meta_desc if meta_desc else "Missing"}"',
      (
          f"  - Length: {len(meta_desc)} characters ("
          + (
              "Optimal"
              if 140 <= len(meta_desc) <= 160
              else "Needs Optimization"
          )
          + ")"
      ),
      (
          f"• Headings Hierarchy: H1 Count = {len(h1_tags)} ("
          + (
              "Optimal"
              if len(h1_tags) == 1
              else "Critical: Needs exactly one H1"
          )
          + ")"
      ),
      f"  - Primary H1: {h1_tags[0] if h1_tags else 'None detected'}",
      f"  - H2 Tags Detected: {len(h2_tags)}",
      f"• Image Optimization: Total {len(images)}, Missing ALT:"
      f" {len(missing_alt)}",
      "",
      "[3] INTERNAL LINKING & OFF-PAGE SIGNALS",
      "-" * 70,
      f"• Internal Links Detected  : {len(internal_links)}",
      f"• External Outbound Links  : {len(external_links)}",
      (
          "• Search Indexing Verification :"
          f" https://www.google.com/search?q=site%3A{base_domain}"
      ),
      (
          "• Free Backlink Profile Check  :"
          f" https://ahrefs.com/backlink-checker/?input={base_domain}"
      ),
      "",
      "=" * 70,
      "PRIORITY ACTION ITEMS".center(70),
      "=" * 70,
  ]

  if len(h1_tags) != 1:
    report_lines.append(
        f"- Heading Fix: Found {len(h1_tags)} H1 tags. Keep exactly 1 H1 per"
        " page."
    )
  if not (50 <= len(title) <= 60):
    report_lines.append(
        f"- Meta Title Fix: Current length is {len(title)} chars (Target:"
        " 50-60)."
    )
  if not (140 <= len(meta_desc) <= 160):
    report_lines.append(
        f"- Meta Description Fix: Current length is {len(meta_desc)} chars"
        " (Target: 140-160)."
    )
  if len(missing_alt) > 0:
    report_lines.append(
        f"- Image SEO: Add descriptive ALT text to {len(missing_alt)}"
        " images."
    )
  if (
      isinstance(psi_data["performance_score"], int)
      and psi_data["performance_score"] < 70
  ):
    report_lines.append(
        "- Speed Optimization: Mobile score is"
        f" {psi_data['performance_score']}/100. Compress images & reduce JS."
    )

  full_report = "\n".join(report_lines)
  st.text_area("Full Written SEO Report", full_report, height=380)

  st.download_button(
      label="📥 Download Written Report (TXT)",
      data=full_report,
      file_name=f"SEO_Audit_{base_domain}.txt",
      mime="text/plain",
  )
