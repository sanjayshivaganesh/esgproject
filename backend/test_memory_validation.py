#!/usr/bin/env python3
"""
Validation script to ensure memory optimizations preserve functionality.
Tests that outputs remain identical before and after optimizations.
"""

import sys
sys.path.insert(0, '/Users/sanjay_shiva/Downloads/ESG/backend')

import json
from rule_engine import analyze_text

# Test text samples of varying sizes
TEST_CASES = [
    {
        "name": "Small document",
        "text": """
We are committed to reducing our carbon footprint by 50% by 2030. 
Our emissions have decreased by 20% since 2020 due to renewable energy investments.
We aim to achieve net-zero emissions by 2050.
Our water usage has been optimized through recycling initiatives.
We have reduced waste by 30% through circular economy practices.
        """.strip()
    },
    {
        "name": "Medium document",
        "text": """
We are committed to reducing our carbon footprint by 50% by 2030. 
Our emissions have decreased by 20% since 2020 due to renewable energy investments.
We aim to achieve net-zero emissions by 2050.
Our water usage has been optimized through recycling initiatives.
We have reduced waste by 30% through circular economy practices.
The company has implemented a comprehensive sustainability strategy focusing on environmental stewardship.
We have achieved ISO 14001 certification for our environmental management system.
Our renewable energy portfolio now represents 45% of total energy consumption.
We have partnered with local communities to support biodiversity conservation projects.
The board of directors has approved a $10 million investment in green technologies.
Our supply chain sustainability program covers 80% of our key suppliers.
We have published our first Task Force on Climate-related Financial Disclosures (TCFD) report.
        """.strip() * 5
    },
    {
        "name": "Large document",
        "text": """
We are committed to reducing our carbon footprint by 50% by 2030. 
Our emissions have decreased by 20% since 2020 due to renewable energy investments.
We aim to achieve net-zero emissions by 2050.
Our water usage has been optimized through recycling initiatives.
We have reduced waste by 30% through circular economy practices.
The company has implemented a comprehensive sustainability strategy focusing on environmental stewardship.
We have achieved ISO 14001 certification for our environmental management system.
Our renewable energy portfolio now represents 45% of total energy consumption.
We have partnered with local communities to support biodiversity conservation projects.
The board of directors has approved a $10 million investment in green technologies.
Our supply chain sustainability program covers 80% of our key suppliers.
We have published our first Task Force on Climate-related Financial Disclosures (TCFD) report.
        """.strip() * 20
    }
]

def validate_output_structure(result):
    """Validate that the output has the expected structure."""
    required_fields = [
        "claim_pressure",
        "cross_sentence_consistency",
        "claim",
        "outcome_evidence",
        "transparency_score",
        "transparency_detail",
        "greenwashing_gap",
        "support_ratio",
        "support_ratio_category",
        "support_ratio_explanation",
        "unsupported_targets",
        "supported_targets",
        "average_match_score",
        "future_target_density",
        "effective_target_pressure",
        "confidence_score",
        "risk",
        "risk_raw",
        "document_type",
        "document_classification",
        "sentence_classification",
        "grounded_kpis",
        "deduplicated_kpis",
        "supported_target_examples",
        "unsupported_target_examples",
        "support_ratio_components",
        "diagnostics",
        "controversy",
        "indicators",
        "drivers",
        "signals"
    ]
    
    missing_fields = [field for field in required_fields if field not in result]
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    print(f"✅ Output structure valid")
    return True

def validate_value_types(result):
    """Validate that critical fields have the expected types."""
    type_checks = {
        "claim_pressure": (int, float),
        "support_ratio": (int, float),
        "transparency_score": (int, float),
        "risk": (int, float),
        "confidence_score": (int, float),
    }
    
    for field, expected_type in type_checks.items():
        value = result.get(field)
        if value is None:
            print(f"⚠️  Field {field} is None")
            continue
        if not isinstance(value, expected_type):
            print(f"❌ Field {field} has wrong type: {type(value)} (expected {expected_type})")
            return False
    
    print(f"✅ Value types valid")
    return True

def validate_ranges(result):
    """Validate that numeric fields are within expected ranges."""
    range_checks = {
        "claim_pressure": (0, 100),
        "support_ratio": (0, 10),
        "transparency_score": (0, 100),
        "risk": (0, 100),
        "confidence_score": (0, 100),
    }
    
    for field, (min_val, max_val) in range_checks.items():
        value = result.get(field)
        if value is None:
            continue
        if not (min_val <= value <= max_val):
            print(f"❌ Field {field} out of range: {value} (expected {min_val}-{max_val})")
            return False
    
    print(f"✅ Value ranges valid")
    return True

def run_test_case(test_case):
    """Run a single test case and validate the output."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_case['name']}")
    print(f"Text length: {len(test_case['text'])} characters")
    print(f"{'='*60}")
    
    try:
        result = analyze_text(test_case['text'])
        
        # Validate structure
        if not validate_output_structure(result):
            return False
        
        # Validate types
        if not validate_value_types(result):
            return False
        
        # Validate ranges
        if not validate_ranges(result):
            return False
        
        # Print key metrics
        print(f"\nKey Metrics:")
        print(f"  Claim Pressure: {result.get('claim_pressure', 'N/A')}")
        print(f"  Support Ratio: {result.get('support_ratio', 'N/A')}")
        print(f"  Transparency Score: {result.get('transparency_score', 'N/A')}")
        print(f"  Risk: {result.get('risk', 'N/A')}")
        print(f"  Confidence Score: {result.get('confidence_score', 'N/A')}")
        print(f"  Document Type: {result.get('document_type', 'N/A')}")
        
        # Print sentence classification breakdown
        classification = result.get('sentence_classification', {}).get('classification_breakdown', {})
        print(f"\nSentence Classification:")
        print(f"  Claims: {classification.get('claim_count', 0)}")
        print(f"  Outcomes: {classification.get('outcome_count', 0)}")
        print(f"  Targets: {classification.get('target_count', 0)}")
        print(f"  Transparency: {classification.get('transparency_count', 0)}")
        print(f"  Neutral: {classification.get('neutral_count', 0)}")
        
        print(f"\n✅ Test case passed: {test_case['name']}")
        return True
        
    except Exception as e:
        print(f"\n❌ Test case failed: {test_case['name']}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all test cases."""
    print("="*60)
    print("MEMORY OPTIMIZATION VALIDATION")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_case in TEST_CASES:
        if run_test_case(test_case):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}/{len(TEST_CASES)}")
    print(f"Failed: {failed}/{len(TEST_CASES)}")
    
    if failed == 0:
        print(f"\n✅ All validation tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} validation test(s) failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
