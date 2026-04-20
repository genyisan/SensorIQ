# SensorIQ
AI-powered dental imaging quality assistant that recommends optimal sensor image settings for clear, diagnostically superior X-rays.

## Overview

A specialized AI assistant designed to calibrate dental sensor image quality across multiple imaging softwares and X-ray sources.

## Features
Baseline Injection: Automatically provides verified baseline settings for specific software/machine combos.

AI Refinement: Uses Claude to troubleshoot visual artifacts (grain, contrast, etc.).

Data Logging: Connects to Google Sheets to build a master iq_settings database.

Notion Integration: Centralized feedback loop for the tech team.

## Setup & Installation
Since this is a Streamlit app you need to add your AI Key and Google API key in Secrets.

Secrets: You must have a .streamlit/secrets.toml file or Streamlit Cloud Secrets configured with:

CLAUDE_KEY

CONNECTIONS.gsheets (Google Service Account credentials)

*Knowledge Base: Ensure knowledge/settings_guide.txt and iq_settings.csv are in the root directory.

## Data Structure
CSV/Google Sheet is mapping:

machine: Wall-mounted vs Hand-held.

software: The imaging platform (Vixwin, Dexis, etc.).

issue: Standardized tags (dark xray, grainy, etc.).

settings: The formatted string for the software filters.

## ⚠️ Disclaimer
"This tool provides recommendations based on AI analysis. Always verify diagnostic quality with the clinician before finalizing settings."
