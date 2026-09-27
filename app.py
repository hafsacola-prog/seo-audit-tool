import base64
import json
import urllib.parse
from bs4 import BeautifulSoup
import requests
import streamlit as st
import tldextract

# Page Configuration
st.set_page_config(page_title="SEO & Technical Audit Engine", layout="wide")

# Streamlit Secrets se API Keys fetch karna
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
SHEET_WEBHOOK_URL = st.secrets.get("SHEET_WEBHOOK_URL", "")


def get_pagespeed(url):
  """Google PageSpeed Insights API call"""
  endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={urllib.parse.quote(url)}&strategy=mobile"
  try:
    res = requests.get(endpoint, timeout=30).json()
    cats = res.get("lighthouseResult", {}).get("categories", {})
    audits = res.get("lighthouseResult", {}).get("audits", {})

    perf = (
        int(cats.get("performance", {}).get("score", 0) * 100)
        if cats.get("performance")
        else "N/A"
    )
    seo = (
        int(cats.get("seo", {}).get("score", 0) * 100)
        if cats.get("seo")
        else "N/A"
    )
    fcp = audits.get("first-contentful-paint", {}).get(
        "displayValue", "Unknown"
    )
    lcp = audits.get("largest-contentful-paint", {}).get(
        "displayValue", "Unknown"
    )
    cls_val = audits.get("cumulative-layout-shift", {}).get(
        "displayValue", "Unknown"
    )
    return {
        "perf": perf,
        "seo": seo,
        "fcp": fcp,
        "lcp": lcp,
        "cls": cls_val,
    }
  except Exception:
    return {
        "perf": "N/A",
        "seo": "N/A",
        "fcp": "N/A",
        "lcp": "N/A",
        "cls": "N/A",
    }


def get_gemini_private_strategy(
    url, title, meta_desc, h1_count, psi, broken_count, ext_links_count, keyword
):
  """Gemini AI Outreach & SEO Action Strategy Generator"""
  if not GEMINI_API_KEY:
    return "Gemini API key not configured in Streamlit Secrets."

  prompt = f"""
    You are an expert SEO strategist. Analyze these live audit findings for client website {url}:
    - Target Keyword / Niche: {keyword if keyword else 'General SEO'}
    - Title Tag: {title}
    - Meta Description: {meta_desc}
    - H1 Tag Count: {h1_count}
    - Mobile Performance Score: {psi.get('perf', 'N/A')}/100
    - Lighthouse SEO Score: {psi.get('seo', 'N/A')}/100
    - Broken Links Detected: {broken_count}
    - Outbound Links: {ext_links_count}

    Write a concise agency outreach strategy (under 120 words):
    1. 2 quick-win technical fixes.
    2. A short personalized cold pitch angle to sell them high-authority backlinks and SEO services.
    """

  headers = {"Content-Type": "application/json"}
  body = {"contents": [{"parts": [{"text": prompt}]}]}

  # Auto-fallback models list
  candidate_models = [
      "gemini-2.5-flash",
      "gemini-2.0-flash",
      "gemini-1.5-flash",
      "gemini-1.5-flash-latest",
      "gemini-pro",
  ]
  try:
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    list_res = requests.get(list_url, timeout=8).json()
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

  last_err = ""
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
        last_err = (
            f"Model {model_name} Error:"
            f" {res_data['error'].get('message', 'Unknown')}"
        )
    except Exception as e:
      last_err = str(e)
      continue

  return f"Gemini generation failed. Details: {last_err}"


def send_to_google_sheet(payload):
  """Google Sheets Webhook par data bhejna"""
  if not SHEET_WEBHOOK_URL:
    return
  try:
    requests.post(SHEET_WEBHOOK_URL, json=payload, timeout=10)
  except Exception:
    pass


# ==========================================================
# UI INTERFACE
# ==========================================================
st.title("🔍 Complete SEO & Technical Audit Engine")
st.write(
    "Target website ka URL enter karein aur live technical, on-page, speed aur"
    " AI outreach report hasil karein."
)

col_in1, col_in2 = st.columns([3, 1])
with col_in1:
  target_url = st.text_input(
      "Website URL:", placeholder="https://example.com"
  )
with col_in2:
  target_keyword = st.text_input(
      "Focus Keyword (Optional):", placeholder="SEO Services"
  )

run_btn = st.button("Generate Audit Report 🚀", use_container_width=True)

if run_btn and target_url:
  if not target_url.startswith("http"):
    target_url = "https://" + target_url

  with st.spinner(
      "Audit chal raha hai... Google PageSpeed aur Page DOM analyze ho rahe"
      " hain..."
  ):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
      resp = requests.get(target_url, headers=headers, timeout=15)
      soup = BeautifulSoup(resp.text, "html.parser")
      domain_info = tldextract.extract(target_url)
      base_domain = f"{domain_info.domain}.{domain_info.suffix}"

      # Speed test
      psi = get_pagespeed(target_url)

      # On-Page Data Crawl
      title = (
          soup.title.string.strip() if soup.title and soup.title.string else ""
      )
      desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
          "meta", attrs={"property": "og:description"}
      )
      meta_desc = desc_tag.get("content", "").strip() if desc_tag else ""

      h1s = [
          h.get_text(strip=True)
          for h in soup.find_all("h1")
          if h.get_text(strip=True)
      ]
      h2s = [
          h.get_text(strip=True)
          for h in soup.find_all("h2")
          if h.get_text(strip=True)
      ]

      images = soup.find_all("img")
      no_alt = [img for img in images if not img.get("alt")]

      internals = [
          a["href"]
          for a in soup.find_all("a", href=True)
          if tldextract.extract(a["href"]).registered_domain
          in [base_domain, ""]
      ]
      externals = [
          a["href"]
          for a in soup.find_all("a", href=True)
          if tldextract.extract(a["href"]).registered_domain
          not in [base_domain, "", None]
      ]

      # Gemini AI Strategy
      gemini_strategy = get_gemini_private_strategy(
          url=target_url,
          title=title,
          meta_desc=meta_desc,
          h1_count=len(h1s),
          psi=psi,
          broken_count=0,
          ext_links_count=len(externals),
          keyword=target_keyword,
      )

      # Google Sheets par auto-sync
      sheet_payload = {
          "url": target_url,
          "keyword": target_keyword,
          "title_length": len(title),
          "meta_length": len(meta_desc),
          "h1_count": len(h1s),
          "speed_score": psi["perf"],
          "seo_score": psi["seo"],
          "missing_alt": len(no_alt),
          "gemini_strategy": gemini_strategy,
      }
      send_to_google_sheet(sheet_payload)

      # ==========================================================
      # REPORT DISPLAY
      # ==========================================================
      st.success("✅ Audit Kamyabi Se Mukammal Ho Gaya!")

      col1, col2, col3, col4 = st.columns(4)
      col1.metric("Mobile Speed", f"{psi['perf']}/100")
      col2.metric("Lighthouse SEO", f"{psi['seo']}/100")
      col3.metric("Largest Paint (LCP)", psi["lcp"])
      col4.metric("Cumulative Shift (CLS)", psi["cls"])

      st.markdown("---")
      st.subheader("📋 On-Page SEO Breakdown")

      if 50 <= len(title) <= 60:
        st.success(f"**Meta Title ({len(title)} chars):** {title}")
      else:
        st.warning(
            f"**Meta Title Issue ({len(title)} chars - Ideal: 50-60):**"
            f" {title if title else 'Missing'}"
        )

      if 140 <= len(meta_desc) <= 160:
        st.success(f"**Meta Description ({len(meta_desc)} chars):** {meta_desc}")
      else:
        st.warning(
            f"**Meta Description Issue ({len(meta_desc)} chars - Ideal:"
            f" 140-160):** {meta_desc if meta_desc else 'Missing'}"
        )

      if len(h1s) == 1:
        st.success(f"**H1 Heading (1 Found):** {h1s[0]}")
      else:
        st.error(
            f"**H1 Tag Issue:** Exactly 1 primary H1 required, but {len(h1s)}"
            " found."
        )

      st.info(f"**H2 Subheadings Found:** {len(h2s)}")
      st.info(
          f"**Internal Links:** {len(internals)} | **External Links:**"
          f" {len(externals)}"
      )

      if len(no_alt) > 0:
        st.warning(f"**Images Missing ALT:** {len(no_alt)} images need ALT tags.")
      else:
        st.success("**All images have descriptive ALT text.**")

      st.markdown("---")
      st.subheader("🤖 AI Outreach Pitch & Growth Strategy")
      st.markdown(f"> {gemini_strategy}")

      st.markdown("---")
      st.subheader("🛠 Priority Fixes List")
      fixes = []
      if len(h1s) != 1:
        fixes.append("Keep only 1 primary H1 tag targeting your main keyword.")
      if not (50 <= len(title) <= 60):
        fixes.append(
            f"Update Meta Title length to 50-60 characters (currently"
            f" {len(title)})."
        )
      if not (140 <= len(meta_desc) <= 160):
        fixes.append(
            f"Optimize Meta Description to 140-160 characters (currently"
            f" {len(meta_desc)})."
        )
      if len(no_alt) > 0:
        fixes.append(f"Add descriptive keyword ALT text to {len(no_alt)} images.")

      if fixes:
        for f in fixes:
          st.write(f"👉 {f}")
      else:
        st.write("🎉 No critical on-page issues detected!")

    except Exception as err:
      st.error(f"Website analyze karne me error aaya: {err}")
