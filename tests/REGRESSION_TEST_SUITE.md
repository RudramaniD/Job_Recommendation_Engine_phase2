# 🧪 REGRESSION TEST SUITE - 25 SCENARIOS (Frontend Payload Format)

## Test Execution Guide
1. Run each payload in Postman: `POST http://localhost:8000/api/v1/recommendations`
2. Note the top 5 job IDs returned
3. Run the MongoDB query to verify results manually
4. Check if engine results align with expected matches

---

## SCENARIO 1: AI/ML Engineer - Toronto (ONSITE)
**Test**: Gen AI/ML Engineer with extensive ML/AI skills seeking onsite work in Toronto

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "minBasePay": {
        "amount": 100,
        "payType": "HOURLY"
      },
      "workType": "FULLTIME",
      "workSetting": ["ONSITE"],
      "willingToRelocate": false
    },
    "_id": "TEST-001",
    "email": "test001@example.com",
    "languages": ["English"],
    "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "NLP", "AWS", "Azure", "GCP"],
    "workExperience": [
      {
        "jobTitle": "Gen AI/ML Engineer",
        "company": "Tech Corp",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2020-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Building AI-driven solutions using GPT-4, BERT, and LLMs"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 001",
    "headline": "AI/ML Engineer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  city: "Toronto",
  province: "Ontario",
  jobSetting: { $in: ["ONSITE"] },
  positionType: "FULLTIME",
  skills: { $in: ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "NLP"] }
}).limit(10)
```

**Expected**: High location scores (1.0), AI/ML jobs, onsite only

---

## SCENARIO 2: DevOps Engineer - Remote
**Test**: DevOps engineer seeking remote work

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE"],
      "willingToRelocate": false
    },
    "_id": "TEST-002",
    "email": "test002@example.com",
    "skills": ["Docker", "Kubernetes", "Jenkins", "AWS", "Terraform", "Python", "CI/CD"],
    "workExperience": [
      {
        "jobTitle": "DevOps Engineer",
        "company": "Cloud Services Inc",
        "workType": "FULLTIME",
        "city": "Calgary",
        "province": "Alberta",
        "country": "Canada",
        "startDate": "2019-03-01T00:00:00.000Z",
        "endDate": null,
        "description": "CI/CD pipeline automation and cloud infrastructure"
      }
    ],
    "city": "Calgary",
    "country": "Canada",
    "fullName": "Test User 002",
    "headline": "DevOps Engineer",
    "province": "Alberta"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobSetting: { $in: ["REMOTE"] },
  positionType: "FULLTIME",
  skills: { $in: ["Docker", "Kubernetes", "Jenkins", "AWS", "Terraform", "Python", "CI/CD"] }
}).limit(10)
```

**Expected**: Remote jobs only, DevOps roles prioritized

---

## SCENARIO 3: Frontend Developer - Hybrid
**Test**: Frontend developer seeking hybrid work in Toronto

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-003",
    "email": "test003@example.com",
    "skills": ["React", "JavaScript", "TypeScript", "CSS", "HTML", "Redux", "Webpack"],
    "workExperience": [
      {
        "jobTitle": "Frontend Developer",
        "company": "Design Agency",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2020-06-01T00:00:00.000Z",
        "endDate": null,
        "description": "Building responsive web interfaces with React"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 003",
    "headline": "Frontend Developer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  city: "Toronto",
  jobSetting: { $in: ["HYBRID"] },
  positionType: "FULLTIME",
  skills: { $in: ["React", "JavaScript", "TypeScript", "CSS", "HTML"] }
}).limit(10)
```

**Expected**: Hybrid jobs in Toronto, frontend roles

---

## SCENARIO 4: Backend Engineer - Multiple Cities
**Test**: Backend engineer open to multiple work settings

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-004",
    "email": "test004@example.com",
    "skills": ["Node.js", "Express", "PostgreSQL", "MongoDB", "REST API", "GraphQL", "Microservices"],
    "workExperience": [
      {
        "jobTitle": "Backend Engineer",
        "company": "API Services",
        "workType": "FULLTIME",
        "city": "Vancouver",
        "province": "British Columbia",
        "country": "Canada",
        "startDate": "2019-03-01T00:00:00.000Z",
        "endDate": null,
        "description": "Building scalable backend services"
      }
    ],
    "city": "Vancouver",
    "country": "Canada",
    "fullName": "Test User 004",
    "headline": "Backend Engineer",
    "province": "British Columbia"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobSetting: { $in: ["REMOTE", "HYBRID"] },
  positionType: "FULLTIME",
  skills: { $in: ["Node.js", "Express", "PostgreSQL", "MongoDB", "REST API", "GraphQL"] }
}).limit(10)
```

**Expected**: Remote/Hybrid backend jobs

---

## SCENARIO 5: Full Stack Developer - High Skill Overlap
**Test**: Full stack developer with extensive skills

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-005",
    "email": "test005@example.com",
    "skills": ["JavaScript", "TypeScript", "React", "Angular", "Node.js", "Express", "MongoDB", "PostgreSQL", "Docker", "Git", "AWS", "CI/CD"],
    "workExperience": [
      {
        "jobTitle": "Full Stack Developer",
        "company": "Tech Startup",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2019-06-01T00:00:00.000Z",
        "endDate": null,
        "description": "End-to-end web application development"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 005",
    "headline": "Full Stack Developer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  city: "Toronto",
  jobSetting: { $in: ["REMOTE", "HYBRID"] },
  $or: [
    { skills: { $in: ["JavaScript", "TypeScript", "React", "Angular"] } },
    { skills: { $in: ["Node.js", "Express", "MongoDB", "PostgreSQL"] } }
  ]
}).limit(10)
```

**Expected**: Very high skill scores (0.6-0.9), full stack jobs

---

## SCENARIO 6: Data Scientist - Exact Title Match
**Test**: Data Scientist looking for exact title match

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-006",
    "email": "test006@example.com",
    "skills": ["Python", "Machine Learning", "TensorFlow", "Pandas", "NumPy", "Scikit-learn", "SQL"],
    "workExperience": [
      {
        "jobTitle": "Data Scientist",
        "company": "AI Labs",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2020-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Machine learning model development and data analysis"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 006",
    "headline": "Data Scientist",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Data Scientist/i,
  city: "Toronto",
  skills: { $in: ["Python", "Machine Learning", "TensorFlow", "Pandas", "NumPy"] }
}).limit(10)
```

**Expected**: High title scores (0.75-1.0), "Data Scientist" jobs prioritized

---

## SCENARIO 7: Mobile Developer - iOS/Android
**Test**: Mobile developer with cross-platform skills

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-007",
    "email": "test007@example.com",
    "skills": ["Swift", "Kotlin", "iOS", "Android", "React Native", "Flutter", "Firebase"],
    "workExperience": [
      {
        "jobTitle": "Mobile Developer",
        "company": "App Studio",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2020-03-01T00:00:00.000Z",
        "endDate": null,
        "description": "Cross-platform mobile app development"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 007",
    "headline": "Mobile Developer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Mobile|iOS|Android/i,
  city: "Toronto",
  skills: { $in: ["Swift", "Kotlin", "iOS", "Android", "React Native", "Flutter"] }
}).limit(10)
```

**Expected**: Mobile development jobs, high title and skill scores

---

## SCENARIO 8: QA Engineer - Automation Testing
**Test**: QA engineer with automation skills

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-008",
    "email": "test008@example.com",
    "skills": ["Selenium", "Automation Testing", "JIRA", "Test Planning", "Python", "Java", "Cypress"],
    "workExperience": [
      {
        "jobTitle": "QA Engineer",
        "company": "Software Co",
        "workType": "FULLTIME",
        "city": "Ottawa",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2020-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Automated testing and quality assurance"
      }
    ],
    "city": "Ottawa",
    "country": "Canada",
    "fullName": "Test User 008",
    "headline": "QA Engineer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /QA|Quality|Test|Automation/i,
  province: "Ontario",
  skills: { $in: ["Selenium", "Automation Testing", "JIRA", "Test Planning", "Python"] }
}).limit(10)
```

**Expected**: QA/testing positions, title match important

---

## SCENARIO 9: Security Engineer - Cybersecurity
**Test**: Cybersecurity professional

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": true
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["ONSITE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-009",
    "email": "test009@example.com",
    "skills": ["Cybersecurity", "Penetration Testing", "SIEM", "Firewall", "Compliance", "Network Security"],
    "workExperience": [
      {
        "jobTitle": "Security Engineer",
        "company": "SecureCorp",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2019-06-01T00:00:00.000Z",
        "endDate": null,
        "description": "Network security and threat analysis"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 009",
    "headline": "Security Engineer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Security|Cybersecurity|InfoSec/i,
  city: "Toronto",
  skills: { $in: ["Cybersecurity", "Penetration Testing", "SIEM", "Firewall", "Compliance"] }
}).limit(10)
```

**Expected**: Security-focused roles, specialized matching

---

## SCENARIO 10: Product Manager - Non-Engineering
**Test**: Product manager seeking PM roles

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-010",
    "email": "test010@example.com",
    "skills": ["Product Strategy", "Roadmap Planning", "Agile", "User Research", "Analytics", "Stakeholder Management"],
    "workExperience": [
      {
        "jobTitle": "Product Manager",
        "company": "SaaS Company",
        "workType": "FULLTIME",
        "city": "Vancouver",
        "province": "British Columbia",
        "country": "Canada",
        "startDate": "2019-06-01T00:00:00.000Z",
        "endDate": null,
        "description": "Managing product lifecycle and strategy"
      }
    ],
    "city": "Vancouver",
    "country": "Canada",
    "fullName": "Test User 010",
    "headline": "Product Manager",
    "province": "British Columbia"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Product Manager|PM/i,
  city: "Vancouver",
  province: "British Columbia"
}).limit(10)
```

**Expected**: Product management roles, title match critical

---

## SCENARIO 11: Senior Cloud Architect
**Test**: Senior cloud specialist with 8+ years experience

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-011",
    "email": "test011@example.com",
    "skills": ["AWS", "Azure", "GCP", "Cloud Architecture", "Terraform", "Kubernetes", "Microservices"],
    "workExperience": [
      {
        "jobTitle": "Cloud Solutions Architect",
        "company": "Cloud Services",
        "workType": "FULLTIME",
        "city": "Vancouver",
        "province": "British Columbia",
        "country": "Canada",
        "startDate": "2016-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Designing cloud infrastructure solutions"
      }
    ],
    "city": "Vancouver",
    "country": "Canada",
    "fullName": "Test User 011",
    "headline": "Cloud Solutions Architect",
    "province": "British Columbia"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Cloud|Architect|Infrastructure/i,
  skills: { $in: ["AWS", "Azure", "GCP", "Cloud Architecture", "Terraform", "Kubernetes"] },
  experienceLevel: { $in: ["SENIOR", "MID_SENIOR", "LEAD"] }
}).limit(10)
```

**Expected**: Senior cloud roles, high skill and experience scores

---

## SCENARIO 12: Junior Developer - Entry Level
**Test**: Junior developer with minimal experience

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["ONSITE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-012",
    "email": "test012@example.com",
    "skills": ["HTML", "CSS", "JavaScript", "Git", "React"],
    "workExperience": [
      {
        "jobTitle": "Junior Web Developer",
        "company": "StartUp",
        "workType": "FULLTIME",
        "city": "Montreal",
        "province": "Quebec",
        "country": "Canada",
        "startDate": "2023-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Frontend development internship"
      }
    ],
    "city": "Montreal",
    "country": "Canada",
    "fullName": "Test User 012",
    "headline": "Junior Web Developer",
    "province": "Quebec"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  experienceLevel: { $in: ["ENTRY", "JUNIOR"] },
  city: "Montreal",
  province: "Quebec",
  skills: { $in: ["HTML", "CSS", "JavaScript", "Git", "React"] }
}).limit(10)
```

**Expected**: Entry-level jobs, low experience scores (0.2)

---

## SCENARIO 13: Contract PHP Developer
**Test**: Contractor seeking contract work

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "CONTRACT",
      "workSetting": ["REMOTE"],
      "willingToRelocate": false
    },
    "_id": "TEST-013",
    "email": "test013@example.com",
    "skills": ["PHP", "Laravel", "MySQL", "Vue.js", "REST API"],
    "workExperience": [
      {
        "jobTitle": "PHP Developer",
        "company": "Web Agency",
        "workType": "CONTRACT",
        "city": "Vancouver",
        "province": "British Columbia",
        "country": "Canada",
        "startDate": "2021-06-01T00:00:00.000Z",
        "endDate": "2023-12-31T00:00:00.000Z",
        "description": "Contract web development"
      }
    ],
    "city": "Vancouver",
    "country": "Canada",
    "fullName": "Test User 013",
    "headline": "Contract PHP Developer",
    "province": "British Columbia"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  positionType: "CONTRACT",
  jobSetting: { $in: ["REMOTE"] },
  skills: { $in: ["PHP", "Laravel", "MySQL", "Vue.js"] }
}).limit(10)
```

**Expected**: Contract positions only

---

## SCENARIO 14: Engineering Manager - Leadership
**Test**: Experienced professional with career progression

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-014",
    "email": "test014@example.com",
    "skills": ["Leadership", "Agile", "Java", "Python", "AWS", "Team Management", "Architecture"],
    "workExperience": [
      {
        "jobTitle": "Engineering Manager",
        "company": "Tech Giant",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2020-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Leading engineering teams"
      },
      {
        "jobTitle": "Senior Software Engineer",
        "company": "Mid Corp",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2017-01-01T00:00:00.000Z",
        "endDate": "2019-12-31T00:00:00.000Z",
        "description": "Backend development"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 014",
    "headline": "Engineering Manager",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Manager|Lead|Director/i,
  experienceLevel: { $in: ["SENIOR", "LEAD", "EXECUTIVE"] },
  city: "Toronto"
}).limit(10)
```

**Expected**: Management/leadership roles, high experience scores (0.8-1.0)

---

## SCENARIO 15: UI/UX Designer - Part-Time
**Test**: Designer seeking part-time work

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "PARTTIME",
      "workSetting": ["REMOTE"],
      "willingToRelocate": false
    },
    "_id": "TEST-015",
    "email": "test015@example.com",
    "skills": ["Figma", "Adobe XD", "UI/UX", "Prototyping", "User Research", "Wireframing"],
    "workExperience": [
      {
        "jobTitle": "UI/UX Designer",
        "company": "Design Studio",
        "workType": "PARTTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2021-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "User interface and experience design"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 015",
    "headline": "UI/UX Designer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  positionType: "PARTTIME",
  jobSetting: { $in: ["REMOTE"] },
  skills: { $in: ["Figma", "Adobe XD", "UI/UX", "Prototyping"] }
}).limit(10)
```

**Expected**: Part-time positions only

---

## SCENARIO 16: Data Analyst - Cross-Province
**Test**: Candidate in Ottawa looking at Ontario jobs

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["ONSITE"],
      "willingToRelocate": true
    },
    "_id": "TEST-016",
    "email": "test016@example.com",
    "skills": ["SQL", "Python", "Tableau", "Excel", "Power BI", "Data Visualization"],
    "workExperience": [
      {
        "jobTitle": "Data Analyst",
        "company": "Analytics Co",
        "workType": "FULLTIME",
        "city": "Ottawa",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2020-06-01T00:00:00.000Z",
        "endDate": null,
        "description": "Data analysis and visualization"
      }
    ],
    "city": "Ottawa",
    "country": "Canada",
    "fullName": "Test User 016",
    "headline": "Data Analyst",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  province: "Ontario",
  country: "Canada",
  jobSetting: { $in: ["ONSITE"] },
  skills: { $in: ["SQL", "Python", "Tableau", "Excel", "Power BI"] }
}).limit(10)
```

**Expected**: Jobs in Ontario (Toronto, Ottawa, etc.), location score 0.8 for same province

---

## SCENARIO 17: Business Analyst - Non-Technical
**Test**: Business analyst role

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-017",
    "email": "test017@example.com",
    "skills": ["Requirements Gathering", "SQL", "Excel", "Business Process", "Stakeholder Management", "JIRA"],
    "workExperience": [
      {
        "jobTitle": "Business Analyst",
        "company": "Consulting Inc",
        "workType": "FULLTIME",
        "city": "Montreal",
        "province": "Quebec",
        "country": "Canada",
        "startDate": "2020-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Business requirements and process analysis"
      }
    ],
    "city": "Montreal",
    "country": "Canada",
    "fullName": "Test User 017",
    "headline": "Business Analyst",
    "province": "Quebec"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Business Analyst|BA/i,
  city: "Montreal",
  province: "Quebec"
}).limit(10)
```

**Expected**: Business analyst roles, location and title important

---

## SCENARIO 18: Recent Graduate - No Experience
**Test**: Entry-level with no work history

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["ONSITE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-018",
    "email": "test018@example.com",
    "skills": ["Java", "Python", "Data Structures", "Algorithms", "Git"],
    "workExperience": [],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 018",
    "headline": "Computer Science Graduate",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  experienceLevel: { $in: ["ENTRY", "JUNIOR", "INTERN"] },
  city: "Toronto",
  skills: { $in: ["Java", "Python"] }
}).limit(10)
```

**Expected**: Entry-level jobs, low experience scores

---

## SCENARIO 19: Niche Technology - Rust Developer
**Test**: Specialized developer with rare skills

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE"],
      "willingToRelocate": false
    },
    "_id": "TEST-019",
    "email": "test019@example.com",
    "skills": ["Rust", "WebAssembly", "Systems Programming", "Performance Optimization", "C++"],
    "workExperience": [
      {
        "jobTitle": "Systems Engineer",
        "company": "Performance Co",
        "workType": "FULLTIME",
        "city": "Vancouver",
        "province": "British Columbia",
        "country": "Canada",
        "startDate": "2021-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Low-level systems programming"
      }
    ],
    "city": "Vancouver",
    "country": "Canada",
    "fullName": "Test User 019",
    "headline": "Rust Developer",
    "province": "British Columbia"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  skills: { $in: ["Rust", "WebAssembly", "Systems Programming"] }
}).limit(10)
```

**Expected**: Few matches, high semantic scores for related jobs

---

## SCENARIO 20: Project Manager - Scrum Master
**Test**: Project manager with Agile skills

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["ONSITE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-020",
    "email": "test020@example.com",
    "skills": ["Project Management", "Scrum", "JIRA", "Stakeholder Management", "Agile", "Risk Management"],
    "workExperience": [
      {
        "jobTitle": "Project Manager",
        "company": "Consulting Firm",
        "workType": "FULLTIME",
        "city": "Calgary",
        "province": "Alberta",
        "country": "Canada",
        "startDate": "2019-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Managing software projects"
      }
    ],
    "city": "Calgary",
    "country": "Canada",
    "fullName": "Test User 020",
    "headline": "Project Manager",
    "province": "Alberta"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  country: "Canada",
  jobTitle: /Project Manager|Scrum Master/i,
  jobSetting: { $in: ["ONSITE", "HYBRID"] }
}).limit(10)
```

**Expected**: Project management roles, location score 0.5 for same country

---

## SCENARIO 21: Content Writer - Minimal Skills
**Test**: Candidate with limited skill set

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE"],
      "willingToRelocate": false
    },
    "_id": "TEST-021",
    "email": "test021@example.com",
    "skills": ["Writing", "SEO", "Content Marketing"],
    "workExperience": [
      {
        "jobTitle": "Content Writer",
        "company": "Media Co",
        "workType": "FULLTIME",
        "city": "Montreal",
        "province": "Quebec",
        "country": "Canada",
        "startDate": "2022-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Blog and article writing"
      }
    ],
    "city": "Montreal",
    "country": "Canada",
    "fullName": "Test User 021",
    "headline": "Content Writer",
    "province": "Quebec"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Writer|Content|Editor/i,
  skills: { $in: ["Writing", "SEO"] }
}).limit(10)
```

**Expected**: Low skill scores but relevant title matches

---

## SCENARIO 22: .NET Developer - Windows Stack
**Test**: Microsoft stack developer

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-022",
    "email": "test022@example.com",
    "skills": ["C#", ".NET", "ASP.NET", "SQL Server", "Azure", "Entity Framework"],
    "workExperience": [
      {
        "jobTitle": "Software Developer",
        "company": "Software Inc",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2020-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Desktop and web application development"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 022",
    "headline": ".NET Developer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  city: "Toronto",
  skills: { $in: ["C#", ".NET", "ASP.NET", "SQL Server", "Azure"] }
}).limit(10)
```

**Expected**: .NET/Microsoft stack jobs, high skill overlap

---

## SCENARIO 23: Site Reliability Engineer (SRE)
**Test**: SRE with DevOps background

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-023",
    "email": "test023@example.com",
    "skills": ["Kubernetes", "Docker", "Terraform", "Monitoring", "Prometheus", "Grafana", "Python", "Linux"],
    "workExperience": [
      {
        "jobTitle": "Site Reliability Engineer",
        "company": "Tech Platform",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2019-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Infrastructure reliability and automation"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 023",
    "headline": "Site Reliability Engineer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /SRE|Site Reliability|DevOps|Platform Engineer/i,
  skills: { $in: ["Kubernetes", "Docker", "Terraform", "Monitoring", "Prometheus"] }
}).limit(10)
```

**Expected**: SRE/DevOps roles, high role affinity (0.7-1.0)

---

## SCENARIO 24: Database Administrator (DBA)
**Test**: DBA with database specialization

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["ONSITE", "HYBRID"],
      "willingToRelocate": false
    },
    "_id": "TEST-024",
    "email": "test024@example.com",
    "skills": ["PostgreSQL", "MySQL", "Oracle", "Database Design", "Performance Tuning", "Backup Recovery", "SQL"],
    "workExperience": [
      {
        "jobTitle": "Database Administrator",
        "company": "Enterprise Corp",
        "workType": "FULLTIME",
        "city": "Vancouver",
        "province": "British Columbia",
        "country": "Canada",
        "startDate": "2018-01-01T00:00:00.000Z",
        "endDate": null,
        "description": "Database management and optimization"
      }
    ],
    "city": "Vancouver",
    "country": "Canada",
    "fullName": "Test User 024",
    "headline": "Database Administrator",
    "province": "British Columbia"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Database|DBA/i,
  city: "Vancouver",
  skills: { $in: ["PostgreSQL", "MySQL", "Oracle", "Database Design", "SQL"] }
}).limit(10)
```

**Expected**: DBA roles, specialized matching

---

## SCENARIO 25: Technical Writer - Documentation
**Test**: Technical writer with software background

```json
{
  "data": {
    "workEligibility": {
      "authorization": "CAN_CITIZEN",
      "hasSecurityClearance": false
    },
    "jobPreferences": {
      "workType": "FULLTIME",
      "workSetting": ["REMOTE"],
      "willingToRelocate": false
    },
    "_id": "TEST-025",
    "email": "test025@example.com",
    "skills": ["Technical Writing", "Documentation", "API Documentation", "Markdown", "Git", "Confluence"],
    "workExperience": [
      {
        "jobTitle": "Technical Writer",
        "company": "Software Company",
        "workType": "FULLTIME",
        "city": "Toronto",
        "province": "Ontario",
        "country": "Canada",
        "startDate": "2020-06-01T00:00:00.000Z",
        "endDate": null,
        "description": "Creating technical documentation for software products"
      }
    ],
    "city": "Toronto",
    "country": "Canada",
    "fullName": "Test User 025",
    "headline": "Technical Writer",
    "province": "Ontario"
  }
}
```

**MongoDB Validation Query**:
```javascript
db.jobs.find({
  status: "ACTIVE",
  jobTitle: /Technical Writer|Documentation/i,
  jobSetting: { $in: ["REMOTE"] },
  skills: { $in: ["Technical Writing", "Documentation", "API Documentation"] }
}).limit(10)
```

**Expected**: Technical writing roles, remote positions

---

## 📊 VALIDATION CHECKLIST

For each test scenario, verify:

### ✅ Score Validation
- [ ] **Location Score**: Matches expected (1.0 same city, 0.8 same province, 0.5 same country)
- [ ] **Title Score**: Relevant jobs have higher scores (0.5-1.0)
- [ ] **Experience Score**: Aligns with candidate years (0.2-1.0)
- [ ] **Skill Score**: Jaccard overlap makes sense (0.0-1.0)
- [ ] **Semantic Score**: Similar jobs have higher scores (0.5-0.9)

### ✅ Filter Validation
- [ ] **Work Setting**: Only requested settings appear (REMOTE/HYBRID/ONSITE)
- [ ] **Work Type**: Only requested types appear (FULLTIME/PARTTIME/CONTRACT)
- [ ] **Experience Level**: Matches candidate seniority

### ✅ Business Logic
- [ ] **Layer 1 Constraints**: No jobs violating hard rules
- [ ] **Semantic Threshold**: All results have semantic_score >= 0.55
- [ ] **Skill Penalty**: Jobs with zero skill overlap have 50% penalty applied
- [ ] **Role Affinity**: Unrelated roles (affinity < 0.5) have 70% penalty applied
- [ ] **Location Eligibility**: Onsite/Hybrid jobs in same country only

### ✅ Ranking Quality
- [ ] **Top Result**: Makes intuitive sense as best match
- [ ] **Score Distribution**: Reasonable spread (not all 0.3 or all 0.9)
- [ ] **Diversity**: Mix of factors contributing to final score
- [ ] **Professional Relevance**: No irrelevant jobs (e.g., Event Coordinator for DevOps)

---

## 🎯 SUCCESS CRITERIA

**Pass Rate**: 23/25 scenarios (92%) should return relevant results

**Critical Scenarios** (Must Pass):
- Scenario 1: AI/ML Engineer with exact location + skills
- Scenario 2: DevOps remote-only
- Scenario 6: Data Scientist exact title match
- Scenario 5: Full stack high skill overlap
- Scenario 18: Recent graduate entry-level

**Known Edge Cases**:
- Scenario 19: Niche tech (Rust) may have <5 results
- Scenario 21: Minimal skills may have lower scores
- Scenario 25: Technical writer may have fewer matches

---

## 📝 REPORTING TEMPLATE

For each failed scenario, document:

```
Scenario #: [Number]
Issue: [Description]
Expected: [What should happen]
Actual: [What happened]
MongoDB Results: [Job IDs from manual query]
Engine Results: [Job IDs from API]
Root Cause: [Analysis]
Fix Required: [Yes/No]
```

---

## 🔧 API ENDPOINT

**URL**: `POST http://localhost:8000/api/v1/recommendations`

**Headers**:
```
Content-Type: application/json
```

**Payload Structure**:
```json
{
  "data": {
    // Candidate data with workEligibility, jobPreferences, skills, workExperience, etc.
  }
}
```

**Response Structure**:
```json
{
  "total_matches": 10,
  "matches": [
    {
      "jobId": "...",
      "jobTitle": "...",
      "city": "...",
      "province": "...",
      "country": "...",
      "locationScore": 1.0,
      "titleScore": 0.85,
      "experienceScore": 0.6,
      "skillScore": 0.7,
      "semanticScore": 0.82,
      "finalScore": 0.78
    }
  ]
}
```

---

**Test Suite Version**: 2.0 (Frontend Payload Format)  
**Created**: January 2025  
**Total Scenarios**: 25  
**Estimated Time**: 2-3 hours for complete validation  
**Performance Target**: ~4.77s per request
