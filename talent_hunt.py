import streamlit as st
import pandas as pd
from ast import literal_eval

# --- Load and prepare candidate data ---
df = pd.read_csv("intelligent_talent_assistant_candidates.csv")
df['Skills'] = df['Skills'].apply(literal_eval)
df['Job Title Applied'] = df['Job Title Applied'].str.lower()
df['Availability'] = df['Availability'].str.lower()

# --- Load interview schedule data ---
interview_df = pd.read_csv("interview_schedule.csv")
interview_df['Job Title'] = interview_df['Job Title'].str.lower()

# --- Define required skills per job title ---
required_skills_map = {
    'data analyst': {'python', 'sql', 'data visualization', 'communication'},
    'devops engineer': {'cloud computing', 'node.js', 'linux', 'docker'},
    'software engineer': {'machine learning', 'cloud computing', 'ai'},
    'python project manager': {'python', 'project management', 'communication', 'leadership'}
}

# --- Core functions ---
def get_top_candidates(job_title, min_experience=3):
    job_title_lower = job_title.lower()
    filtered = df[
        (df['Job Title Applied'] == job_title_lower) &
        (df['Availability'] == 'immediate') &
        (df['Experience (Years)'] >= min_experience)
    ].copy()

    if filtered.empty:
        return pd.DataFrame([{"Result": "No matching candidates found."}])

    required_skills = required_skills_map.get(job_title_lower, set())

    def score(row):
        skills = set(s.lower() for s in row['Skills'])
        skill_score = len(skills & required_skills) / len(required_skills) if required_skills else 0
        exp_score = min(row['Experience (Years)'] / 10, 1)
        fit_score = row['Cultural Fit Score'] / 10
        return round((skill_score * 0.5 + exp_score * 0.2 + fit_score * 0.3) * 100, 2)

    filtered['Match Score'] = filtered.apply(score, axis=1)
    return filtered.sort_values(by='Match Score', ascending=False)[
        ['Name', 'Job Title Applied', 'Experience (Years)', 'Match Score']
    ]

def get_total_applicants(job_title):
    return df[df['Job Title Applied'] == job_title.lower()].shape[0]

def get_immediate_joiners(job_title):
    result = df[
        (df['Job Title Applied'] == job_title.lower()) &
        (df['Availability'] == 'immediate')
    ][['Name', 'Experience (Years)', 'Availability']]
    return result if not result.empty else pd.DataFrame([{"Result": "No immediate joiners found."}])

def get_interview_schedule(job_title=None):
    if job_title:
        jt = job_title.lower()
        filtered = interview_df[interview_df['Job Title'] == jt]
    else:
        filtered = interview_df
    return filtered if not filtered.empty else pd.DataFrame([{"Result": "No interview schedules found."}])

# --- Enhanced Engagement Assistant ---
def engagement_agent(user_input):
    user_input = user_input.lower()
    
    # Known job titles for extraction
    job_titles = {
        "data analyst": "data analyst",
        "devops engineer": "devops engineer",
        "software engineer": "software engineer",
        "python project manager": "python project manager"
    }

    # Detect job title in the query
    detected_title = None
    for key in job_titles:
        if key in user_input:
            detected_title = job_titles[key]
            break

    # Intent detection and routing
    if any(kw in user_input for kw in ["top", "best", "fit"]):
        if detected_title:
            return get_top_candidates(detected_title)
        return "Please mention the job title to view top candidates (e.g., 'top candidates for Data Analyst')."

    if any(kw in user_input for kw in ["how many", "total", "applied", "applicants"]):
        if detected_title:
            count = get_total_applicants(detected_title)
            return f"Total candidates applied for '{detected_title.title()}': {count}"
        return "Please specify the job title (e.g., 'how many applied for DevOps Engineer')."

    if any(kw in user_input for kw in ["immediate", "join now", "available"]):
        if detected_title:
            return get_immediate_joiners(detected_title)
        return "Please mention the job title to view immediate joiners (e.g., 'immediate joiners for Software Engineer')."

    if any(kw in user_input for kw in ["interview", "schedule"]):
        # If they asked about interviews without specifying a title, show all
        return get_interview_schedule(detected_title) if detected_title else get_interview_schedule()

    if any(kw in user_input for kw in ["help", "what can you do", "options"]):
        return (
            "You can ask things like:\n"
            "- Show top candidates for DevOps Engineer\n"
            "- Who is available immediately for Data Analyst?\n"
            "- How many people applied for Python Project Manager?\n"
            "- Show interview schedule for Software Engineer"
        )

    return "I'm here to help! Try asking about top candidates, total applicants, immediate joiners, or interview schedules."

# --- Streamlit UI ---
st.title("Talent Acquisition Manager Chatbot")

# Dropdown actions
option = st.selectbox("Select an action:", [
    "Show Top Candidates",
    "Total Applicants",
    "Immediate Joiners",
    "Interview Schedule"
])

job_title_input = st.selectbox("Select Job Title:", [
    "Data Analyst",
    "DevOps Engineer",
    "Software Engineer",
    "Python Project Manager"
])

if st.button("Get Info"):
    if option == "Show Top Candidates":
        df_out = get_top_candidates(job_title_input)
        if df_out.empty or "Result" in df_out.columns:
            st.warning(df_out.iloc[0]["Result"])
        else:
            st.write(df_out)

    elif option == "Total Applicants":
        count = get_total_applicants(job_title_input)
        st.success(f"Total candidates applied for '{job_title_input}': {count}")

    elif option == "Immediate Joiners":
        df_out = get_immediate_joiners(job_title_input)
        if df_out.empty or "Result" in df_out.columns:
            st.warning(df_out.iloc[0]["Result"])
        else:
            st.write(df_out)

    elif option == "Interview Schedule":
        df_out = get_interview_schedule(job_title_input)
        if df_out.empty or "Result" in df_out.columns:
            st.warning(df_out.iloc[0]["Result"])
        else:
            st.write(df_out)

# Free-text Engagement Assistant
st.subheader("Engagement Assistant")
user_query = st.text_input("Ask a question about the recruitment process:")

if user_query:
    response = engagement_agent(user_query)
    # If DataFrame, display table (or warning if it has a Result column)
    if isinstance(response, pd.DataFrame):
        if response.empty or "Result" in response.columns:
            st.warning(response.iloc[0]["Result"])
        else:
            st.write(response)
    else:
        st.write(response)