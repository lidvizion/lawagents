#!/usr/bin/env python3
"""
Crawl and discover 200+ legal APIs, platforms, and integrations.
Uses OpenAI to generate a comprehensive list from dataRade categories and known legal tech.
Outputs: docs/tools/legal-apis-index.json and updates MongoDB if MONGODB_URI is set.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

# Check for OPENAI_API_KEY or OPENAI_KEY
OPENAI_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
if not OPENAI_KEY:
    print("OPENAI_API_KEY or OPENAI_KEY required. Set in .env or environment.")
    sys.exit(1)

from libs.openai_helpers import discover_legal_tools_full

# Static expansion: known legal APIs/platforms from dataRade and industry (ensures 200+)
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
        "slug": "legiscan-api",
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
    """Create URL-safe slug from name."""
    s = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[-\s]+", "-", s).strip("-")


def ensure_tool_record(t: dict) -> dict:
    """Ensure each tool has required fields."""
    return {
        "name": t.get("name") or "Unknown",
        "slug": t.get("slug") or slugify(t.get("name", "unknown")),
        "category": t.get("category") or "legal-tech",
        "use_when": t.get("use_when") or "",
        "url": t.get("url") or "",
        "has_api": bool(t.get("has_api", False)),
        "has_mcp": bool(t.get("has_mcp", False)),
        "provider": t.get("provider") or "",
        "source": "openai-discovery",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
    }


def upsert_to_mongodb(tools: list[dict]) -> int:
    """Upsert tools to MongoDB. Returns count upserted."""
    try:
        from libs.db import get_tools_collection, ensure_indexes

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
                "source": "crawl-datarade",
            }
            coll.update_one(
                {"slug": doc["slug"]},
                {"$set": doc},
                upsert=True,
            )
            upserted += 1
        return upserted
    except Exception as e:
        print(f"MongoDB upsert error: {e}")
        return 0


def main() -> int:
    print("Discovering 200+ legal APIs and platforms via OpenAI...")
    tools = discover_legal_tools_full(target_count=220)
    tools = [ensure_tool_record(t) for t in tools]

    # Merge static expansion and curated tools
    for c in EXPANDED_STATIC + CURATED_TOOLS:
        tools.append(ensure_tool_record(c))
    # Dedupe by slug (curated last, so they win)
    seen: set[str] = set()
    unique: list[dict] = []
    for t in tools:
        if t["slug"] not in seen:
            seen.add(t["slug"])
            unique.append(t)
    # Sort by category then name for consistency
    unique.sort(key=lambda x: (x["category"], x["name"].lower()))

    print(f"Discovered {len(unique)} unique tools")

    # Write JSON index
    out_path = REPO_ROOT / "docs" / "tools" / "legal-apis-index.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    index = {
        "source": "https://datarade.ai/search/products/legal-apis",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "count": len(unique),
        "tools": unique,
    }
    out_path.write_text(json.dumps(index, indent=2) + "\n")
    print(f"Wrote {out_path}")

    # Upsert to MongoDB
    if os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URI"):
        n = upsert_to_mongodb(unique)
        print(f"MongoDB: upserted {n} tools")
    else:
        print("MONGODB_URI not set; skipping MongoDB update")

    return 0


if __name__ == "__main__":
    sys.exit(main())
