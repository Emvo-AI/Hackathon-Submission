#!/usr/bin/env python3
"""
Test script for Google Cloud Storage PDF upload functionality.
"""

import os
from pdf_creator import pdf_creator_tool

def test_pdf_upload():
    """Test the PDF creation and upload to Google Cloud Storage."""
    
    # Sample data
    sample_plan = """**Daily Caloric Target:** 2000 kcal

**Macronutrient Split**
- Protein: ~100 g (20 %)
- Carbohydrates: ~250 g (50 %)
- Fats: ~67 g (30 %)

**Culturally Appropriate Foods**
• Breakfast: Veg poha with peanuts + a glass of low‑fat milk  
• Lunch: 2 whole‑wheat rotis, chickpea curry, mixed‑veg salad  
• Dinner: Brown‑rice pulao with tofu & veggies  

**Allergy / Restriction Substitutes**
You indicated a lactose intolerance. Replace dairy with soy or almond alternatives.

**Hydration**
Aim for 2.5 L water daily; include 1 ORS sachet post‑workout if exercising in humid climates."""

    sample_user_info = {
        "name": "Test User",
        "location": "Test Location",
        "goals": "Test goals"
    }
    
    print("Testing PDF creation and GCS upload...")
    print(f"User: {sample_user_info['name']}")
    print(f"Location: {sample_user_info['location']}")
    
    try:
        # Call the PDF creator tool
        result = pdf_creator_tool(sample_plan, sample_user_info)
        
        # Check if result is a URL (GCS upload successful) or base64 (fallback)
        if result.startswith('http'):
            print("✅ SUCCESS: PDF uploaded to Google Cloud Storage!")
            print(f"📄 Public URL: {result}")
        else:
            print("⚠️  FALLBACK: GCS upload failed, returned base64 encoded PDF")
            print(f"📄 Base64 length: {len(result)} characters")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    # Check if required environment variables are set
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    if not project_id:
        print("⚠️  Warning: GOOGLE_CLOUD_PROJECT_ID environment variable not set")
        print("   The tool will fall back to base64 encoding if GCS upload fails")
    
    test_pdf_upload() 