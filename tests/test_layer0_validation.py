#!/usr/bin/env python3
"""
Layer 0 Validation Tests - 10 test cases with different candidate scenarios
"""

if __name__ == "__main__":
    # Need to add match_jobs_for_candidate to the module first
    import sys
    sys.path.append('.')
    
    # Test Case 1: Normal candidate
    print("=" * 80)
    print("TEST CASE 1: Normal candidate")
    print("=" * 80)
    
    test1_candidate = {
        "candidate_id": "1",
        "headline": "Customer Experience Manager | Customer Success Manager",
        "desired_title": "Training Specialist",
        "skills": "Customer Success,Client Management Communication",
        "summary": "Customer Success professional focused on building strong relationships with enterprise clients.",
        "experience": "3+ years in customer success and account management in SaaS environments.",
        "city": "Ottawa",
        "province": "Ontario",
        "country": "Canada",
    }
    
    test1_filters = {
        "date_posted_days": None,
        "work_setting": ["HYBRID", "REMOTE"],
        "job_type": ["FULLTIME"],
        "experience_levels": [],
        "distance_km": None,
    }
    
    from job_recommendation_vdb import validate_candidate_input
    validated = validate_candidate_input(test1_candidate)
    print(f"Validated candidate: {validated['candidate_id']}, skills: {len(validated['skills'])}, experience: {validated['years_experience']}")
    
    # Test Case 2: Null candidate
    print("\n" + "=" * 80)
    print("TEST CASE 2: Null candidate")
    print("=" * 80)
    
    test2_candidate = None
    validated2 = validate_candidate_input(test2_candidate)
    print(f"Validated candidate: {validated2['candidate_id']}, skills: {len(validated2['skills'])}, experience: {validated2['years_experience']}")
    
    # Test Case 3: Empty candidate
    print("\n" + "=" * 80)
    print("TEST CASE 3: Empty candidate")
    print("=" * 80)
    
    test3_candidate = {}
    validated3 = validate_candidate_input(test3_candidate)
    print(f"Validated candidate: {validated3['candidate_id']}, skills: {len(validated3['skills'])}, experience: {validated3['years_experience']}")
    
    # Test Case 4: Malformed experience
    print("\n" + "=" * 80)
    print("TEST CASE 4: Malformed experience")
    print("=" * 80)
    
    test4_candidate = {
        "candidate_id": "4",
        "headline": "Software Developer",
        "desired_title": "Senior Developer",
        "skills": "Python,JavaScript,React",
        "years_experience": "not_a_number",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
    }
    validated4 = validate_candidate_input(test4_candidate)
    print(f"Validated candidate: {validated4['candidate_id']}, skills: {len(validated4['skills'])}, experience: {validated4['years_experience']}")
    
    # Test Case 5: Empty location fields
    print("\n" + "=" * 80)
    print("TEST CASE 5: Empty location fields")
    print("=" * 80)
    
    test5_candidate = {
        "candidate_id": "5",
        "headline": "Marketing Manager",
        "desired_title": "Marketing Director",
        "skills": "Marketing,SEO,Content Strategy",
        "city": "",
        "province": "",
        "country": "",
    }
    validated5 = validate_candidate_input(test5_candidate)
    print(f"Validated candidate: {validated5['candidate_id']}, city: {validated5['city']}, province: {validated5['province']}, country: {validated5['country']}")
    
    # Test Case 6: Missing required fields
    print("\n" + "=" * 80)
    print("TEST CASE 6: Missing required fields")
    print("=" * 80)
    
    test6_candidate = {
        "candidate_id": "6",
        "skills": None,
        "experience": None,
    }
    validated6 = validate_candidate_input(test6_candidate)
    print(f"Validated candidate: {validated6['candidate_id']}, skills: {validated6['skills']}, experience: {validated6['years_experience']}")
    
    # Test Case 7: Very long text fields
    print("\n" + "=" * 80)
    print("TEST CASE 7: Very long text fields")
    print("=" * 80)
    
    test7_candidate = {
        "candidate_id": "7",
        "headline": "A" * 2000,  # Very long headline
        "desired_title": "Data Scientist",
        "skills": "Python,Machine Learning,Statistics",
        "summary": "B" * 2000,  # Very long summary
        "city": "Vancouver",
        "province": "BC",
        "country": "Canada",
    }
    validated7 = validate_candidate_input(test7_candidate)
    print(f"Validated candidate: {validated7['candidate_id']}, headline length: {len(validated7['headline'])}, summary length: {len(validated7['summary'])}")
    
    # Test Case 8: Numeric experience field
    print("\n" + "=" * 80)
    print("TEST CASE 8: Numeric experience field")
    print("=" * 80)
    
    test8_candidate = {
        "candidate_id": "8",
        "headline": "Project Manager",
        "desired_title": "Senior Project Manager",
        "skills": "Project Management,Agile,Scrum",
        "years_experience": 5,  # Numeric value
        "city": "Montreal",
        "province": "Quebec",
        "country": "Canada",
    }
    validated8 = validate_candidate_input(test8_candidate)
    print(f"Validated candidate: {validated8['candidate_id']}, experience: {validated8['years_experience']}")
    
    # Test Case 9: Mixed data types
    print("\n" + "=" * 80)
    print("TEST CASE 9: Mixed data types")
    print("=" * 80)
    
    test9_candidate = {
        "candidate_id": 9,  # Numeric ID
        "headline": 12345,  # Numeric headline
        "desired_title": None,  # None title
        "skills": ["Python", "Java", "C++"],  # List skills
        "city": "Calgary",
        "province": "Alberta",
        "country": "Canada",
    }
    validated9 = validate_candidate_input(test9_candidate)
    print(f"Validated candidate: {validated9['candidate_id']}, headline: '{validated9['headline']}', skills: {validated9['skills']}")
    
    # Test Case 10: Edge case values
    print("\n" + "=" * 80)
    print("TEST CASE 10: Edge case values")
    print("=" * 80)
    
    test10_candidate = {
        "candidate_id": "",  # Empty string ID
        "headline": "   ",  # Whitespace only
        "desired_title": "UX Designer",
        "skills": ",,,,",  # Empty skills with commas
        "years_experience": -5,  # Negative experience
        "city": "Halifax",
        "province": "Nova Scotia",
        "country": "Canada",
    }
    validated10 = validate_candidate_input(test10_candidate)
    print(f"Validated candidate: {validated10['candidate_id']}, headline: '{validated10['headline']}', skills: {validated10['skills']}, experience: {validated10['years_experience']}")
    
    print("\n" + "=" * 80)
    print("LAYER 0 VALIDATION TEST SUMMARY")
    print("=" * 80)
    print("All 10 test cases completed successfully!")
    print("Layer 0 validation handles all edge cases without exceptions.")