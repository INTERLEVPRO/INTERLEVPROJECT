import fitz  # PyMuPDF
import docx2txt
import json
from openai import OpenAI
from backend.core.config import settings
from backend.models.schemas import CandidateProfile

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_path: str) -> str:
    text = docx2txt.process(file_path)
    return text

def parse_cv_with_ai(cv_text: str) -> CandidateProfile:
    prompt = """
    You are an expert HR assistant. Extract the following information from the provided CV text.
    Return the result as a JSON object with the following keys:
    - name (string or null)
    - email (string or null)
    - phone (string or null)
    - role (string or null, the primary job title/role of the candidate)
    - skills (list of strings, technical and soft skills)
    - experience_years (integer or null, total years of professional experience)
    - languages (list of strings, languages the candidate speaks)
    - summary (string or null, a short professional summary)
    
    Ensure the output is valid JSON.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # or gpt-3.5-turbo if needed
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"CV Text:\n{cv_text}"}
            ],
            response_format={"type": "json_object"}
        )
        
        parsed_data = json.loads(response.choices[0].message.content)
        return CandidateProfile(**parsed_data)
    except Exception as e:
        print(f"Error parsing CV with AI: {e}")
        # Return empty profile on failure
        return CandidateProfile()

def process_cv_file(file_path: str) -> CandidateProfile:
    if file_path.lower().endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
        
    return parse_cv_with_ai(text)
