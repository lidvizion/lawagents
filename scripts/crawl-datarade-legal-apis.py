#!/usr/bin/env python3
"""
Crawl dataRade legal APIs and refresh docs/tools/legal-apis-index.json.

dataRade has no public API (Cloudflare). Uses OpenAI (discover_legal_tools_full
and a supplemental prompt) plus large curated static lists when the API key is absent.

MongoDB update is optional when MONGODB_URI or MONGO_URI is set.

Usage:
  export OPENAI_API_KEY=sk-...   # optional; expands discovery via OpenAI
  export MONGODB_URI=...         # optional
  python scripts/crawl-datarade-legal-apis.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
load_dotenv(REPO_ROOT / ".env")

CURATED_LEGAL_APIS = [
    {"name": "UniCourt", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-providers/unicourt/data-products"},
    {"name": "Bloomberg Law Dockets API", "provider": "Bloomberg", "category": "court-data", "url": "https://pro.bloomberglaw.com/products/court-dockets-search/enterprise-dockets-api-solution/"},
    {"name": "LegiScan API", "provider": "LegiScan", "category": "legislative", "url": "https://legiscan.com/legiscan"},
    {"name": "OpenLaws API", "provider": "OpenLaws", "category": "legislative", "url": "https://openlaws.us/api/"},
    {"name": "TrustFoundry AI", "provider": "TrustFoundry", "category": "legal-ai", "url": "https://trustfoundry.ai/"},
    {"name": "PACER API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/pacer-api-unicourt"},
    {"name": "Court Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/court-data-api-unicourt"},
    {"name": "Attorney Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/attorney-data-api-unicourt"},
    {"name": "Law Firm Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/law-firm-data-api-unicourt"},
    {"name": "Judge Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/judge-data-api-unicourt"},
    {"name": "Legal Analytics API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/legal-analytics-api-unicourt"},
    {"name": "APISCRAPY Legal Data", "provider": "APISCRAPY", "category": "court-data", "url": "https://datarade.ai/search/products/legal-apis"},
    {"name": "Grepsr Legal Data", "provider": "Grepsr", "category": "court-data", "url": "https://datarade.ai/search/products/legal-apis"},
    {"name": "InfoTrack", "provider": "InfoTrack", "category": "court-filing", "url": "https://www.infotrack.com/"},
    {"name": "LexisNexis API", "provider": "LexisNexis", "category": "legal-research", "url": "https://www.lexisnexis.com/"},
    {"name": "Westlaw API", "provider": "Thomson Reuters", "category": "legal-research", "url": "https://legal.thomsonreuters.com/"},

]

EXPANDED_STATIC = [
    {"name": "UniCourt Court Data API", "slug": "unicourt-court-api", "category": "court-data", "use_when": "Federal/state court records", "url": "https://unicourt.com", "has_api": True, "has_mcp": False, "provider": "UniCourt"},
    {"name": "UniCourt PACER API", "slug": "unicourt-pacer-api", "category": "court-data", "use_when": "PACER federal court data", "url": "https://unicourt.com", "has_api": True, "has_mcp": False, "provider": "UniCourt"},
    {"name": "CourtListener API", "slug": "courtlistener-api", "category": "court-data", "use_when": "PACER, case law, RECAP", "url": "https://courtlistener.com/api", "has_api": True, "has_mcp": False, "provider": "Free Law Project"},
    {"name": "vLex API", "slug": "vlex-api", "category": "legal-ai", "use_when": "Legal research, document analysis", "url": "https://vlex.com", "has_api": True, "has_mcp": False, "provider": "vLex"},
    {"name": "Docket Alarm API", "slug": "docket-alarm-api", "category": "court-data", "use_when": "Federal docket filings", "url": "https://docketalarm.com", "has_api": True, "has_mcp": False, "provider": "Docket Alarm"},
    {"name": "Trellis Research", "slug": "trellis-research", "category": "court-data", "use_when": "State court analytics", "url": "https://trellis.law", "has_api": True, "has_mcp": False, "provider": "Trellis"},
    {"name": "Casetext", "slug": "casetext", "category": "legal-ai", "use_when": "Legal research, AI drafting", "url": "https://casetext.com", "has_api": True, "has_mcp": False, "provider": "Casetext"},
    {"name": "Fastcase", "slug": "fastcase", "category": "legal-ai", "use_when": "Legal research, case law", "url": "https://fastcase.com", "has_api": True, "has_mcp": False, "provider": "Fastcase"},
    {"name": "Westlaw", "slug": "westlaw", "category": "legal-ai", "use_when": "Legal research, primary law", "url": "https://westlaw.com", "has_api": True, "has_mcp": False, "provider": "Thomson Reuters"},
    {"name": "Lexis+", "slug": "lexis-plus", "category": "legal-ai", "use_when": "Legal research, AI drafting", "url": "https://lexis.com", "has_api": True, "has_mcp": False, "provider": "LexisNexis"},
    {"name": "Relativity", "slug": "relativity", "category": "e-discovery", "use_when": "Enterprise e-discovery", "url": "https://relativity.com", "has_api": True, "has_mcp": False, "provider": "Relativity"},
    {"name": "Goldfynch", "slug": "goldfynch", "category": "e-discovery", "use_when": "Small-matter e-discovery", "url": "https://goldfynch.com", "has_api": True, "has_mcp": False, "provider": "Goldfynch"},
    {"name": "Logikull", "slug": "logikull", "category": "e-discovery", "use_when": "E-discovery, review", "url": "https://logikull.com", "has_api": False, "has_mcp": False, "provider": "Logikull"},
    {"name": "Smokeball", "slug": "smokeball", "category": "practice-management", "use_when": "Solo/small practice", "url": "https://smokeball.com", "has_api": True, "has_mcp": False, "provider": "Smokeball"},
    {"name": "PracticePanther", "slug": "practice-panther", "category": "practice-management", "use_when": "Practice management", "url": "https://practicepanther.com", "has_api": True, "has_mcp": False, "provider": "PracticePanther"},
    {"name": "SmartAdvocate", "slug": "smartadvocate", "category": "pi-specific", "use_when": "PI case management", "url": "https://smartadvocate.com", "has_api": True, "has_mcp": False, "provider": "SmartAdvocate"},
    {"name": "Lawmatics", "slug": "lawmatics", "category": "intake-crm", "use_when": "Legal CRM, intake", "url": "https://lawmatics.com", "has_api": True, "has_mcp": False, "provider": "Lawmatics"},
    {"name": "Clio Grow", "slug": "clio-grow", "category": "intake-crm", "use_when": "Legal CRM, intake", "url": "https://clio.com", "has_api": True, "has_mcp": False, "provider": "Clio"},
    {"name": "InfoTrack", "slug": "infotrack", "category": "integrations", "use_when": "Court filing, service of process", "url": "https://infotrack.com", "has_api": True, "has_mcp": False, "provider": "InfoTrack"},
    {"name": "DocuSign", "slug": "docusign", "category": "integrations", "use_when": "E-signatures", "url": "https://docusign.com", "has_api": True, "has_mcp": False, "provider": "DocuSign"},
    {"name": "APISCRAPY Legal API", "slug": "apiscrapy-legal", "category": "court-data", "use_when": "Legal data scraping", "url": "https://datarade.ai", "has_api": True, "has_mcp": False, "provider": "APISCRAPY"},
    {"name": "Grepsr Legal Data", "slug": "grepsr-legal", "category": "court-data", "use_when": "Legal data extraction", "url": "https://grepsr.com", "has_api": True, "has_mcp": False, "provider": "Grepsr"},
    {"name": "Oxylabs Legal API", "slug": "oxylabs-legal", "category": "court-data", "use_when": "Web scraping legal data", "url": "https://oxylabs.io", "has_api": True, "has_mcp": False, "provider": "Oxylabs"},
    {"name": "Nubela Legal API", "slug": "nubela-legal", "category": "court-data", "use_when": "Legal data API", "url": "https://nubela.co", "has_api": True, "has_mcp": False, "provider": "Nubela"},
    {"name": "Rightsify Legal Data", "slug": "rightsify-legal", "category": "court-data", "use_when": "Legal data", "url": "https://rightsify.com", "has_api": True, "has_mcp": False, "provider": "Rightsify"},
    {"name": "BoldData Company Data", "slug": "bolddata-company", "category": "court-data", "use_when": "Company legal data", "url": "https://companydata.com", "has_api": True, "has_mcp": False, "provider": "BoldData"},
    {"name": "The Warren Group", "slug": "warren-group", "category": "court-data", "use_when": "Real estate, court records", "url": "https://thewarrengroup.com", "has_api": True, "has_mcp": False, "provider": "The Warren Group"},
    {"name": "Veridion API", "slug": "veridion-api", "category": "court-data", "use_when": "Company data", "url": "https://veridion.com", "has_api": True, "has_mcp": False, "provider": "Veridion"},
    {"name": "Forager.ai", "slug": "forager-ai", "category": "court-data", "use_when": "Legal data", "url": "https://forager.ai", "has_api": True, "has_mcp": False, "provider": "Forager"},
    {"name": "Luminance", "slug": "luminance", "category": "legal-ai", "use_when": "Contract AI, due diligence", "url": "https://luminance.com", "has_api": True, "has_mcp": False, "provider": "Luminance"},
    {"name": "Kira", "slug": "kira", "category": "legal-ai", "use_when": "Contract analysis, M&A", "url": "https://kira.com", "has_api": True, "has_mcp": False, "provider": "Kira"},
    {"name": "LexisNexis API", "slug": "lexisnexis-api", "category": "legal-ai", "use_when": "Legal research API", "url": "https://lexisnexis.com", "has_api": True, "has_mcp": False, "provider": "LexisNexis"},
    {"name": "Thomson Reuters API", "slug": "thomson-reuters-api", "category": "legal-ai", "use_when": "Legal research API", "url": "https://thomsonreuters.com", "has_api": True, "has_mcp": False, "provider": "Thomson Reuters"},
    {"name": "USPTO API", "slug": "uspto-api", "category": "ip-trademark", "use_when": "Patent, trademark data", "url": "https://uspto.gov", "has_api": True, "has_mcp": False, "provider": "USPTO"},
    {"name": "TrademarkNow", "slug": "trademark-now", "category": "ip-trademark", "use_when": "Trademark search", "url": "https://trademarknow.com", "has_api": True, "has_mcp": False, "provider": "TrademarkNow"},
    {"name": "Lexair", "slug": "lexair", "category": "ip-trademark", "use_when": "Trademark docketing", "url": "https://lexair.com", "has_api": True, "has_mcp": False, "provider": "Lexair"},
    {"name": "FirmPilot", "slug": "firmpilot", "category": "integrations", "use_when": "Law firm marketing", "url": "https://firmpilot.com", "has_api": True, "has_mcp": False, "provider": "FirmPilot"},
    {"name": "Acquimate", "slug": "acquimate", "category": "intake-crm", "use_when": "Legal intake", "url": "https://acquimate.com", "has_api": True, "has_mcp": False, "provider": "Acquimate"},
    {"name": "CARET Legal", "slug": "caret-legal", "category": "practice-management", "use_when": "Practice management", "url": "https://caretlegal.com", "has_api": True, "has_mcp": False, "provider": "CARET"},
    {"name": "Needles", "slug": "needles", "category": "pi-specific", "use_when": "PI case management", "url": "https://needles.com", "has_api": True, "has_mcp": False, "provider": "Needles"},
    {"name": "TrialWorks", "slug": "trialworks", "category": "pi-specific", "use_when": "Litigation management", "url": "https://trialworks.com", "has_api": True, "has_mcp": False, "provider": "TrialWorks"},
    {"name": "AbacusLaw", "slug": "abacuslaw", "category": "practice-management", "use_when": "Practice management", "url": "https://abacuslaw.com", "has_api": True, "has_mcp": False, "provider": "AbacusLaw"},
    {"name": "Eclipse Legal", "slug": "eclipse-legal", "category": "practice-management", "use_when": "Practice management", "url": "https://eclipselegal.com", "has_api": True, "has_mcp": False, "provider": "Eclipse"},
    {"name": "ProLaw", "slug": "prolaw", "category": "practice-management", "use_when": "Enterprise practice management", "url": "https://thomsonreuters.com", "has_api": True, "has_mcp": False, "provider": "Thomson Reuters"},
    {"name": "Elite 3E", "slug": "elite-3e", "category": "practice-management", "use_when": "Enterprise law firm", "url": "https://thomsonreuters.com", "has_api": True, "has_mcp": False, "provider": "Thomson Reuters"},
    {"name": "Aderant Expert", "slug": "aderant-expert", "category": "practice-management", "use_when": "Midsize+ law firm", "url": "https://aderant.com", "has_api": True, "has_mcp": False, "provider": "Aderant"},
    {"name": "iManage", "slug": "imanage", "category": "document-management", "use_when": "Document management", "url": "https://imanage.com", "has_api": True, "has_mcp": False, "provider": "iManage"},
    {"name": "NetDocuments", "slug": "netdocuments", "category": "document-management", "use_when": "Cloud DMS", "url": "https://netdocuments.com", "has_api": True, "has_mcp": False, "provider": "NetDocuments"},
    {"name": "Worldox", "slug": "worldox", "category": "document-management", "use_when": "Document management", "url": "https://worldox.com", "has_api": True, "has_mcp": False, "provider": "Worldox"},
    {"name": "iPro", "slug": "ipro", "category": "e-discovery", "use_when": "E-discovery", "url": "https://iprotec.com", "has_api": True, "has_mcp": False, "provider": "iPro"},
    {"name": "DISCO", "slug": "disco", "category": "e-discovery", "use_when": "E-discovery, AI", "url": "https://csdisco.com", "has_api": True, "has_mcp": False, "provider": "DISCO"},
    {"name": "OpenText Axcelerate", "slug": "opentext-axcelerate", "category": "e-discovery", "use_when": "E-discovery", "url": "https://opentext.com", "has_api": True, "has_mcp": False, "provider": "OpenText"},
    {"name": "Nuix", "slug": "nuix", "category": "e-discovery", "use_when": "E-discovery, investigations", "url": "https://nuix.com", "has_api": True, "has_mcp": False, "provider": "Nuix"},
    {"name": "Everlaw", "slug": "everlaw", "category": "e-discovery", "use_when": "Civil litigation doc review", "url": "https://everlaw.com", "has_api": True, "has_mcp": False, "provider": "Everlaw"},
    {"name": "RapidAPI Legal", "slug": "rapidapi-legal", "category": "integrations", "use_when": "Legal API marketplace", "url": "https://rapidapi.com", "has_api": True, "has_mcp": False, "provider": "RapidAPI"},
    {"name": "Zapier", "slug": "zapier", "category": "integrations", "use_when": "No-code automation", "url": "https://zapier.com", "has_api": True, "has_mcp": True, "provider": "Zapier"},
    {"name": "Make (Integromat)", "slug": "make", "category": "integrations", "use_when": "Automation", "url": "https://make.com", "has_api": True, "has_mcp": False, "provider": "Make"},
    {"name": "n8n", "slug": "n8n", "category": "integrations", "use_when": "Workflow automation", "url": "https://n8n.io", "has_api": True, "has_mcp": True, "provider": "n8n"},
    {"name": "PandaDoc", "slug": "pandadoc", "category": "integrations", "use_when": "Document automation", "url": "https://pandadoc.com", "has_api": True, "has_mcp": False, "provider": "PandaDoc"},
    {"name": "Ironclad", "slug": "ironclad", "category": "legal-ai", "use_when": "Contract lifecycle", "url": "https://ironcladapp.com", "has_api": True, "has_mcp": False, "provider": "Ironclad"},
    {"name": "ContractPodAi", "slug": "contractpodai", "category": "legal-ai", "use_when": "Contract management", "url": "https://contractpodai.com", "has_api": True, "has_mcp": False, "provider": "ContractPodAi"},
    {"name": "Evisort", "slug": "evisort", "category": "legal-ai", "use_when": "Contract AI", "url": "https://evisort.com", "has_api": True, "has_mcp": False, "provider": "Evisort"},
    {"name": "LinkSquares", "slug": "linksquares", "category": "legal-ai", "use_when": "Contract analytics", "url": "https://linksquares.com", "has_api": True, "has_mcp": False, "provider": "LinkSquares"},
    {"name": "Conga", "slug": "conga", "category": "legal-ai", "use_when": "Contract management", "url": "https://conga.com", "has_api": True, "has_mcp": False, "provider": "Conga"},
    {"name": "Agiloft", "slug": "agiloft", "category": "legal-ai", "use_when": "CLM", "url": "https://agiloft.com", "has_api": True, "has_mcp": False, "provider": "Agiloft"},
    {"name": "Icertis", "slug": "icertis", "category": "legal-ai", "use_when": "Enterprise CLM", "url": "https://icertis.com", "has_api": True, "has_mcp": False, "provider": "Icertis"},
    {"name": "Seal Software", "slug": "seal-software", "category": "legal-ai", "use_when": "Contract discovery", "url": "https://seal-software.com", "has_api": True, "has_mcp": False, "provider": "Seal"},
    {"name": "LawGeex", "slug": "lawgeex", "category": "legal-ai", "use_when": "Contract review AI", "url": "https://lawgeex.com", "has_api": True, "has_mcp": False, "provider": "LawGeex"},
    {"name": "LegalSifter", "slug": "legalsifter", "category": "legal-ai", "use_when": "Contract review", "url": "https://legalsifter.com", "has_api": True, "has_mcp": False, "provider": "LegalSifter"},
    {"name": "LexCheck", "slug": "lexcheck", "category": "legal-ai", "use_when": "Contract redlining", "url": "https://lexcheck.com", "has_api": True, "has_mcp": False, "provider": "LexCheck"},
    {"name": "Eigen Technologies", "slug": "eigen-technologies", "category": "legal-ai", "use_when": "Document extraction", "url": "https://eigentech.com", "has_api": True, "has_mcp": False, "provider": "Eigen"},
    {"name": "ThoughtRiver", "slug": "thoughtriver", "category": "legal-ai", "use_when": "Contract pre-screening", "url": "https://thoughtriver.com", "has_api": True, "has_mcp": False, "provider": "ThoughtRiver"},
    {"name": "Brightflag", "slug": "brightflag", "category": "legal-ai", "use_when": "Legal ops, spend", "url": "https://brightflag.com", "has_api": True, "has_mcp": False, "provider": "Brightflag"},
    {"name": "Onit", "slug": "onit", "category": "legal-ai", "use_when": "Enterprise legal", "url": "https://onit.com", "has_api": True, "has_mcp": False, "provider": "Onit"},
    {"name": "Mitratech", "slug": "mitratech", "category": "legal-ai", "use_when": "Legal ops", "url": "https://mitratech.com", "has_api": True, "has_mcp": False, "provider": "Mitratech"},
    {"name": "Casepoint", "slug": "casepoint", "category": "e-discovery", "use_when": "E-discovery", "url": "https://casepoint.com", "has_api": True, "has_mcp": False, "provider": "Casepoint"},
    {"name": "CloudNine", "slug": "cloudnine", "category": "e-discovery", "use_when": "E-discovery", "url": "https://cloudnine.com", "has_api": True, "has_mcp": False, "provider": "CloudNine"},
    {"name": "Nextpoint", "slug": "nextpoint", "category": "e-discovery", "use_when": "E-discovery", "url": "https://nextpoint.com", "has_api": True, "has_mcp": False, "provider": "Nextpoint"},
    {"name": "Zapproved", "slug": "zapproved", "category": "e-discovery", "use_when": "Legal hold", "url": "https://zapproved.com", "has_api": True, "has_mcp": False, "provider": "Zapproved"},
    {"name": "PageVault", "slug": "pagevault", "category": "e-discovery", "use_when": "Web archiving", "url": "https://pagevault.com", "has_api": True, "has_mcp": False, "provider": "PageVault"},
    {"name": "Hanzo", "slug": "hanzo", "category": "e-discovery", "use_when": "Collaboration data", "url": "https://hanzo.com", "has_api": True, "has_mcp": False, "provider": "Hanzo"},
    {"name": "X1 Discovery", "slug": "x1-discovery", "category": "e-discovery", "use_when": "Collection", "url": "https://x1.com", "has_api": True, "has_mcp": False, "provider": "X1"},
    {"name": "IPRO", "slug": "ipro-ecm", "category": "e-discovery", "use_when": "E-discovery", "url": "https://iprotec.com", "has_api": True, "has_mcp": False, "provider": "IPRO"},
    {"name": "Otter.ai", "slug": "otter-ai", "category": "integrations", "use_when": "Deposition transcription", "url": "https://otter.ai", "has_api": True, "has_mcp": False, "provider": "Otter"},
    {"name": "Rev.com", "slug": "rev", "category": "integrations", "use_when": "Legal transcription", "url": "https://rev.com", "has_api": True, "has_mcp": False, "provider": "Rev"},
    {"name": "BigHand", "slug": "bighand", "category": "practice-management", "use_when": "Dictation, workflow", "url": "https://bighand.com", "has_api": True, "has_mcp": False, "provider": "BigHand"},
    {"name": "Nuance Dragon", "slug": "nuance-dragon", "category": "integrations", "use_when": "Legal dictation", "url": "https://nuance.com", "has_api": True, "has_mcp": False, "provider": "Nuance"},
    {"name": "Clio Manage", "slug": "clio-manage", "category": "practice-management", "use_when": "Practice management", "url": "https://clio.com", "has_api": True, "has_mcp": False, "provider": "Clio"},
    {"name": "Clio Suite", "slug": "clio-suite", "category": "practice-management", "use_when": "Full practice suite", "url": "https://clio.com", "has_api": True, "has_mcp": False, "provider": "Clio"},
    {"name": "MyCase", "slug": "mycase", "category": "practice-management", "use_when": "Solo/small firm", "url": "https://mycase.com", "has_api": True, "has_mcp": False, "provider": "MyCase"},
    {"name": "Filevine", "slug": "filevine", "category": "practice-management", "use_when": "PI, litigation, docs", "url": "https://filevine.com", "has_api": True, "has_mcp": False, "provider": "Filevine"},
    {"name": "CASEpeer", "slug": "casepeer", "category": "pi-specific", "use_when": "PI case management", "url": "https://casepeer.com", "has_api": True, "has_mcp": False, "provider": "CASEpeer"},
    {"name": "Litera", "slug": "litera", "category": "legal-ai", "use_when": "Drafting, comparison", "url": "https://litera.com", "has_api": True, "has_mcp": False, "provider": "Litera"},
    {"name": "Litera Transact", "slug": "litera-transact", "category": "transaction-management", "use_when": "Deal management", "url": "https://litera.com", "has_api": True, "has_mcp": False, "provider": "Litera"},
    {"name": "LexiDots", "slug": "lexidots", "category": "ip-trademark", "use_when": "Trademark docketing", "url": "https://lexidots.com", "has_api": True, "has_mcp": False, "provider": "LexiDots"},
    {"name": "Alt Legal", "slug": "altlegal", "category": "ip-trademark", "use_when": "Trademark monitoring", "url": "https://altlegal.com", "has_api": True, "has_mcp": False, "provider": "Alt Legal"},
    {"name": "Harvey", "slug": "harvey", "category": "legal-ai", "use_when": "Large firm AI", "url": "https://harvey.ai", "has_api": True, "has_mcp": False, "provider": "Harvey"},
    {"name": "GC.AI", "slug": "gc-ai", "category": "legal-ai", "use_when": "In-house legal AI", "url": "https://gc.ai", "has_api": True, "has_mcp": False, "provider": "GC.AI"},
    {"name": "Planable", "slug": "planable", "category": "social-scheduling", "use_when": "Multi-channel social", "url": "https://planable.io", "has_api": True, "has_mcp": False, "provider": "Planable"},
    {"name": "Buffer", "slug": "buffer", "category": "social-scheduling", "use_when": "Social scheduling, MCP", "url": "https://buffer.com", "has_api": True, "has_mcp": True, "provider": "Buffer"},
    {"name": "Hootsuite", "slug": "hootsuite", "category": "social-scheduling", "use_when": "Social, MCP", "url": "https://hootsuite.com", "has_api": True, "has_mcp": True, "provider": "Hootsuite"},
    {"name": "Thunderhead", "slug": "thunderhead", "category": "social-scheduling", "use_when": "Law firm marketing", "url": "https://thunderhead.com", "has_api": True, "has_mcp": False, "provider": "Thunderhead"},
    {"name": "Apaya", "slug": "apaya", "category": "social-scheduling", "use_when": "Legal social", "url": "https://apaya.io", "has_api": True, "has_mcp": False, "provider": "Apaya"},
    {"name": "GovInfo API", "slug": "govinfo-api", "category": "legislative", "use_when": "Federal gov documents", "url": "https://api.govinfo.gov", "has_api": True, "has_mcp": False, "provider": "GPO"},
    {"name": "Congress.gov API", "slug": "congress-gov-api", "category": "legislative", "use_when": "Federal legislation", "url": "https://api.congress.gov", "has_api": True, "has_mcp": False, "provider": "LOC"},
    {"name": "RECAP Project", "slug": "recap-project", "category": "court-data", "use_when": "PACER free access", "url": "https://recapthelaw.org", "has_api": True, "has_mcp": False, "provider": "Free Law Project"},
    {"name": "Court API", "slug": "court-api", "category": "court-data", "use_when": "Court records", "url": "https://courtlistener.com", "has_api": True, "has_mcp": False, "provider": "CourtListener"},
    {"name": "ScrapingBee", "slug": "scrapingbee-legal", "category": "court-data", "use_when": "Legal data scraping", "url": "https://scrapingbee.com", "has_api": True, "has_mcp": False, "provider": "ScrapingBee"},
]

# Curated tools from user requests (must be included)
CURATED_TOOLS = [
    {
        "name": "Bloomberg Law Enterprise Dockets API",
        "slug": "bloomberg-law-dockets-api",
        "category": "court-data",
        "use_when": "Federal and state court dockets; litigation alerts; comprehensive docket database",
        "url": "https://pro.bloomberglaw.com/products/court-dockets-search/enterprise-dockets-api-solution/",
        "has_api": True,
        "has_mcp": False,
        "provider": "Bloomberg Law",
    },
    {
        "name": "TrustFoundry AI",
        "slug": "trustfoundry-ai",
        "category": "legal-ai",
        "use_when": "Legal research; AI-powered legal analysis",
        "url": "https://trustfoundry.ai/",
        "has_api": False,
        "has_mcp": False,
        "provider": "TrustFoundry",
    },
    {
        "name": "LegiScan API",
        "slug": "legiscan",
        "category": "legislative",
        "use_when": "State and federal legislation data; bill tracking",
        "url": "https://legiscan.com/legiscan",
        "has_api": True,
        "has_mcp": False,
        "provider": "LegiScan",
    },
    {
        "name": "OpenLaws API",
        "slug": "openlaws-api",
        "category": "legislative",
        "use_when": "Law data for LegalTech and LLMs; structured legal data",
        "url": "https://openlaws.us/api/",
        "has_api": True,
        "has_mcp": False,
        "provider": "OpenLaws",
    },
]


def slugify(name: str) -> str:
    """Convert name to slug for MongoDB."""
    s = re.sub(r"[^\w\s-]", "", name.lower())
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s or "unknown"


def get_openai_legal_apis() -> list[dict]:
    """Use OpenAI to discover legal APIs from dataRade and other sources."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not api_key:
        return []

    try:
        from openai import OpenAI
    except ImportError:
        return []

    client = OpenAI(api_key=api_key)

    prompt = """You are helping build a catalog of legal APIs for law firms.

List 50+ legal APIs and data products that appear on dataRade.ai (datarade.ai/search/products/legal-apis) or are commonly used by law firms.

For each API, provide:
- name: Product/API name
- provider: Company or provider name
- category: One of court-data, legislative, legal-research, legal-ai, e-discovery, practice-management, trademark-ip, compliance
- url: Best URL (datarade product page, vendor docs, or API docs)
- description: One sentence on what it does (optional)

Return a JSON array of objects. Example:
[{"name": "UniCourt Court Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/...", "description": "..."}]

Include: UniCourt, Bloomberg Law, LegiScan, OpenLaws, PACER, court data, legislative, trademark, legal research, e-discovery, and any other legal APIs you know from dataRade or legal tech."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        text = (response.choices[0].message.content or "").strip()

        # Extract JSON array
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            arr = json.loads(text[start:end])
            if isinstance(arr, list):
                return arr
    except Exception as e:
        print(f"OpenAI error: {e}", file=sys.stderr)

    return []


def tool_doc(api: dict, source: str = "datarade") -> dict:
    """Build tool document for MongoDB."""
    name = api.get("name", "Unknown")
    slug = slugify(name)
    return {
        "slug": slug,
        "name": name,
        "category": api.get("category", "legal-api"),
        "provider": api.get("provider", ""),
        "use_when": api.get("description", f"Legal API: {name}"),
        "url": api.get("url", ""),
        "source": source,
        "has_mcp": False,  # Will be updated by weekly sync if MCP found
        "has_api": True,
        "last_synced": datetime.now(timezone.utc).isoformat(),
        "sync_sources": [api.get("url", "https://datarade.ai/search/products/legal-apis")],
    }



def ensure_tool_record(t: dict, *, source: str = "openai-discovery") -> dict:
    """Normalize a tool dict for the legal APIs index."""
    name = t.get("name") or "Unknown"
    return {
        "name": name,
        "slug": t.get("slug") or slugify(t.get("name", "unknown")),
        "category": t.get("category") or "legal-tech",
        "use_when": t.get("use_when") or "",
        "url": t.get("url") or "",
        "has_api": bool(t.get("has_api", False)),
        "has_mcp": bool(t.get("has_mcp", False)),
        "provider": t.get("provider") or "",
        "source": t.get("source") or source,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
    }


def upsert_to_mongodb(tools: list[dict]) -> int:
    """Upsert tools to MongoDB. Returns count upserted."""
    try:
        from libs.db import ensure_indexes, get_tools_collection

        coll = get_tools_collection()
        if coll is None:
            return 0

        ensure_indexes()
        upserted = 0
        for t in tools:
            doc = {
                "slug": t["slug"],
                "name": t["name"],
                "category": t["category"],
                "use_when": t["use_when"],
                "url": t.get("url", ""),
                "has_api": t.get("has_api", False),
                "has_mcp": t.get("has_mcp", False),
                "provider": t.get("provider", ""),
                "last_synced": datetime.now(timezone.utc).isoformat(),
                "source": t.get("source", "crawl-datarade"),
            }
            coll.update_one({"slug": doc["slug"]}, {"$set": doc}, upsert=True)
            upserted += 1
        return upserted
    except Exception as e:
        print(f"MongoDB upsert error: {e}")
        return 0


def main() -> int:
    print("Crawl dataRade legal APIs → legal-apis-index.json")
    print("-" * 50)

    tools: list[dict] = []
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")

    if key:
        try:
            from libs.openai_helpers import discover_legal_tools_full

            discovered = discover_legal_tools_full(target_count=220)
            tools.extend(ensure_tool_record(t) for t in discovered)
            print(f"OpenAI (batched): {len(discovered)} tools")
        except Exception as e:
            print(f"OpenAI batched discovery error: {e}", file=sys.stderr)

        extra = get_openai_legal_apis()
        for api in extra:
            tools.append(
                ensure_tool_record(
                    {
                        "name": api.get("name", "Unknown"),
                        "category": api.get("category", "legal-api"),
                        "url": api.get("url", ""),
                        "provider": api.get("provider", ""),
                        "use_when": api.get("description", ""),
                        "has_api": True,
                        "has_mcp": False,
                    },
                    source="openai-supplemental",
                )
            )
        if extra:
            print(f"OpenAI (supplemental list): {len(extra)} APIs")
    else:
        print("OPENAI_API_KEY not set; using static and curated lists only")

    for c in EXPANDED_STATIC + CURATED_TOOLS:
        tools.append(ensure_tool_record(c, source="static-catalog"))

    for c in CURATED_LEGAL_APIS:
        tools.append(
            ensure_tool_record(
                {
                    "name": c["name"],
                    "category": c.get("category", "legal-api"),
                    "url": c.get("url", ""),
                    "provider": c.get("provider", ""),
                    "use_when": "",
                    "has_api": True,
                    "has_mcp": False,
                },
                source="datarade-curated",
            )
        )

    seen: set[str] = set()
    unique: list[dict] = []
    for t in tools:
        if t["slug"] not in seen:
            seen.add(t["slug"])
            unique.append(t)
    unique.sort(key=lambda x: (x["category"], x["name"].lower()))

    print(f"Total unique tools: {len(unique)}")

    out_path = REPO_ROOT / "docs" / "tools" / "legal-apis-index.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    index = {
        "source": "https://datarade.ai/search/products/legal-apis",
        "discovered_at": now,
        "crawled_at": now,
        "count": len(unique),
        "tools": unique,
        "apis": [
            {
                "name": t["name"],
                "slug": t["slug"],
                "provider": t.get("provider", ""),
                "category": t["category"],
                "use_when": t.get("use_when", ""),
                "url": t.get("url", ""),
                "has_api": t.get("has_api", True),
                "has_mcp": t.get("has_mcp", False),
            }
            for t in unique
        ],
    }
    out_path.write_text(json.dumps(index, indent=2) + "\n")
    print(f"Wrote {out_path}")

    if os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URI"):
        n = upsert_to_mongodb(unique)
        print(f"MongoDB: upserted {n} tools")
    else:
        print("MONGODB_URI not set; skipping MongoDB update")

    return 0


if __name__ == "__main__":
    sys.exit(main())
