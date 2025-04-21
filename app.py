# Add these imports at the top of the file
import streamlit as st
import os
import json
import pandas as pd
import base64
from io import BytesIO
import tempfile
import skill_ass
import time
import altair as alt
# For PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# Set Streamlit page config
st.set_page_config(
    page_title="AI Skill",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def add_custom_css():
    """Add custom CSS styles to enhance the app's appearance"""
    st.markdown("""
    <style>
        /* General styling */
        .main {
            background-color: #f0f4f8;
            padding: 1rem;
        }
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1, h2, h3 {
            color: #1e3a8a;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        h1 {
            text-align: center;
            font-weight: 700;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #3b82f6;
        }
        /* Cards for sections */
        .card {
            background-color: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            border-left: 5px solid #3b82f6;
        }
        /* Skill ratings */
        .rating {
            font-family: monospace;
            color: #3b82f6;
        }
        /* Metric containers */
        .metric-container {
            background-color: #f1f8ff;
            border-left: 4px solid #3b82f6;
            padding: 12px;
            margin: 12px 0;
            border-radius: 0 8px 8px 0;
        }
        /* Override default button styles */
        .stButton>button {
            background-color: #3b82f6;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #1e40af;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transform: translateY(-2px);
        }
        /* Upload area styling */
        [data-testid="stFileUploader"] {
            border: 2px dashed #3b82f6;
            border-radius: 10px;
            padding: 15px;
            background-color: #f8fafc;
        }
        /* Success message */
        .success-message {
            background-color: #d1fae5;
            color: #065f46;
            padding: 12px;
            border-radius: 6px;
            margin: 15px 0;
            border-left: 5px solid #10b981;
        }
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6;
            border-radius: 6px 6px 0 0;
            padding: 8px 18px;
            height: auto;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            background-color: #3b82f6 !important;
            color: white !important;
        }
        /* Progress bars */
        .stProgress > div > div {
            background-color: #3b82f6;
        }
        /* Download links */
        a {
            color: #3b82f6;
            text-decoration: none;
            font-weight: 500;
            padding: 8px 16px;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            display: inline-block;
            text-align: center;
            margin: 8px 0;
            transition: all 0.3s ease;
        }
        a:hover {
            background-color: #3b82f6;
            color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        /* Information callouts */
        .info-box {
            background-color: #e0f2fe;
            border-left: 5px solid #38bdf8;
            padding: 12px;
            margin: 12px 0;
            border-radius: 0 6px 6px 0;
        }
    </style>
    """, unsafe_allow_html=True)

def make_json_serializable(obj):
    """Convert any non-serializable objects to strings"""
    if hasattr(obj, '__class__') and obj.__class__.__name__ == 'CrewOutput':
        return str(obj)
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    else:
        return obj

def display_summary(results):
    """Display the summary results in a nicely formatted way"""
    summary = str(results.get("summary", "Summary not available"))
    
    # Display the markdown summary with custom styling
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(summary, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def create_skills_chart(skill_data):
    """Create a bar chart for skills visualization"""
    try:
        # Try to extract skills and ratings in a format suitable for visualization
        skill_list = []
        
        # Handle different possible structures of skill_data
        if isinstance(skill_data, dict) and "skills" in skill_data:
            # If we have a structured format with a 'skills' key
            categories = skill_data.get("skills", {})
            for category, skills in categories.items():
                if isinstance(skills, dict):
                    for skill, rating in skills.items():
                        if isinstance(rating, (int, float)):
                            skill_list.append({"Skill": f"{skill} ({category})", "Rating": rating})
                        elif isinstance(rating, dict) and "rating" in rating:
                            skill_list.append({"Skill": f"{skill} ({category})", "Rating": rating["rating"]})
                elif isinstance(skills, list):
                    for skill_item in skills:
                        if isinstance(skill_item, dict) and "name" in skill_item and "rating" in skill_item:
                            skill_list.append({"Skill": f"{skill_item['name']} ({category})", "Rating": skill_item["rating"]})
        
        # If the above didn't work, try a flatter structure
        if not skill_list and isinstance(skill_data, dict):
            for category, items in skill_data.items():
                if isinstance(items, dict):
                    for skill, value in items.items():
                        if isinstance(value, (int, float)):
                            skill_list.append({"Skill": f"{skill} ({category})", "Rating": value})
                        elif isinstance(value, dict) and "rating" in value:
                            skill_list.append({"Skill": f"{skill} ({category})", "Rating": value["rating"]})
        
        # If we still don't have skills, try to parse from raw text
        if not skill_list and "raw_result" in skill_data:
            import re
            # Look for patterns like "skill_name: X/10" or "skill_name - X/10"
            skill_pattern = r'([A-Za-z\+\#]+(?:\s[A-Za-z\+\#]+)*)\s*[:-]\s*(\d+)(?:/10)?'
            matches = re.findall(skill_pattern, skill_data["raw_result"])
            for skill, rating in matches:
                skill_list.append({"Skill": skill, "Rating": int(rating)})
        
        # Create the chart if we have data
        if skill_list:
            df = pd.DataFrame(skill_list)
            
            # Sort by rating in descending order
            df = df.sort_values("Rating", ascending=False)
            
            # Take top 10 skills for cleaner visualization
            df = df.head(10)
            
            # Create the chart
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('Rating:Q', scale=alt.Scale(domain=[0, 10])),
                y=alt.Y('Skill:N', sort='-x'),
                color=alt.Color('Rating:Q', scale=alt.Scale(scheme='blues')),
                tooltip=['Skill', 'Rating']
            ).properties(
                title='Top Skills Rating',
                width=600,
                height=400
            )
            
            return chart
        
        return None
        
    except Exception as e:
        st.error(f"Error creating skills chart: {str(e)}")
        return None

def display_full_analysis(results):
    """Display the full analysis results in tabbed sections"""
    tabs = st.tabs(["Resume Data", "Profile Data", "Skills Evaluation", "Job Match", "Evaluation Pipeline", "Interview Questions"])
    
    # Tab 1: Resume Data
    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📄 Resume Information")
        
        resume_data = results.get("resume_data", {})
        if isinstance(resume_data, dict) and "raw_result" not in resume_data:
            # Display personal info if available
            if "personal_info" in resume_data:
                st.markdown("### Personal Information")
                personal_info = resume_data["personal_info"]
                for key, value in personal_info.items():
                    st.markdown(f"**{key.title()}:** {value}")
                
            # Display skills if available
            if "skills" in resume_data:
                st.markdown("### Skills")
                skills = resume_data["skills"]
                if isinstance(skills, list):
                    st.markdown(", ".join(skills))
                elif isinstance(skills, dict):
                    for category, skill_list in skills.items():
                        st.markdown(f"**{category}:** {', '.join(skill_list)}")
                
            # Display experience if available
            if "experience" in resume_data:
                st.markdown("### Work Experience")
                for job in resume_data["experience"]:
                    if isinstance(job, dict):
                        company = job.get("company", "")
                        title = job.get("title", "")
                        period = job.get("period", "")
                        
                        st.markdown(f"**{title}** at **{company}** ({period})")
                        
                        if "responsibilities" in job and job["responsibilities"]:
                            if isinstance(job["responsibilities"], list):
                                for resp in job["responsibilities"]:
                                    st.markdown(f"- {resp}")
                            else:
                                st.markdown(job["responsibilities"])
                    else:
                        st.markdown(f"- {job}")
            
            # Display education if available
            if "education" in resume_data:
                st.markdown("### Education")
                for edu in resume_data["education"]:
                    if isinstance(edu, dict):
                        degree = edu.get("degree", "")
                        institution = edu.get("institution", "")
                        year = edu.get("year", "")
                        
                        st.markdown(f"**{degree}** from **{institution}** ({year})")
                    else:
                        st.markdown(f"- {edu}")
                        
            # Display certifications if available
            if "certifications" in resume_data:
                st.markdown("### Certifications")
                certs = resume_data["certifications"]
                if isinstance(certs, list):
                    for cert in certs:
                        if isinstance(cert, dict):
                            name = cert.get("name", "")
                            issuer = cert.get("issuer", "")
                            date = cert.get("date", "")
                            
                            st.markdown(f"**{name}** from **{issuer}** ({date})")
                        else:
                            st.markdown(f"- {cert}")
                else:
                    st.markdown(certs)
                    
            # Display profiles if available
            if "profiles" in resume_data:
                st.markdown("### Online Profiles")
                profiles = resume_data["profiles"]
                if isinstance(profiles, dict):
                    for platform, username in profiles.items():
                        st.markdown(f"**{platform.title()}:** {username}")
        else:
            # Display raw text if structured data is not available
            st.json(resume_data)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 2: Profile Data
    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("👤 Profile Information")
        
        profile_data = results.get("profile_data", {})
        if profile_data:
            # GitHub data
            if "github" in profile_data:
                st.markdown("### GitHub Profile")
                github_data = profile_data["github"]
                
                # Create two columns
                col1, col2 = st.columns(2)
                
                if isinstance(github_data, dict):
                    with col1:
                        st.markdown(f"**Username:** {github_data.get('username', 'N/A')}")
                        st.markdown(f"**Name:** {github_data.get('name', 'N/A')}")
                        st.markdown(f"**Public Repos:** {github_data.get('public_repos', 'N/A')}")
                        st.markdown(f"**Profile Created:** {github_data.get('profile_created_at', 'N/A')}")
                    
                    with col2:
                        st.markdown(f"**Followers:** {github_data.get('followers', 'N/A')}")
                        st.markdown(f"**Following:** {github_data.get('following', 'N/A')}")
                        st.markdown(f"**Stars Received:** {github_data.get('starred_repos_count', 'N/A')}")
                        st.markdown(f"**Forks Received:** {github_data.get('forks_count', 'N/A')}")
                    
                    if "top_languages" in github_data:
                        st.markdown("**Top Languages:**")
                        st.markdown(", ".join(github_data["top_languages"]))
                    
                    if "bio" in github_data and github_data["bio"] != "Not available":
                        st.markdown(f"**Bio:** {github_data['bio']}")
                else:
                    st.markdown(github_data)
            
            # LeetCode data
            if "leetcode" in profile_data:
                st.markdown("### LeetCode Profile")
                leetcode_data = profile_data["leetcode"]
                
                if isinstance(leetcode_data, dict):
                    st.markdown(f"**Username:** {leetcode_data.get('username', 'N/A')}")
                    st.markdown(f"**Total Problems Solved:** {leetcode_data.get('total_problems_solved', 'N/A')}")
                    
                    # Problems by difficulty
                    if "problems_by_difficulty" in leetcode_data:
                        st.markdown("**Problems by Difficulty:**")
                        difficulties = leetcode_data["problems_by_difficulty"]
                        
                        cols = st.columns(3)
                        if isinstance(difficulties, dict):
                            with cols[0]:
                                st.metric("Easy", difficulties.get("Easy", "N/A"))
                            with cols[1]:
                                st.metric("Medium", difficulties.get("Medium", "N/A"))
                            with cols[2]:
                                st.metric("Hard", difficulties.get("Hard", "N/A"))
                    
                    st.markdown(f"**Ranking:** {leetcode_data.get('ranking', 'N/A')}")
                    
                    # Badges
                    if "badges" in leetcode_data and leetcode_data["badges"]:
                        st.markdown("**Badges:**")
                        st.markdown(", ".join(leetcode_data["badges"]))
                else:
                    st.markdown(leetcode_data)
        else:
            st.info("No profile information available")
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 3: Skills Evaluation
    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🛠️ Skills Evaluation")
        
        skill_evaluation = results.get("skill_evaluation", {})
        
        # Try to create a visual chart from the skills data
        chart = create_skills_chart(skill_evaluation)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        
        if isinstance(skill_evaluation, dict) and "raw_result" not in skill_evaluation:
            # Display structured skills evaluation
            if "skills" in skill_evaluation:
                for category, skills in skill_evaluation["skills"].items():
                    st.markdown(f"### {category}")
                    
                    if isinstance(skills, dict):
                        for skill, rating in skills.items():
                            if isinstance(rating, (int, float)):
                                stars = "★" * int(rating) + "☆" * (10 - int(rating))
                                st.markdown(f"**{skill}:** {rating}/10 <span class='rating'>{stars}</span>", unsafe_allow_html=True)
                            elif isinstance(rating, dict):
                                skill_rating = rating.get("rating", "N/A")
                                evidence = rating.get("evidence", "")
                                stars = "★" * int(skill_rating) + "☆" * (10 - int(skill_rating))
                                st.markdown(f"**{skill}:** {skill_rating}/10 <span class='rating'>{stars}</span>", unsafe_allow_html=True)
                                if evidence:
                                    st.markdown(f"*Evidence:* {evidence}")
                    elif isinstance(skills, list):
                        for skill_item in skills:
                            if isinstance(skill_item, dict):
                                skill_name = skill_item.get("name", "")
                                skill_rating = skill_item.get("rating", "N/A")
                                evidence = skill_item.get("evidence", "")
                                
                                stars = "★" * int(skill_rating) + "☆" * (10 - int(skill_rating))
                                st.markdown(f"**{skill_name}:** {skill_rating}/10 <span class='rating'>{stars}</span>", unsafe_allow_html=True)
                                if evidence:
                                    st.markdown(f"*Evidence:* {evidence}")
            
            # Display analysis if available
            if "analysis" in skill_evaluation:
                st.markdown("### Analysis")
                analysis = skill_evaluation["analysis"]
                if isinstance(analysis, dict):
                    for key, value in analysis.items():
                        st.markdown(f"**{key.replace('_', ' ').title()}:**")
                        st.markdown(value)
                else:
                    st.markdown(analysis)
        else:
            # Display raw text if structured data is not available
            st.json(skill_evaluation)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 4: Job Match
    with tabs[3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🎯 Job Match Analysis")
        
        job_match = results.get("job_match", {})
        
        if isinstance(job_match, dict) and "raw_result" not in job_match:
            # Overall match percentage
            if "overall_match" in job_match:
                overall = job_match["overall_match"]
                if isinstance(overall, (int, float)) or (isinstance(overall, str) and overall.replace('.', '', 1).isdigit()):
                    overall_pct = float(overall)
                    st.markdown(f"<div style='text-align: center;'><h2>Overall Match: {overall_pct:.1f}%</h2></div>", unsafe_allow_html=True)
                    
                    # Progress bar for overall match
                    st.progress(overall_pct/100)
                else:
                    st.markdown(f"**Overall Match:** {overall}")
            
            # Essential requirements
            if "essential_requirements" in job_match:
                st.markdown("### Essential Requirements")
                essentials = job_match["essential_requirements"]
                
                if isinstance(essentials, dict):
                    for req, match_info in essentials.items():
                        if isinstance(match_info, dict):
                            match_pct = match_info.get("match_percentage", "N/A")
                            explanation = match_info.get("explanation", "")
                            
                            if isinstance(match_pct, (int, float)) or (isinstance(match_pct, str) and match_pct.replace('.', '', 1).isdigit()):
                                match_float = float(match_pct)
                                col1, col2 = st.columns([3, 7])
                                with col1:
                                    st.markdown(f"**{req}:**")
                                with col2:
                                    st.progress(match_float/100)
                                    st.markdown(f"{match_float:.1f}%")
                            else:
                                st.markdown(f"**{req}:** {match_pct}")
                            
                            if explanation:
                                st.markdown(f"*{explanation}*")
                        else:
                            st.markdown(f"**{req}:** {match_info}")
                elif isinstance(essentials, list):
                    for item in essentials:
                        if isinstance(item, dict):
                            req = item.get("requirement", "")
                            match_pct = item.get("match_percentage", "N/A")
                            explanation = item.get("explanation", "")
                            
                            if isinstance(match_pct, (int, float)) or (isinstance(match_pct, str) and match_pct.replace('.', '', 1).isdigit()):
                                match_float = float(match_pct)
                                col1, col2 = st.columns([3, 7])
                                with col1:
                                    st.markdown(f"**{req}:**")
                                with col2:
                                    st.progress(match_float/100)
                                    st.markdown(f"{match_float:.1f}%")
                            else:
                                st.markdown(f"**{req}:** {match_pct}")
                            
                            if explanation:
                                st.markdown(f"*{explanation}*")
            
            # Preferred requirements
            if "preferred_requirements" in job_match:
                st.markdown("### Preferred Requirements")
                preferred = job_match["preferred_requirements"]
                
                if isinstance(preferred, dict):
                    for req, match_info in preferred.items():
                        if isinstance(match_info, dict):
                            match_pct = match_info.get("match_percentage", "N/A")
                            explanation = match_info.get("explanation", "")
                            
                            if isinstance(match_pct, (int, float)) or (isinstance(match_pct, str) and match_pct.replace('.', '', 1).isdigit()):
                                match_float = float(match_pct)
                                col1, col2 = st.columns([3, 7])
                                with col1:
                                    st.markdown(f"**{req}:**")
                                with col2:
                                    st.progress(match_float/100)
                                    st.markdown(f"{match_float:.1f}%")
                            else:
                                st.markdown(f"**{req}:** {match_pct}")
                            
                            if explanation:
                                st.markdown(f"*{explanation}*")
                        else:
                            st.markdown(f"**{req}:** {match_info}")
                elif isinstance(preferred, list):
                    for item in preferred:
                        if isinstance(item, dict):
                            req = item.get("requirement", "")
                            match_pct = item.get("match_percentage", "N/A")
                            explanation = item.get("explanation", "")
                            
                            if isinstance(match_pct, (int, float)) or (isinstance(match_pct, str) and match_pct.replace('.', '', 1).isdigit()):
                                match_float = float(match_pct)
                                col1, col2 = st.columns([3, 7])
                                with col1:
                                    st.markdown(f"**{req}:**")
                                with col2:
                                    st.progress(match_float/100)
                                    st.markdown(f"{match_float:.1f}%")
                            else:
                                st.markdown(f"**{req}:** {match_pct}")
                            
                            if explanation:
                                st.markdown(f"*{explanation}*")
        else:
            # Display raw result if structured data not available
            st.json(job_match)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 5: Evaluation Pipeline
    with tabs[4]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 Evaluation Pipeline Results")
        
        evaluation_results = results.get("evaluation_results", {})
        
        if isinstance(evaluation_results, dict) and "raw_result" not in evaluation_results:
            # Display final score and recommendation
            if "total_score" in evaluation_results or "recommendation" in evaluation_results:
                col1, col2 = st.columns(2)
                
                with col1:
                    if "total_score" in evaluation_results:
                        total_score = evaluation_results["total_score"]
                        st.markdown(f"<div style='text-align: center;'><h2>Total Score: {total_score}/100</h2></div>", unsafe_allow_html=True)
                        # Create a gauge-like visualization with progress bar
                        st.progress(float(total_score)/100)
                
                with col2:
                    if "recommendation" in evaluation_results:
                        recommendation = evaluation_results["recommendation"]
                        
                        # Color code the recommendation
                        if "proceed" in recommendation.lower():
                            st.markdown(f"<div style='text-align: center; background-color: #d4edda; padding: 10px; border-radius: 5px;'><h3>{recommendation}</h3></div>", unsafe_allow_html=True)
                        elif "hold" in recommendation.lower():
                            st.markdown(f"<div style='text-align: center; background-color: #fff3cd; padding: 10px; border-radius: 5px;'><h3>{recommendation}</h3></div>", unsafe_allow_html=True)
                        elif "reject" in recommendation.lower():
                            st.markdown(f"<div style='text-align: center; background-color: #f8d7da; padding: 10px; border-radius: 5px;'><h3>{recommendation}</h3></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='text-align: center;'><h3>{recommendation}</h3></div>", unsafe_allow_html=True)
            
            # Display stage results
            stages = ["stage_1", "stage_2", "stage_3", "stage_4"]
            stage_names = {
                "stage_1": "Basic Eligibility",
                "stage_2": "Skill Match", 
                "stage_3": "Domain Experience",
                "stage_4": "Role Fit"
            }
            
            st.markdown("### Evaluation Stages")
            
            # Create columns for the stages
            cols = st.columns(len(stages))
            
            for i, stage_key in enumerate(stages):
                if stage_key in evaluation_results:
                    stage = evaluation_results[stage_key]
                    
                    with cols[i]:
                        st.markdown(f"<div style='text-align: center;'><h4>{stage_names[stage_key]}</h4></div>", unsafe_allow_html=True)
                        
                        if isinstance(stage, dict):
                            score = stage.get("score", "N/A")
                            max_score = 0
                            if stage_key == "stage_1":
                                max_score = 20
                            elif stage_key == "stage_2":
                                max_score = 40
                            elif stage_key == "stage_3":
                                max_score = 15
                            elif stage_key == "stage_4":
                                max_score = 25
                            
                            st.markdown(f"<div style='text-align: center;'><h2>{score}/{max_score}</h2></div>", unsafe_allow_html=True)
                            
                            # Create progress bar
                            if isinstance(score, (int, float)) and max_score > 0:
                                st.progress(float(score)/max_score)
                            
                            # Display justification if available
                            justification = stage.get("justification", "")
                            if justification:
                                with st.expander("Justification"):
                                    st.markdown(justification)
                        else:
                            st.markdown(str(stage))
        else:
            # Display raw result if structured data not available
            st.json(evaluation_results)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Tab 6: Interview Questions
    with tabs[5]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🎯 Technical Interview Questions")
        
        questions = results.get("interview_questions", {})
        
        # Handle different formats of interview questions data
        if isinstance(questions, dict):
            if "questions" in questions:
                questions_list = questions["questions"]
            elif "raw_result" in questions:
                # Try to extract JSON from the raw result
                import re
                import json
                json_match = re.search(r'```json\n(.*?)\n```', questions["raw_result"], re.DOTALL)
                if json_match:
                    try:
                        extracted_json = json.loads(json_match.group(1))
                        if "questions" in extracted_json:
                            questions_list = extracted_json["questions"]
                        else:
                            questions_list = extracted_json
                    except:
                        questions_list = []
                else:
                    # If no JSON found, try to parse questions by pattern
                    question_pattern = r'(\d+[\)\.]\s*.*?(?:\?|:))([^0-9]*(?=\d+[\)\.]\s*|$))'
                    matches = re.findall(question_pattern, questions["raw_result"], re.DOTALL)
                    questions_list = [{"question": q.strip(), "explanation": e.strip()} for q, e in matches]
            else:
                # Assume the dict itself contains the questions
                questions_list = [questions]
        elif isinstance(questions, list):
            questions_list = questions
        elif isinstance(questions, str):
            # Try to convert string to JSON if possible
            try:
                questions_list = json.loads(questions)
                if isinstance(questions_list, dict) and "questions" in questions_list:
                    questions_list = questions_list["questions"]
            except:
                st.write(questions)
                st.markdown('</div>', unsafe_allow_html=True)
                return
        else:
            st.write("Questions format not recognized.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        if isinstance(questions_list, list):
            for i, q in enumerate(questions_list):
                if isinstance(q, dict):
                    question = q.get("question", "")
                    difficulty = q.get("difficulty", "")
                    assessment = q.get("assessment", "")
                    guidance = q.get("guidance", "")
                    
                    # Display question with nice formatting
                    st.markdown(f"### Q{i+1}: {question}")
                    
                    col1, col2 = st.columns(2)
                    if difficulty:
                        with col1:
                            st.markdown(f"**Difficulty:** {difficulty}")
                    
                    if assessment:
                        with col2:
                            st.markdown(f"**Assessing:** {assessment}")
                    
                    if guidance:
                        st.markdown(f"**Guidance:** {guidance}")
                    
                    st.markdown("---")
                else:
                    # If it's just a string
                    st.markdown(f"### Q{i+1}: {q}")
                    st.markdown("---")
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_interview_questions(results):
    """Display interview questions in a structured format"""
    questions = results.get("interview_questions", {})
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎯 Technical Interview Questions")
    
    # Handle different formats of interview questions data
    if isinstance(questions, dict):
        if "questions" in questions:
            questions_list = questions["questions"]
        elif "raw_result" in questions:
            # Try to extract JSON from the raw result
            import re
            import json
            json_match = re.search(r'```json\n(.*?)\n```', questions["raw_result"], re.DOTALL)
            if json_match:
                try:
                    extracted_json = json.loads(json_match.group(1))
                    if "questions" in extracted_json:
                        questions_list = extracted_json["questions"]
                    else:
                        questions_list = extracted_json
                except:
                    questions_list = []
            else:
                # If no JSON found, try to parse questions by pattern
                question_pattern = r'(\d+[\)\.]\s*.*?(?:\?|:))([^0-9]*(?=\d+[\)\.]\s*|$))'
                matches = re.findall(question_pattern, questions["raw_result"], re.DOTALL)
                questions_list = [{"question": q.strip(), "explanation": e.strip()} for q, e in matches]
        else:
            # Assume the dict itself contains the questions
            questions_list = [questions]
    elif isinstance(questions, list):
        questions_list = questions
    elif isinstance(questions, str):
        # Try to convert string to JSON if possible
        try:
            questions_list = json.loads(questions)
            if isinstance(questions_list, dict) and "questions" in questions_list:
                questions_list = questions_list["questions"]
        except:
            st.write(questions)
            st.markdown('</div>', unsafe_allow_html=True)
            return
    else:
        st.write("Questions format not recognized.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    if isinstance(questions_list, list):
        for i, q in enumerate(questions_list):
            if isinstance(q, dict):
                question = q.get("question", "")
                difficulty = q.get("difficulty", "")
                assessment = q.get("assessment", "")
                guidance = q.get("guidance", "")
                
                # Display question with nice formatting
                st.markdown(f"### Q{i+1}: {question}")
                
                col1, col2 = st.columns(2)
                if difficulty:
                    with col1:
                        st.markdown(f"**Difficulty:** {difficulty}")
                
                if assessment:
                    with col2:
                        st.markdown(f"**Assessing:** {assessment}")
                
                if guidance:
                    st.markdown(f"**Guidance:** {guidance}")
                
                st.markdown("---")
            else:
                # If it's just a string
                st.markdown(f"### Q{i+1}: {q}")
                st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True)



    # Fix for Tab 3: Skills Evaluation
# Inside the display_full_analysis function
    def create_skills_chart(skill_data):
        """Create a bar chart for skills visualization"""
        try:
            # Try to extract skills and ratings in a format suitable for visualization
            skill_list = []
            
            # Handle different possible structures of skill_data
            if isinstance(skill_data, dict) and "skills" in skill_data:
                # If we have a structured format with a 'skills' key
                categories = skill_data.get("skills", {})
                for category, skills in categories.items():
                    if isinstance(skills, dict):
                        for skill, rating in skills.items():
                            if isinstance(rating, (int, float)):
                                skill_list.append({"Skill": f"{skill} ({category})", "Rating": rating})
                            elif isinstance(rating, dict) and "rating" in rating:
                                skill_list.append({"Skill": f"{skill} ({category})", "Rating": rating["rating"]})
                    elif isinstance(skills, list):
                        for skill_item in skills:
                            if isinstance(skill_item, dict) and "name" in skill_item and "rating" in skill_item:
                                skill_list.append({"Skill": f"{skill_item['name']} ({category})", "Rating": skill_item["rating"]})
            
            # If we still don't have skills, try to parse from raw text
            if not skill_list and isinstance(skill_data, dict) and "raw_result" in skill_data:
                import re
                # Look for patterns like "skill_name: X/10" or "skill_name - X/10"
                skill_pattern = r'([A-Za-z\+\#]+(?:\s[A-Za-z\+\#]+)*)\s*[:-]\s*(\d+)(?:/10)?'
                matches = re.findall(skill_pattern, skill_data["raw_result"])
                for skill, rating in matches:
                    skill_list.append({"Skill": skill, "Rating": int(rating)})
            
            # Create the chart if we have data
            if skill_list:
                df = pd.DataFrame(skill_list)
                
                # Sort by rating in descending order
                df = df.sort_values("Rating", ascending=False)
                
                # Take top 10 skills for cleaner visualization
                df = df.head(10)
                
                # Create the chart
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X('Rating:Q', scale=alt.Scale(domain=[0, 10])),
                    y=alt.Y('Skill:N', sort='-x'),
                    color=alt.Color('Rating:Q', scale=alt.Scale(scheme='blues')),
                    tooltip=['Skill', 'Rating']
                ).properties(
                    title='Top Skills Rating',
                    width=600,
                    height=400
                )
                
                return chart
            
            return None
            
        except Exception as e:
            st.error(f"Error creating skills chart: {str(e)}")
            return None
        
def download_results(results):
    """Create a downloadable JSON file of the analysis results"""
    # Make results JSON serializable
    serializable_results = make_json_serializable(results)
    
    # Convert to JSON
    json_results = json.dumps(serializable_results, indent=4)
    
    # Create a download button
    b64 = base64.b64encode(json_results.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="resume_analysis_results.json">Download Results (JSON)</a>'
    return href

def download_report_pdf(results):
    """Generate a PDF report of the analysis results"""
    try:
        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        # Create a BytesIO object to store the PDF
        pdf_buffer = BytesIO()
        
        # Create the PDF document using ReportLab
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Custom styles
        title_style = styles["Heading1"]
        heading2_style = styles["Heading2"]
        heading3_style = styles["Heading3"]
        normal_style = styles["Normal"]
        
        # Add title
        elements.append(Paragraph("Resume Analysis Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Add summary
        elements.append(Paragraph("Executive Summary", heading2_style))
        elements.append(Spacer(1, 6))
        summary = str(results.get("summary", "Summary not available"))
        elements.append(Paragraph(summary, normal_style))
        elements.append(Spacer(1, 15))
        
        # Add skills evaluation
        elements.append(Paragraph("Skills Evaluation", heading2_style))
        elements.append(Spacer(1, 6))
        
        skill_eval = results.get("skill_evaluation", {})
        if isinstance(skill_eval, dict) and "skills" in skill_eval:
            for category, skills in skill_eval["skills"].items():
                elements.append(Paragraph(f"{category}", heading3_style))
                elements.append(Spacer(1, 6))
                
                if isinstance(skills, dict):
                    # Create a table for skills
                    data = [["Skill", "Rating", "Evidence"]]
                    for skill, rating in skills.items():
                        if isinstance(rating, (int, float)):
                            data.append([skill, f"{rating}/10", ""])
                        elif isinstance(rating, dict) and "rating" in rating:
                            evidence = rating.get("evidence", "")
                            data.append([skill, f"{rating['rating']}/10", evidence])
                    
                    # Create the table
                    if len(data) > 1:
                        table = Table(data, colWidths=[200, 70, 230])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
                        
        # Add analysis if available
        if isinstance(skill_eval, dict) and "analysis" in skill_eval:
            elements.append(Paragraph("Skills Analysis", heading3_style))
            elements.append(Spacer(1, 6))
            analysis = skill_eval["analysis"]
            if isinstance(analysis, dict):
                for key, value in analysis.items():
                    elements.append(Paragraph(f"{key.replace('_', ' ').title()}", heading3_style))
                    elements.append(Paragraph(value, normal_style))
                    elements.append(Spacer(1, 6))
            else:
                elements.append(Paragraph(str(analysis), normal_style))
            elements.append(Spacer(1, 12))
        
        # Add job match
        elements.append(Paragraph("Job Match Analysis", heading2_style))
        elements.append(Spacer(1, 6))
        
        job_match = results.get("job_match", {})
        if isinstance(job_match, dict):
            if "overall_match" in job_match:
                overall = job_match["overall_match"]
                if isinstance(overall, (int, float)) or (isinstance(overall, str) and overall.replace('.', '', 1).isdigit()):
                    elements.append(Paragraph(f"Overall Match: {float(overall):.1f}%", heading3_style))
                else:
                    elements.append(Paragraph(f"Overall Match: {overall}", heading3_style))
                elements.append(Spacer(1, 6))
            
            # Essential requirements
            if "essential_requirements" in job_match:
                elements.append(Paragraph("Essential Requirements", heading3_style))
                elements.append(Spacer(1, 6))
                essentials = job_match["essential_requirements"]
                
                if isinstance(essentials, dict):
                    data = [["Requirement", "Match %", "Explanation"]]
                    for req, match_info in essentials.items():
                        if isinstance(match_info, dict):
                            match_pct = match_info.get("match_percentage", "N/A")
                            explanation = match_info.get("explanation", "")
                            data.append([req, f"{match_pct}%", explanation])
                        else:
                            data.append([req, str(match_info), ""])
                    
                    # Create the table
                    if len(data) > 1:
                        table = Table(data, colWidths=[170, 70, 260])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
                elif isinstance(essentials, list):
                    data = [["Requirement", "Match %", "Explanation"]]
                    for item in essentials:
                        if isinstance(item, dict):
                            req = item.get("requirement", "")
                            match_pct = item.get("match_percentage", "N/A")
                            explanation = item.get("explanation", "")
                            data.append([req, f"{match_pct}%", explanation])
                    
                    # Create the table
                    if len(data) > 1:
                        table = Table(data, colWidths=[170, 70, 260])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
                elif isinstance(essentials, list):
                    data = [["Requirement", "Match %", "Explanation"]]
                    for item in essentials:
                        if isinstance(item, dict):
                            req = item.get("requirement", "")
                            match_pct = item.get("match_percentage", "N/A")
                            explanation = item.get("explanation", "")
                            data.append([req, f"{match_pct}%", explanation])
                    
                    # Create the table
                    if len(data) > 1:
                        table = Table(data, colWidths=[170, 70, 260])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
            
            # Desired requirements
            if "desired_requirements" in job_match:
                elements.append(Paragraph("Desired Requirements", heading3_style))
                elements.append(Spacer(1, 6))
                desired = job_match["desired_requirements"]
                
                if isinstance(desired, dict):
                    data = [["Requirement", "Match %", "Explanation"]]
                    for req, match_info in desired.items():
                        if isinstance(match_info, dict):
                            match_pct = match_info.get("match_percentage", "N/A")
                            explanation = match_info.get("explanation", "")
                            data.append([req, f"{match_pct}%", explanation])
                        else:
                            data.append([req, str(match_info), ""])
                    
                    # Create the table
                    if len(data) > 1:
                        table = Table(data, colWidths=[170, 70, 260])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
                elif isinstance(desired, list):
                    data = [["Requirement", "Match %", "Explanation"]]
                    for item in desired:
                        if isinstance(item, dict):
                            req = item.get("requirement", "")
                            match_pct = item.get("match_percentage", "N/A")
                            explanation = item.get("explanation", "")
                            data.append([req, f"{match_pct}%", explanation])
                    
                    # Create the table
                    if len(data) > 1:
                        table = Table(data, colWidths=[170, 70, 260])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
                        
            # Add match analysis
            if "analysis" in job_match:
                elements.append(Paragraph("Match Analysis", heading3_style))
                elements.append(Spacer(1, 6))
                analysis = job_match["analysis"]
                elements.append(Paragraph(str(analysis), normal_style))
                elements.append(Spacer(1, 12))
        
        # Add evaluation results
        elements.append(Paragraph("Evaluation Results", heading2_style))
        elements.append(Spacer(1, 6))
        
        eval_results = results.get("evaluation_results", {})
        if isinstance(eval_results, dict):
            if "total_score" in eval_results:
                elements.append(Paragraph(f"Total Score: {eval_results['total_score']}/100", heading3_style))
                elements.append(Spacer(1, 6))
            if "recommendation" in eval_results:
                elements.append(Paragraph(f"Recommendation: {eval_results['recommendation']}", heading3_style))
                elements.append(Spacer(1, 6))
            
            # Add detailed evaluation
            if "detailed_evaluation" in eval_results:
                elements.append(Paragraph("Detailed Evaluation", heading3_style))
                elements.append(Spacer(1, 6))
                detailed = eval_results["detailed_evaluation"]
                
                if isinstance(detailed, dict):
                    data = [["Category", "Score", "Comments"]]
                    for category, details in detailed.items():
                        if isinstance(details, dict):
                            score = details.get("score", "N/A")
                            comments = details.get("comments", "")
                            data.append([category, score, comments])
                        else:
                            data.append([category, str(details), ""])
                    
                    # Create the table
                    if len(data) > 1:
                        table = Table(data, colWidths=[150, 70, 280])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
        
        # Add interview questions
        interview_questions = results.get("interview_questions", [])
        if interview_questions:
            elements.append(Paragraph("Recommended Interview Questions", heading2_style))
            elements.append(Spacer(1, 6))
            
            if isinstance(interview_questions, list):
                for i, question in enumerate(interview_questions, 1):
                    elements.append(Paragraph(f"{i}. {question}", normal_style))
                    elements.append(Spacer(1, 6))
            elif isinstance(interview_questions, dict):
                for category, questions in interview_questions.items():
                    elements.append(Paragraph(f"{category}", heading3_style))
                    elements.append(Spacer(1, 6))
                    
                    if isinstance(questions, list):
                        for i, question in enumerate(questions, 1):
                            elements.append(Paragraph(f"{i}. {question}", normal_style))
                            elements.append(Spacer(1, 6))
        
        # Build the PDF
        doc.build(elements)
        
        # Reset buffer position
        pdf_buffer.seek(0)
        
        # Create download button
        b64 = base64.b64encode(pdf_buffer.getvalue()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="resume_analysis_report.pdf">Download Report (PDF)</a>'
        return href
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return ""
    
def main():
    """Main function to run the Streamlit app"""
    # Add custom CSS
    add_custom_css()
    
    # App header with enhanced styling
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #1e3a8a; font-size: 2.5rem; font-weight: 700;">🚀 AI Skill Assessment System</h1>
        <p style="font-size: 1.2rem; color: #4b5563; max-width: 800px; margin: 0 auto;">
            Upload a resume and job description to get an AI-powered analysis and evaluation.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs with enhanced styling
    tabs = st.tabs(["📤 Upload", "📊 Analysis", "ℹ️ About"])
    
    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("📤 Upload Files")
        
        # Resume upload
        resume_file = st.file_uploader("Upload Resume (PDF, DOCX)", type=["pdf", "docx", "txt"])
        
        # Job description input
        st.markdown("### 📋 Job Description")
        job_description_option = st.radio(
            "Choose an option:",
            ["Enter job description", "Use sample job description"]
        )
        
        if job_description_option == "Enter job description":
            job_requirements = st.text_area(
                "Enter job requirements:",
                height=200,
                placeholder="Enter the job description including requirements, responsibilities, etc."
            )
        else:
            job_requirements = skill_ass.sample_job_requirements
            st.text_area("Sample job description:", value=job_requirements, height=200, disabled=True)
        
        # Analysis button
        analyze_button = st.button("Analyze Resume", type="primary", use_container_width=True)
        
        # In the main function, in the analyze_button handler:
        if analyze_button:
            if resume_file is not None and job_requirements:
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{resume_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(resume_file.getvalue())
                        temp_path = tmp_file.name
                    
                    # Display progress with enhanced styling
                    progress_container = st.container()
                    with progress_container:
                        st.markdown("""
                        <div style="text-align: center; margin-bottom: 15px;">
                            <h3 style="color: #1e3a8a;">Analyzing Resume</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Create a spinner for visual feedback
                        with st.spinner('Processing...'):
                            # Analysis started
                            status_text.markdown('<div style="text-align: center; color: #4b5563;">Starting analysis...</div>', unsafe_allow_html=True)
                            progress_bar.progress(10)
                            time.sleep(0.5)  # Small delay for visual feedback
                            
                            # Run the assessment
                            status_text.markdown('<div style="text-align: center; color: #4b5563;">Extracting resume data...</div>', unsafe_allow_html=True)
                            progress_bar.progress(20)
                            time.sleep(0.5)
                            
                            # Open the file in binary mode
                            with open(temp_path, "rb") as file:
                                status_text.markdown('<div style="text-align: center; color: #4b5563;">Analyzing skills and experience...</div>', unsafe_allow_html=True)
                                progress_bar.progress(40)
                                
                                # Call the function from skill_ass.py
                                results = skill_ass.run_skill_assessment(file, job_requirements)
                                
                                status_text.markdown('<div style="text-align: center; color: #4b5563;">Generating recommendations...</div>', unsafe_allow_html=True)
                                progress_bar.progress(70)
                                time.sleep(0.5)
                                
                                status_text.markdown('<div style="text-align: center; color: #4b5563;">Creating report...</div>', unsafe_allow_html=True)
                                progress_bar.progress(90)
                                time.sleep(0.5)
                                
                                # Save results to session state
                                st.session_state.results = results
                                st.session_state.analysis_complete = True
                                
                                # Complete
                                status_text.markdown('<div style="text-align: center; color: #065f46; font-weight: bold;">Analysis complete!</div>', unsafe_allow_html=True)
                                progress_bar.progress(100)
                        
                        # Show success message with enhanced styling
                        st.markdown("""
                        <div style="background-color: #d1fae5; padding: 15px; border-radius: 8px; border-left: 5px solid #10b981; margin-top: 20px;">
                            <p style="color: #065f46; font-weight: 500; margin: 0;">
                                <span style="font-size: 1.2rem;">✅</span> Analysis completed successfully! Go to the Analysis tab to view results.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                if resume_file is None:
                    st.warning("Please upload a resume file.")
                if not job_requirements:
                    st.warning("Please enter or select a job description.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tabs[1]:
        if 'analysis_complete' in st.session_state and st.session_state.analysis_complete:
            results = st.session_state.results
            
            # Create two columns for the summary and download buttons
            col1, col2 = st.columns([7, 3])
            
            with col1:
                st.header("📊 Analysis Results")
            
            with col2:
                st.markdown(download_results(results), unsafe_allow_html=True)
                st.markdown(download_report_pdf(results), unsafe_allow_html=True)
            
            # Display the summary
            st.subheader("📝 Executive Summary")
            display_summary(results)
            
            # Display interview questions
            st.subheader("🎯 Recommended Interview Questions")
            display_interview_questions(results)
            
            # Display the full analysis
            st.subheader("🔍 Detailed Analysis")
            display_full_analysis(results)
            
        else:
            st.info("Upload a resume and job description in the Upload tab to see analysis results.")
    
    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("ℹ️ About AI Resume Analyzer")
        
        st.markdown("""
        This application uses AI to analyze resumes and job descriptions to help:
        
        - **Recruiters** evaluate candidate skills and job fit quickly and objectively
        - **Candidates** understand how their resume matches job requirements
        - **Hiring managers** create better interview questions based on candidate profiles
        
        ### How It Works
        
        1. **Upload a resume** in PDF, DOCX, or TXT format
        2. **Enter a job description** with requirements and responsibilities
        3. **Get an AI-powered analysis** including:
           - Skill evaluations
           - Job match percentage
           - Technical interview questions
           - Overall recommendations
        
        ### Privacy & Data
        
        All data is processed temporarily and not stored permanently. Analysis results can be downloaded for your records.
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()