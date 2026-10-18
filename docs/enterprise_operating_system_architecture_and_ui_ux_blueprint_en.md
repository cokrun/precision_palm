# ENTERPRISE SYSTEM OPERATING ARCHITECTURE & UI/UX WORKSPACE BLUEPRINT
# Precision Palm Cloud OS — Tropical Biophysical Agroforestry & Statutory Compliance
# Industry Reference Standards: Google Cloud Console Workspace • Multi-Tenancy • ISO 19115 • EUDR Reg. 2023/1115 • ISPO Permentan 33/2025

================================================================================
SECTION 0: GLOBAL TOP BAR & SYSTEM-WIDE PERSISTENT CONTEXT
================================================================================
Design Principle: Inspired by the Google Cloud Platform Console Top Bar. Regardless 
of which functional module the user navigates to, the global system identity, 
active corporate entity (dossier), audit progression year, and cryptographic 
integrity state remain persistently visible and accessible.

[ TOP PERSISTENT CONTEXT BAR (GLOBAL STICKY HEADER) ]
├── 1. Brand & Operating System Identity:
│      └── "🌴 Precision Palm Enterprise OS • Biophysical & Statutory Intelligence"
│
├── 2. Corporate Concession Selector (Multi-Tenant Scoping Anchor):
│      └── [🏢 Active Concession: PT Mandailing Agro Sustainable (EST-MDN-001) ▾]
│          ├── EST-MDN-001 • PT Mandailing Agro Sustainable (North Sumatra) [Active / Certified]
│          ├── EST-RIAU-002 • Koperasi Sawit Makmur Bersama (Riau) [Onboarding / Empty State]
│          ├── EST-KALTENG-003 • PT Kahayan Agro Mandiri (Central Kalimantan) [In Verification]
│          └── [+ Register New Corporate Dossier / Concession Onboarding]
│
├── 3. Statutory Audit Year Selector (Year Temporal Anchor):
│      └── [📅 Audit Fiscal Year: 2026 (Active EUDR Audit Cycle) ▾]
│          ├── 2026 (Active Statutory Audit & European Union Export Cycle)
│          ├── 2027 (Long-Term In-Silico LER & Biomass Growth Projection)
│          └── 2025 (Historical Cut-Off Baseline & Retrospective Dossier Archive)
│
├── 4. Market Jurisdiction & Pricing Currency Toggle:
│      └── [🌐 Market Context: 🇮🇩 Domestic IDR (Permentan Index-K) | 🌐 International USD (CIF Rotterdam / EUDR)]
│
├── 5. User Persona Display Toggle (Cognitive Mode Switcher):
│      └── [👁️ Executive Plain Mode (Smallholders / Regulators) | 🔬 Full Diagnostic Mode (Auditors / GIS Engineers)]
│
└── 6. Cryptographic State & Cloud KMS Hardware Seal:
       └── [🔒 FIPS 180-4 SHA-256 Valid • Storage Engine: Dual-Write SQLite WAL + Google BigQuery DW]

================================================================================
SECTION 1: ENTERPRISE FILE & MODULE NOMENCLATURE TRANSFORMATION
================================================================================
Design Principle: Retiring prototype/consumer-tier names (e.g., "simulator", "timelines", 
"roadmap") and adopting official enterprise nomenclature aligned with regulatory 
jurisdictions, planetary remote sensing, and biophysical engineering.

--------------------------------------------------------------------------------
1.1 Template Files Mapping (/templates)
--------------------------------------------------------------------------------
• Legacy Name       : templates/index.html
  Enterprise Name   : templates/executive_overview.html
  Route URL         : /
  Functional Domain : Executive Vision, Cohort ESG KPIs, Macro Devisa & Landscape

• Legacy Name       : templates/pendaftaran.html
  Enterprise Name   : templates/concession_master_register.html
  Route URL         : /concession-register
  Functional Domain : Master Concession Directory with Max-10 Row Pagination & Search

• Legacy Name       : templates/permohonan.html
  Enterprise Name   : templates/cadastral_onboarding.html
  Route URL         : /cadastral-onboarding
  Functional Domain : Stage 1: Agrarian Land Deed Ingestion (HGU/e-STDB) & WGS84 Geodesy

• Legacy Name       : templates/spatial.html
  Enterprise Name   : templates/planetary_observatory.html
  Route URL         : /planetary-observatory
  Functional Domain : Stage 2A: Google Earth Engine Satellite Telemetry & Moratorium Buffers

• Legacy Name       : templates/simulator.html
  Enterprise Name   : templates/in_silico_engine.html
  Route URL         : /in-silico
  Functional Domain : Stage 2B: Monsi-Saeki Solar Attenuation, LER & Commodity TBS Engine

• Legacy Name       : templates/timelines.html
  Enterprise Name   : templates/quarterly_surveillance.html
  Route URL         : /quarterly-surveillance
  Functional Domain : Stage 3: Multi-Evidence Edge Monitoring (Q1–Q4) & 180-Day SLA Machine

• Legacy Name       : templates/roadmap.html
  Enterprise Name   : templates/statutory_ratification.html
  Route URL         : /statutory-ratification
  Functional Domain : Stage 4: Assessor Council Hearing, All-Report Docket & EUDR DDS JSON

• Legacy Name       : templates/topologi.html
  Enterprise Name   : templates/compliance_lineage_dag.html
  Route URL         : /compliance-lineage
  Functional Domain : 12-Node Directed Acyclic Graph (DAG) & Attributed Legal Reasoning

• Legacy Name       : templates/pengaturan.html
  Enterprise Name   : templates/system_control_center.html
  Route URL         : /system-control
  Functional Domain : Multi-Tenancy Scoping, Commodity Indexing, & Anti-Fraud Registry

--------------------------------------------------------------------------------
1.2 JavaScript Client Controllers (/static/js)
--------------------------------------------------------------------------------
• spatial.js       ──> planetary_observatory.js   (Leaflet GIS & GEE Satellite Pipelines)
• simulator.js     ──> in_silico_engine.js        (LER Math & Real-Time Price Simulation)
• timelines.js     ──> quarterly_surveillance.js  (Unified Evidence Gallery & Gemini 3.8 HUD)
• roadmap.js       ──> statutory_ratification.js  (All-Report Ingestion & Cloud KMS Digest)
• app_workspace.js [NEW]                          (Sidebar Collapse, Year Context & Tenancy)

--------------------------------------------------------------------------------
1.3 Backend Dual-Routing & Backward Compatibility (app.py)
--------------------------------------------------------------------------------
To guarantee that existing bookmarks, QR codes, and automated test suites never 
break with HTTP 404 errors, app.py enforces strict 301 Permanent Redirects:
• /spatial   ──[301 Redirect]──> /planetary-observatory
• /proses    ──[301 Redirect]──> /in-silico
• /timelines ──[301 Redirect]──> /quarterly-surveillance
• /roadmap   ──[301 Redirect]──> /statutory-ratification
• /topologi  ──[301 Redirect]──> /compliance-lineage

================================================================================
SECTION 2: COLLAPSIBLE ENTERPRISE SIDEBAR ARCHITECTURE (GCP CONSOLE STYLE)
================================================================================
Design Principle: A fixed left sidebar (width: 240px) that can be collapsed into a 
compact icon-only strip (width: 64px) at the click of a button, freeing up 100% 
horizontal canvas space for GIS maps, satellite spectral layers, and high-density 
evidence grids.

[ LEFT COLLAPSIBLE NAVIGATION SIDEBAR ]
│
├── 🏠 1. EXECUTIVE DASHBOARD (/ or /executive-overview)
│      Macro macroeconomic KPIs, national carbon abatement tally, and export readiness.
│
├── 📑 2. CADASTRAL & TENURIAL ADMINISTRATION (Stage 1)
│      ├── 2.1 Concession Master Register (/concession-register) [Strict Max-10 Pagination]
│      └── 2.2 Cadastral Onboarding (/cadastral-onboarding) [Document AI Deed Parser & WGS84]
│
├── 🛰️ 3. PLANETARY REMOTE SENSING OBSERVATORY (Stage 2A) (/planetary-observatory)
│      ├── High-Resolution Satellite Basemaps & SRTM 30m Micro-Slope DEM (<= 15°)
│      ├── Hansen Global Forest Change Post-2020 Zero-Deforestation Audit (0.00 Ha)
│      ├── Primary Forest Moratorium (PIPPIB) & Hydrological Riparian Buffers (> 50m)
│      └── Nadir Aerial Drone Orthomosaic Gallery (45m AGL Optical Ingestion)
│
├── 🧪 4. IN-SILICO BIOPHYSICAL ENGINE (Stage 2B) (/in-silico)
│      Architected into 3 Clean Sub-View Tabs:
│      ├── [Tab A] 🌿 Agronomic Intercropping & 2.0m Sterile Root Zoning
│      ├── [Tab B] 💰 Real Commodity Pricing & TBS Revenue Optimization (rumus_tb.py)
│      └── [Tab C] 🛡️ Land Sparing Efficiency (LER > 1.40x) & Verra Carbon Accounting
│      └── [Collapsible Deep Accordion] 📊 10-Year In-Silico Financial Cashflow
│
├── 📷 5. QUARTERLY SURVEILLANCE & EDGE MONITORING (Stage 3) (/quarterly-surveillance)
│      ├── 4-Quarter Lifecycle Tracking (Q1: Planting, Q2: Care, Q3: Vigor, Q4: Harvest)
│      ├── Unified Multi-Evidence Gallery (Coupled Drone Aerials + Terrestrial Foremen)
│      ├── Multimodal Gemini 3.8 Flash Spatial Reticle AI (2.0m Weed-Free Buffer HUD)
│      └── 180-Day SLA Dynamic State Machine (Automated Freeze Engine on Day 181)
│
├── ⚖️ 6. STATUTORY RATIFICATION & EXPORT PASSPORT (Stage 4) (/statutory-ratification)
│      ├── Consolidated All-Report Master Dossier (4-Stage Unified Evidence File)
│      ├── Assessor Council Qualitative Deliberation Hearing & Statutory Ratification
│      ├── European Commission EUDR TRACES-NT Due Diligence Statement (DDS JSON)
│      └── Statutory Green Palm Export Certificate with Hardware Cloud KMS SHA-256 Seal
│
├── 🧬 7. STATUTORY COMPLIANCE LINEAGE DAG (/compliance-lineage)
│      12-Node Directed Acyclic Graph (FamilyTree) showing end-to-end data provenance.
│
├── 📚 8. RESEARCH MANUSCRIPTS & SCIENTIFIC SPECIFICATIONS
│      ├── Peer-Reviewed Academic Manuscript (IEEE / Scopus IMRaD Format)
│      ├── National Accredited Scientific Journal (SINTA-1 / Dikti Format)
│      ├── Directorate General of Intellectual Property (DJKI) Patent Specification
│      └── Role-Based Standard Operating Procedure (SOP) Manual
│
└── ⚙️ 9. SYSTEM CONTROL CENTER & GOVERNANCE (/system-control)
       Multi-Tenancy isolation, live international CPO indexing, and binary photo registry.

================================================================================
SECTION 3: IN-SILICO ENGINE (/in-silico) MODULAR SUB-VIEW DESIGN
================================================================================
Design Principle: Eliminating the exhausting "vertical wall of stats." The In-Silico 
Engine is compartmentalized into 3 focused, single-screen tabs, with heavy mathematical 
and financial details tucked into interactive collapsible accordions.

--------------------------------------------------------------------------------
SUB-VIEW TAB A: 🌿 AGRONOMIC INTERCROPPING & ROOT PROTECTION (AGRONOMY FOCUS)
Target Users: Estate Foremen, Field Managers, Agricultural Extension Officers
--------------------------------------------------------------------------------
• Primary Screen (Zero-Scroll Viewport):
  1. Definitive Recommended Intercrop Card:
     - Botanical Taxon: Red Ginger (Zingiber officinale var. rubrum)
     - Suitability Rating: 98.4% (Optimal for 35.8% Sub-Canopy PAR Irradiance)
     - Spatial Dimension: 3.79 Meter Net Cultivated Alleyway
  2. Spatial Corridor Anatomy Cross-Section Diagram:
     - Palm Stem Left [2.0m Sterile Circle] ── 3.79m Active Bed ── [2.0m Sterile Circle] Palm Stem Right
  3. Basal Stem Rot (Ganoderma boninense) Hazard Index:
     - Root Trauma Risk: 0.0% (Enforced Zero-Tillage in Quaternary Feeder-Root Radius).

• Interactive Collapsible Accordions (Expanded on Demand):
  ▼ [▶ Expand] Monsi-Saeki Solar Physics: I = I₀ · exp(-k · LAI) with k=0.45 & Sigmoid Kinetics
  ▼ [▶ Expand] Stoichiometric Mineral Replenishment: Compensatory MOP (+75 kg/Ha) & Mulch Loop

--------------------------------------------------------------------------------
SUB-VIEW TAB B: 💰 REAL COMMODITY PRICING & TBS REVENUE (COMMODITY BUSINESS FOCUS)
Target Users: Plantation Owners, Smallholder Cooperative Chairs, Ministry Directors
--------------------------------------------------------------------------------
• Primary Screen (Zero-Scroll Viewport):
  1. Cash Revenue Multiplier Comparison Card (Money-First Metric):
     - Conventional Monoculture Palm Baseline : IDR  92,557,982 / Ha / Year
     - Engineered Precision Agroforestry      : IDR 321,245,482 / Ha / Year
     - NET SMALLHOLDER MARGIN UPLIFT          : +IDR 228,687,500 / Ha / Year (+247.1%)
  2. Real-Time TBS Pricing Calculator (rumus_tb.py Live Implementation):
     - CIF Rotterdam CPO Index: USD 1,526.56 / MT | Bank Indonesia Exchange Rate: IDR 17,920
     - Net Domestic Mill Gate CPO Price: IDR 20,935.25 / kg
     - Statutory TBS Farmgate Price (Index-K 91%): IDR 3,824.71 / kg (IDR 3,824,710 / Ton)

• Interactive Collapsible Accordions (Expanded on Demand):
  ▼ [▶ Expand] Mill Efficiency Parameters (CPO Extraction 21%, Kernel 5%, Processing Fee IDR 300)
  ▼ [▶ Expand] 10-Year In-Silico Financial Cashflow & Natural Capital Asset Valuation Table

--------------------------------------------------------------------------------
SUB-VIEW TAB C: 🛡️ STATUTORY COMPLIANCE, LER & CARBON (AUDIT & ESG FOCUS)
Target Users: ISPO / EUDR Accreditation Auditors, Environmental Assessors, Carbon Brokers
--------------------------------------------------------------------------------
• Primary Screen (Zero-Scroll Viewport):
  1. Dual-Yield Land Sparing Efficiency:
     - Land Equivalent Ratio (LER): 1.48x (+48% Biological Spatial Superiority)
     - Percentage Land Saved (PLS): 31.25%
     - Spared Lowland Tropical Rainforest: 576.00 Hectares Equivalent
  2. Main Crop bunch Deficit Regulatory Cap:
     - Measured Oil Palm FFB Deficit: 1.22% (Fully Compliant under the Statutory <= 4.5% Cap)
  3. High-Integrity Carbon Asset (Verra VCS VM0007 / IPCC Tier 3 AFOLU):
     - Verified Climate Abatement: 259,200 tCO₂e (Valued at USD 3.11M at $12/tCO₂e)

• Interactive Collapsible Accordions (Expanded on Demand):
  ▼ [▶ Expand] Statutory Law Attributions (MoA Reg. 33/2025, EUDR Reg. 2023/1115, Gov. Reg. 23/2021)
  ▼ [▶ Expand] Cryptographic FIPS 180-4 SHA-256 Ledger Audit Seals

================================================================================
SECTION 4: UNIFIED CROSS-PROCESS EVIDENCE REPOSITORY ARCHITECTURE
================================================================================
Design Principle: Complete elimination of decoupled or orphaned media files. Every 
drone orthomosaic, satellite clipping, and foreman field snapshot is strictly bound 
to the active dossier_id and stored in real binary format.

1. UNIFIED MULTI-EVIDENCE GALLERY:
   • Aggregated Ingestion Sources:
     - Aerial Nadir Drone Sensor (45m AGL captured under /planetary-observatory).
     - Terrestrial In-Situ Mobile Foremen (Hardware camera geolocated under /mobile).
   • Viewport Execution Rules:
     - Left gallery shows verified thumbnails scoped to the active concession.
     - Clicking any thumbnail streams the uncompressed JPEG via `/api/media/evidence/<id>`.
     - Multimodal Gemini 3.8 Flash reticles ONLY render if an image is loaded on canvas.
     - If no evidence exists, display a clean Empty State banner with zero floating boxes.

2. CONSOLIDATED ALL-REPORT MASTER DOSSIER:
   • Unified Deliverables Packaging:
     - Exhibit 1: Validated Agrarian Title Deed Certificate & Municipal NOP Record (Stage 1).
     - Exhibit 2: GEE Moratorium & Zero-Deforestation Clearance Certificate (Stage 2A).
     - Exhibit 3: In-Silico LER Biophysical Recommendation & Fertilizer Formulation (Stage 2B).
     - Exhibit 4: 4-Quarter In-Situ Photographic Surveillance Telemetry Dossier (Stage 3).
   • Ratification Deliverable:
     - Certified Master Dossier locked with SHA-256 hash and issued with an EUDR TRACES-NT DDS JSON file.

================================================================================
SECTION 5: SUMMARY OF SPECIFICATIONS FOR AG IMPLEMENTATION
================================================================================
When implementing this architectural upgrade:
1. Preserve all existing mathematical models, BigQuery sync pipelines, and database constraints.
2. Restructure top navigation into the Google Cloud style Persistent Context Bar.
3. Implement the Left Collapsible Sidebar with standard 240px to 64px toggle animation.
4. Split `/in-silico` into the 3 Sub-View Tabs (Agronomy, Business, and Compliance).
5. Wrap the 10-Year Cashflow Table and complex equations in interactive `<details>` / accordion blocks.
6. Enforce strict 301 Permanent Redirects on all legacy routes (/spatial, /proses, /timelines, /roadmap, /topologi).
```eof

Key Architectural Strengths of This English Blueprint:

    Jury & Auditor-Grade Credibility:

        Changing /simulator to /in-silico (In-Silico Biophysical Engine) removes any perception of a toy or mock app.

        Changing /timelines to /quarterly-surveillance (Quarterly Surveillance & Edge Monitoring) directly reflects compliance and forestry operations.

        Changing /roadmap to /statutory-ratification (Statutory Ratification & Export Passport) positions the module as an authoritative customs clearance gateway.

        Changing /topologi to /compliance-lineage (Statutory Compliance Lineage DAG) makes its purpose crystal clear to lawyers, customs officials, and software architects alike.

    Zero Information Loss:

        Not a single equation, calculation, or dataset is eliminated.

        Heavy sections (like the 10-Year In-Silico Financial Cashflow Table and Monsi-Saeki derivation) are neatly packaged into interactive collapsible accordions.

    Smooth, Non-Breaking Transition:

        All legacy route URLs (/spatial, /proses, /timelines, /roadmap, /topologi) are preserved via HTTP 301 redirects, ensuring no broken links occur.