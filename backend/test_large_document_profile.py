#!/usr/bin/env python3
"""
Memory profiling script for large documents.
Simulates a 90-page ESG report to identify peak memory usage.
"""

import os
import sys

# Enable memory profiling BEFORE importing rule_engine
os.environ["ESG_DEBUG_MEMORY"] = "true"
print(f"ESG_DEBUG_MEMORY set to: {os.environ.get('ESG_DEBUG_MEMORY')}")

sys.path.insert(0, '/Users/sanjay_shiva/Downloads/ESG/backend')

from rule_engine import analyze_text

# Generate a synthetic large document simulating a 90-page ESG report
# Typical ESG report: ~200-300 sentences per page
# 90 pages * 250 sentences = ~22,500 sentences
# Each sentence: ~15-20 words
# Total: ~300,000-450,000 words

def generate_large_document(pages=90, sentences_per_page=250):
    """Generate a synthetic ESG report for testing with unique sentences."""
    
    import random
    random.seed(42)
    
    # ESG-related sentence templates with more variety
    claim_templates = [
        "We are committed to reducing our carbon footprint by {percent}% by {year}.",
        "Our company aims to achieve net-zero emissions by {year}.",
        "We have set ambitious targets for reducing greenhouse gas emissions.",
        "We are dedicated to sustainable development and environmental stewardship.",
        "Our sustainability strategy focuses on long-term value creation.",
        "We prioritize renewable energy investments to combat climate change.",
        "We are working towards a circular economy model.",
        "Our environmental initiatives demonstrate our commitment to the planet.",
        "We have implemented comprehensive ESG policies across our operations.",
        "We are leading the industry in sustainable business practices.",
        "Our organization pledges to minimize environmental impact through innovation.",
        "We recognize the urgency of addressing climate change.",
        "We integrate sustainability into our core business strategy.",
        "We believe in creating shared value for all stakeholders.",
        "Our commitment to ESG is unwavering and transparent.",
        "We strive to exceed industry standards for environmental performance.",
        "We are transforming our operations to be more sustainable.",
        "We embrace our responsibility to protect the environment.",
        "Our ESG commitments are backed by concrete actions.",
        "We are accelerating our transition to a low-carbon economy.",
    ]
    
    outcome_templates = [
        "Our emissions have decreased by {percent}% since {year} due to renewable energy investments.",
        "We have achieved a {percent}% reduction in water consumption through efficiency measures.",
        "Our waste diversion rate has improved to {percent}% through recycling programs.",
        "Renewable energy now represents {percent}% of our total energy consumption.",
        "We have reduced our Scope 1 emissions by {percent}% over the past year.",
        "Our energy efficiency initiatives have saved {percent}% in operational costs.",
        "We have planted {number} trees as part of our reforestation commitment.",
        "Our carbon offset program has neutralized {percent}% of our emissions.",
        "We have achieved ISO 14001 certification for environmental management.",
        "Our supply chain sustainability program covers {percent}% of key suppliers.",
        "We successfully reduced our energy intensity by {percent}% last year.",
        "Our water recycling efforts saved {number} million gallons of water.",
        "We diverted {percent}% of waste from landfills through circular economy practices.",
        "Our renewable energy capacity increased by {percent}% this quarter.",
        "We achieved a {percent}% reduction in single-use plastics across operations.",
        "Our carbon footprint decreased by {percent}% compared to the baseline year.",
        "We implemented energy-efficient technologies that saved {number} kWh.",
        "Our sustainable sourcing program reached {percent}% of materials procured.",
        "We reduced our fleet emissions by {percent}% through electric vehicle adoption.",
        "Our employee sustainability training completion rate reached {percent}%.",
    ]
    
    target_templates = [
        "We pledge to reduce carbon emissions by {percent}% by {year}.",
        "Our target is to achieve {percent}% renewable energy by {year}.",
        "We aim to reduce water usage by {percent}% by {year}.",
        "We commit to zero waste to landfill by {year}.",
        "We plan to invest ${amount} million in green technologies by {year}.",
        "Our goal is to reduce Scope 3 emissions by {percent}% by {year}.",
        "We target {percent}% female representation in leadership by {year}.",
        "We aim to achieve {percent}% employee satisfaction by {year}.",
        "We commit to sourcing {percent}% materials from sustainable sources by {year}.",
        "Our target is to reduce energy intensity by {percent}% by {year}.",
        "We have set a goal to reach net-zero emissions by {year}.",
        "Our water reduction target is {percent}% by {year}.",
        "We aim to eliminate single-use plastics by {year}.",
        "Our renewable energy target is {percent}% by {year}.",
        "We target {percent}% waste diversion rate by {year}.",
        "We commit to reducing Scope 2 emissions by {percent}% by {year}.",
        "Our target is to achieve {percent}% sustainable packaging by {year}.",
        "We aim for {percent}% supplier ESG compliance by {year}.",
        "We target {percent}% reduction in paper usage by {year}.",
        "Our goal is to reach {percent}% carbon neutrality by {year}.",
    ]
    
    transparency_templates = [
        "We publish our sustainability report annually.",
        "Our ESG metrics are audited by third-party verifiers.",
        "We disclose our Scope 1, 2, and 3 emissions in accordance with TCFD.",
        "We have established a sustainability committee at the board level.",
        "Our ESG performance is linked to executive compensation.",
        "We engage with stakeholders on a regular basis.",
        "We participate in the CDP climate change survey.",
        "We report our sustainability progress using GRI standards.",
        "We have implemented a whistleblower policy for ESG concerns.",
        "Our sustainability data is available on our website.",
        "We disclose our climate-related risks and opportunities.",
        "Our sustainability report follows SASB standards.",
        "We provide detailed ESG disclosures to investors.",
        "We conduct regular stakeholder engagement sessions.",
        "Our ESG governance structure is clearly defined.",
        "We report our progress against the UN Sustainable Development Goals.",
        "We maintain transparency in our ESG reporting practices.",
        "Our sustainability data is verified by independent auditors.",
        "We disclose our ESG methodology and assumptions.",
        "We provide regular updates on our sustainability initiatives.",
    ]
    
    neutral_templates = [
        "The company operates in multiple geographic regions.",
        "Our business model focuses on long-term growth.",
        "We have a diverse portfolio of products and services.",
        "Our operations span various industry sectors.",
        "We maintain strong relationships with our customers.",
        "Our workforce is distributed across multiple locations.",
        "We invest in research and development activities.",
        "We have a robust risk management framework.",
        "Our financial performance has been stable.",
        "We continue to explore new market opportunities.",
        "The company was founded in {year}.",
        "We serve customers in {number} countries worldwide.",
        "Our headquarters is located in {city}.",
        "We employ over {number} people globally.",
        "Our revenue for the fiscal year was ${amount} billion.",
        "We have been in business for over {number} years.",
        "Our company is listed on the stock exchange.",
        "We operate in the {industry} sector.",
        "Our market capitalization is ${amount} billion.",
        "We have a strong presence in the {region} market.",
    ]
    
    # Create a larger pool of unique templates
    all_templates = [
        claim_templates * 5,
        outcome_templates * 4,
        target_templates * 4,
        transparency_templates * 3,
        neutral_templates * 4,
    ]
    
    # Flatten and shuffle to ensure variety
    all_sentences = []
    for template_group in all_templates:
        all_sentences.extend(template_group)
    
    # Shuffle to avoid patterns
    random.shuffle(all_sentences)
    
    document = []
    for page in range(pages):
        page_sentences = []
        for i in range(sentences_per_page):
            # Use different templates for each sentence to avoid duplicates
            template_index = (page * sentences_per_page + i) % len(all_sentences)
            template = all_sentences[template_index]
            
            # Add unique identifiers to ensure no duplicates
            unique_id = page * sentences_per_page + i
            
            # Fill in placeholders with realistic values
            sentence = template.format(
                percent=str(10 + (unique_id % 90)),
                year=str(2025 + (unique_id % 10)),
                amount=str(10 + (unique_id % 100)),
                number=str(1000 + (unique_id * 100)),
                city=["New York", "London", "Tokyo", "Singapore", "Berlin"][unique_id % 5],
                industry=["technology", "manufacturing", "finance", "healthcare", "energy"][unique_id % 5],
                region=["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"][unique_id % 5]
            )
            
            # Add a unique suffix to ensure no duplicates
            sentence = f"{sentence} (Section {page + 1}.{i + 1})"
            page_sentences.append(sentence)
        
        # Join sentences with periods and newlines
        page_text = ". ".join(page_sentences) + "."
        document.append(page_text)
    
    # Join pages with double newlines
    full_text = "\n\n".join(document)
    
    return full_text

def main():
    print("="*80)
    print("LARGE DOCUMENT MEMORY PROFILING")
    print("="*80)
    
    # Generate large document (90 pages, ~22,500 sentences)
    print("\nGenerating large document (90 pages, ~22,500 sentences)...")
    large_text = generate_large_document(pages=90, sentences_per_page=250)
    print(f"Document generated: {len(large_text):,} characters")
    print(f"Estimated sentences: ~{len(large_text) // 80:,}")
    
    print("\n" + "="*80)
    print("RUNNING ANALYSIS WITH MEMORY PROFILING")
    print("="*80)
    print("\n[MEMORY] Profiling enabled - watching for RSS > 400 MB\n")
    
    try:
        result = analyze_text(large_text)
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        
        print(f"\nKey Results:")
        print(f"  Claim Pressure: {result.get('claim_pressure', 'N/A')}")
        print(f"  Support Ratio: {result.get('support_ratio', 'N/A')}")
        print(f"  Transparency Score: {result.get('transparency_score', 'N/A')}")
        print(f"  Risk: {result.get('risk', 'N/A')}")
        print(f"  Confidence Score: {result.get('confidence_score', 'N/A')}")
        print(f"  Document Type: {result.get('document_type', 'N/A')}")
        
        classification = result.get('sentence_classification', {}).get('classification_breakdown', {})
        print(f"\nSentence Classification:")
        print(f"  Claims: {classification.get('claim_count', 0)}")
        print(f"  Outcomes: {classification.get('outcome_count', 0)}")
        print(f"  Targets: {classification.get('target_count', 0)}")
        print(f"  Transparency: {classification.get('transparency_count', 0)}")
        print(f"  Neutral: {classification.get('neutral_count', 0)}")
        
        print("\n" + "="*80)
        print("MEMORY PROFILE SUMMARY")
        print("="*80)
        print("\nReview the [MEMORY] logs above to identify:")
        print("  1. Peak RSS memory usage")
        print("  2. Stage where peak occurs")
        print("  3. Whether RSS exceeds 400 MB")
        print("  4. Embedding matrix sizes at each stage")
        print("  5. Sentence/object counts at each stage")
        
        print("\n" + "="*80)
        print("PEAK MEMORY IDENTIFICATION")
        print("="*80)
        print("\nLook for the highest [MEMORY] value above.")
        print("The stage with the highest value is the memory bottleneck.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
