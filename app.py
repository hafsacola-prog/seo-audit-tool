import urllib.parse
import requests
from bs4 import BeautifulSoup
import streamlit as st
import tldextract

st.set_page_config(page_title="Free SEO Audit Tool", layout="wide")

st.title("🔍 Free SEO & Technical Audit Tool")
st.write(
    "Apni website ka URL enter karein aur live on-page, speed aur technical"
    " report hasil karein."
)

target_url = st.text_input(
    "Website URL enter karein:", placeholder="https://rankcenter.net"
)
run_btn = st.button("Generate Audit Report 🚀")


def get_pagespeed(url):
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
    return {"perf": perf, "seo": seo, "fcp": fcp, "lcp": lcp}
  except Exception:
    return {"perf": "N/A", "seo": "N/A", "fcp": "N/A", "lcp": "N/A"}


if run_btn and target_url:
  if not target_url.startswith("http"):
    target_url = "https://" + target_url

  with st.spinner("Website analyze ho rahi hai... Please wait (~10-15s)..."):
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

      psi = get_pagespeed(target_url)

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

      st.success("✅ Audit Completed!")

      col1, col2, col3, col4 = st.columns(4)
      col1.metric("Mobile Speed", f"{psi['perf']}/100")
      col2.metric("Lighthouse SEO", f"{psi['seo']}/100")
      col3.metric("Largest Paint (LCP)", psi["lcp"])
      col4.metric("Total Images", len(images))

      st.markdown("---")
      st.subheader("📋 On-Page SEO Breakdown")

      if 50 <= len(title) <= 60:
        st.success(f"**Meta Title ({len(title)} chars):** {title}")
      else:
        st.warning(
            f"**Meta Title Issue ({len(title)} chars - Target: 50-60 chars):**"
            f" {title if title else 'Missing'}"
        )

      if 140 <= len(meta_desc) <= 160:
        st.success(f"**Meta Description ({len(meta_desc)} chars):** {meta_desc}")
      else:
        st.warning(
            f"**Meta Description Issue ({len(meta_desc)} chars - Target:"
            f" 140-160 chars):** {meta_desc if meta_desc else 'Missing'}"
        )

      if len(h1s) == 1:
        st.success(f"**H1 Heading (1 Found):** {h1s[0]}")
      else:
        st.error(
            f"**H1 Tag Issue:** Exactly 1 H1 required, found {len(h1s)} tags."
        )

      st.info(f"**H2 Subheadings Found:** {len(h2s)}")
      st.info(
          f"**Internal Links:** {len(internals)} | **External Links:**"
          f" {len(externals)}"
      )

      if len(no_alt) > 0:
        st.warning(f"**Images Missing ALT:** {len(no_alt)} images need ALT tags.")
      else:
        st.success("**All images have ALT text.**")

      st.markdown("---")
      st.subheader("🛠 Priority Fixes")
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
      st.error(f"Website analyze karne me masla aaya: {err}")
