from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash-lite",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def describe_csv_data(columns, sample_data):
    prompt = f"""
You are a professional data analyst.

Given:
- Column names
- Top 5 sample rows

Task:
Write a short, clear dataset description suitable for a data profiling report.

Rules:
- Do NOT guess missing context.
- Do NOT mention rows count unless visible.
- Keep it under 5 sentences.
- Focus on what the data represents and what analysis is possible.

Columns:
{columns}

Sample Rows:
{sample_data}
"""

    response = model.invoke(prompt)
    return response.content

def describe_text_data(text):
    prompt = f"""
You are a professional data analyst.