import pandas as pd
from job_recommendation_vdb import (
    validate_candidate_input,
    validate_job_record,
    apply_layer1_eligibility_filter,
    apply_filters_on_dataframe,
    connect_mongo,
    load_all_active_jobs
)

def demo_with_real_jobs(candidate_name, candidate, filters):
    print(f" {candidate_name.upper()} RECOMMENDED JOBS ")
    print(f"Filters: {filters}")
    
    try:
        # Connect to MongoDB and load real jobs
        client = connect_mongo()
        jobs_df = load_all_active_jobs(client)
        
        if jobs_df.empty:
            print("No active jobs found in database")
            return
            
        print(f"Total active jobs in database: {len(jobs_df)}")
        
        # Apply filters first
        filtered_jobs = apply_filters_on_dataframe(jobs_df, filters)
        print(f"After filters: {len(filtered_jobs)} jobs")
        
        validated_candidate = validate_candidate_input(candidate)
        print(f"Layer 0: Candidate validated")
        
        eligible_jobs = apply_layer1_eligibility_filter(filtered_jobs, validated_candidate)
        print(f"Layer 1: {len(eligible_jobs)} jobs passed eligibility constraints")
        
        # Debug: Show a sample of filtered jobs to understand the issue
        if len(filtered_jobs) > 0 and len(eligible_jobs) == 0:
            print("\nDEBUG: Sample of filtered jobs that were rejected by Layer 1:")
            for i, (_, job) in enumerate(filtered_jobs.head(3).iterrows(), 1):
                job_country = job.get('country', 'N/A')
                candidate_country = validated_candidate.get('country', 'N/A')
                job_setting = job.get('jobSetting', [])
                print(f"  Job {i}: {job.get('jobTitle', 'N/A')} | Country: {job_country} | Setting: {job_setting}")
                print(f"    Candidate Country: {candidate_country}")
                print(f"    Skills: {job.get('skills', [])}")
                print()
        
        if not eligible_jobs.empty:
            print(f"\nTop 5 Eligible Jobs:")
            for i, (_, job) in enumerate(eligible_jobs.head(5).iterrows(), 1):
                location = f"{job.get('city', 'N/A')}, {job.get('province', 'N/A')}, {job.get('country', 'N/A')}"
                work_setting = job.get('jobSetting', ['N/A'])
                if isinstance(work_setting, list):
                    work_setting = ', '.join(work_setting)
                    
                print(f"{i}. {job.get('jobTitle', 'N/A')} | {job.get('jobId', 'N/A')}")
                print(f"   Location: {location}")
                print(f"   Work Setting: {work_setting}")
                print(f"   Skills: {', '.join(job.get('skills', [])[:3])}")
                print()
        else:
            print("No jobs passed the eligibility constraints")
            
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

if __name__ == "__main__":
    
    software_engineer = {
        "candidate_id": "SE001",
        "headline": "Senior Software Engineer | Full Stack Developer",
        "desired_title": "Software Engineer",
        "skills": "Python,JavaScript,React,Node.js,AWS,Docker",
        "summary": "Experienced software engineer with 5+ years in full-stack development, specializing in modern web technologies and cloud infrastructure.",
        "experience": "5+ years in software development with expertise in Python, JavaScript, and cloud technologies.",
        "city": "Toronto",
        "province": "Ontario", 
        "country": "Canada",
        "work_setting_preference": "REMOTE"
    }
    
    data_scientist = {
        "candidate_id": "DS001",
        "headline": "Data Scientist | Machine Learning Engineer",
        "desired_title": "Data Scientist",
        "skills": "Python,Machine Learning,TensorFlow,SQL,Statistics,Pandas",
        "summary": "Data scientist with expertise in machine learning, statistical analysis, and building predictive models for business insights.",
        "experience": "3+ years in data science and machine learning, working with large datasets and ML frameworks.",
        "city": "Vancouver",
        "province": "British Columbia",
        "country": "Canada",
        "work_setting_preference": "HYBRID"
    }
    
    marketing_manager = {
        "candidate_id": "MM001",
        "headline": "Digital Marketing Manager | Growth Specialist",
        "desired_title": "Marketing Manager",
        "skills": "Digital Marketing,SEO,Google Analytics,Content Strategy,Social Media, Customer Success, Communication",
        "summary": "Results-driven marketing professional with expertise in digital campaigns, SEO optimization, and growth strategies.",
        "experience": "4+ years in digital marketing with proven track record of driving customer acquisition and engagement.",
        "city": "Montreal",
        "province": "Quebec",
        "country": "Canada",
        "work_setting_preference": "ONSITE"
    }

    training_specialist = {
        "candidate_id": "1",
        "headline": "Customer Experience Manager | Customer Success Manager",
        "desired_title": "Training Specialist",
        "skills": "Customer Success,Client Management, Communication",
        "summary": "Customer Success / Customer Experience professional focused on building strong relationships with enterprise clients and driving adoption of AI-powered SaaS products.",
        "experience": "3+ years in customer success and account management in SaaS and B2B environments, working closely with sales and product teams to track usage metrics and improve client outcomes.",
        "location": "Ottawa, Ontario",
        "city": "Ottawa",
        "province": "Ontario",
        "country": "Canada",
    }

    
    candidates = [
        ("Software Engineer", software_engineer, {
            "date_posted_days": None,
            "work_setting": ["REMOTE", "HYBRID"],
            "job_type": ["FULLTIME"],
            "experience_levels": [],
            "distance_km": None,
        }),
        ("Data Scientist", data_scientist, {
            "date_posted_days": None,
            "work_setting": ["HYBRID", "ONSITE"],
            "job_type": ["FULLTIME"],
            "experience_levels": [],
            "distance_km": None,
        }),
        ("Marketing Manager", marketing_manager, {
            "date_posted_days": None,
            "work_setting": ["ONSITE", "HYBRID"],
            "job_type": ["FULLTIME"],
            "experience_levels": [],
            "distance_km": None,
        }),
        ("Training_specialist", training_specialist, {
            "date_posted_days": None,
            "work_setting": ["REMOTE", "HYBRID"],
            "job_type": ["FULLTIME"],
            "experience_levels": [],
            "distance_km": None,
        })
    ]
    
    for profile_name, candidate, filters in candidates:
        demo_with_real_jobs(profile_name, candidate, filters)
        print("\n" + "="*50 + "\n")