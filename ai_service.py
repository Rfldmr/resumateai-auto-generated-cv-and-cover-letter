import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Konfigurasi OpenRouter/DeepSeek
# Pastikan set environment variable OPENROUTER_API_KEY
llm = ChatOpenAI(
    openai_api_key="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",
    openai_api_base="https://openrouter.ai/api/v1",
    model_name="xiaomi/mimo-v2-flash:free" # Atau deepseek/deepseek-r1
)

def process_resume_data(raw_data):
    """
    Menggunakan AI untuk memoles deskripsi pekerjaan dan membuat summary profesional.
    """
    prompt = ChatPromptTemplate.from_template("""
    Kamu adalah konsultan karir ahli. Tugasmu adalah memperbaiki data resume pengguna agar lebih profesional untuk format ATS.
    
    DATA MENTAH:
    {raw_data}
    
    INSTRUKSI:
    1. Buat 'summary' profesional (sudut pandang orang ketiga, misal "Caca Merica adalah...") berdasarkan data.
    2. Untuk setiap Pengalaman Kerja dan Organisasi: Ubah 'deskripsi' yang kasar menjadi list 'description_points' (3-5 bullet points) yang menggunakan kata kerja aktif (Managed, Developed, Created) dan menonjolkan pencapaian.
    3. Output harus dalam format JSON persis dengan struktur input, tapi dengan field 'summary' yang diisi dan 'description' diganti/ditambah 'description_points'.
    4. Jangan ubah data fakta (Tanggal, Nama Perusahaan).
    5. Gunakan Bahasa Indonesia yang formal.
    
    Output JSON Only:
    """)
    
    chain = prompt | llm | JsonOutputParser()
    refined_data = chain.invoke({"raw_data": json.dumps(raw_data)})
    return refined_data

def generate_cover_letter_text(refined_data):
    """
    Membuat Cover Letter Body email.
    """
    prompt = ChatPromptTemplate.from_template("""
    INSTRUKSI: Tulis HANYA body email lamaran kerja dalam Bahasa Indonesia. JANGAN tulis penjelasan, reasoning, atau thinking process. Langsung tulis cover letter-nya saja.
    
    Data pelamar:
    - Nama: {name}
    - Skill: {skills}
    - Pengalaman: {last_exp}
    
    Format:
    - Mulai dengan "Yth. HRD..." atau "Dengan hormat,"
    - Singkat (3-4 paragraf)
    - Fokus pada value untuk perusahaan
    - Akhiri dengan hormat dan nama
    
    OUTPUT LANGSUNG DALAM BAHASA INDONESIA, TANPA PENJELASAN APAPUN:
    """)
    
    # Ambil data relevan untuk hemat token
    last_role = refined_data['experience'][0]['role'] if refined_data.get('experience') else "Fresh Graduate"
    skills = ", ".join(refined_data['skills']['hard'][:3])
    
    chain = prompt | llm
    res = chain.invoke({
        "name": refined_data['full_name'],
        "skills": skills,
        "last_exp": last_role
    })
    return res.content