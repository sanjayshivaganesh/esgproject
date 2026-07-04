#!/usr/bin/env python3
"""
Memory profiling script for ESG analysis backend.
Run this to capture baseline memory usage before optimizations.
"""

import sys
sys.path.insert(0, '/Users/sanjay_shiva/Downloads/ESG/backend')

from rule_engine import analyze_text, DEBUG_MEMORY

# Ensure memory profiling is enabled
import rule_engine
rule_engine.DEBUG_MEMORY = True

# Sample text for testing (replace with actual 90-page report content)
# For accurate baseline, use the actual 20 MB ESG report that causes the issue
sample_text = """
We are committed to reducing our carbon footprint by 50% by 2030. 
Our emissions have decreased by 20% since 2020 due to renewable energy investments.
We aim to achieve net-zero emissions by 2050.
Our water usage has been optimized through recycling initiatives.
We have reduced waste by 30% through circular economy practices.
""" * 100  # Repeat to simulate longer document

print("=" * 60)
print("MEMORY PROFILING - BASELINE")
print("=" * 60)
print(f"DEBUG_MEMORY enabled: {DEBUG_MEMORY}")
print(f"Sample text length: {len(sample_text)} characters")
print("=" * 60)
print()

# Run analysis
result = analyze_text(sample_text)

print()
print("=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
print(f"Greenwashing risk: {result.get('risk', 'N/A')}")
print(f"Support ratio: {result.get('support_ratio', 'N/A')}")
print(f"Claim pressure: {result.get('claim_pressure', 'N/A')}")
print(f"Outcome evidence score: {result.get('outcome_evidence_score', 'N/A')}")
print("=" * 60)
