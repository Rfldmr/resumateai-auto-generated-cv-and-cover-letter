from flask import Flask, render_template, request, send_file
from ai_service import process_resume_data, generate_cover_letter_text
from pdf_generator import generate_ats_cv
import os
import re
from dotenv import load_dotenv

# Load API Key dari file .env
load_dotenv()

app = Flask(__name__)

# Fungsi helper untuk mempersingkat nama bulan
def shorten_month(date_string):
    """Mengubah nama bulan panjang menjadi 3 huruf (Jan, Feb, Mar, dst)"""
    if not date_string:
        return date_string
    
    month_map = {
        'Januari': 'Jan',
        'Februari': 'Feb',
        'Maret': 'Mar',
        'April': 'Apr',
        'Mei': 'Mei',
        'Juni': 'Jun',
        'Juli': 'Jul',
        'Agustus': 'Agu',
        'September': 'Sep',
        'Oktober': 'Okt',
        'November': 'Nov',
        'Desember': 'Des',
        # English version
        'January': 'Jan',
        'February': 'Feb',
        'March': 'Mar',
        'May': 'May',
        'June': 'Jun',
        'July': 'Jul',
        'August': 'Aug',
        'October': 'Oct',
        'December': 'Dec'
    }
    
    result = date_string
    for long_name, short_name in month_map.items():
        result = result.replace(long_name, short_name)
    
    return result

# Pastikan folder static ada untuk menyimpan PDF
os.makedirs('static', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    # --- 1. AMBIL DATA DARI FORM ---
    
    # Inisialisasi struktur data
    raw_data = {
        "full_name": request.form.get('full_name'),
        "email": request.form.get('email'),
        "phone": request.form.get('phone'),
        "city": request.form.get('city'),
        "country": request.form.get('country'),
        "experience": [],
        "education": [],
        "organization": [], # (Opsional jika ingin ditambahkan di HTML nanti)
        "awards": [],
        "skills": {
            # Pisahkan string berdasarkan koma dan hapus spasi berlebih
            "soft": [s.strip() for s in request.form.get('soft_skills', '').split(',') if s.strip()],
            "hard": [s.strip() for s in request.form.get('hard_skills', '').split(',') if s.strip()]
        }
    }

    # --- 2. PARSING DYNAMIC LISTS ---

    # A. Pengalaman Kerja
    exp_companies = request.form.getlist('exp_company[]')
    exp_roles = request.form.getlist('exp_role[]')
    exp_starts = request.form.getlist('exp_start[]')
    exp_ends = request.form.getlist('exp_end[]')
    exp_descs = request.form.getlist('exp_desc[]')

    for i in range(len(exp_companies)):
        # Hanya masukkan jika nama perusahaan tidak kosong
        if exp_companies[i].strip():
            raw_data['experience'].append({
                "company": exp_companies[i],
                "role": exp_roles[i],
                "start_date": shorten_month(exp_starts[i]),
                "end_date": shorten_month(exp_ends[i]),
                "description": exp_descs[i] # Data mentah ini akan dipoles AI
            })

    # B. Pendidikan
    edu_schools = request.form.getlist('edu_school[]')
    edu_majors = request.form.getlist('edu_major[]')
    edu_starts = request.form.getlist('edu_start[]')
    edu_ends = request.form.getlist('edu_end[]')
    edu_descs = request.form.getlist('edu_desc[]')

    for i in range(len(edu_schools)):
        if edu_schools[i].strip():
            raw_data['education'].append({
                "institution": edu_schools[i],
                "major": edu_majors[i],
                "start_date": shorten_month(edu_starts[i]),
                "end_date": shorten_month(edu_ends[i]),
                "description": edu_descs[i]
            })

    # C. Penghargaan
    aw_names = request.form.getlist('award_name[]')
    aw_years = request.form.getlist('award_year[]')
    aw_descs = request.form.getlist('award_desc[]')

    for i in range(len(aw_names)):
        if aw_names[i].strip():
            raw_data['awards'].append({
                "name": aw_names[i],
                "year": aw_years[i],
                "description": aw_descs[i]
            })

    # --- 3. PROSES AI (DeepSeek) ---
    print("🤖 Mengirim data ke DeepSeek untuk dipoles...")
    
    # Refine Resume (Membuat summary & memoles bullet points)
    try:
        refined_data = process_resume_data(raw_data)
    except Exception as e:
        print(f"Error AI Processing: {e}")
        # Jika AI gagal, gunakan data mentah agar aplikasi tidak crash
        refined_data = raw_data 
        refined_data['summary'] = "Ringkasan profesional belum tersedia karena gangguan koneksi AI."
    
    # Pastikan semua experience dan organization punya description_points
    # Jika AI tidak memberikan description_points, buat dari description
    for exp in refined_data.get('experience', []):
        if 'description_points' not in exp and 'description' in exp:
            # Pisahkan berdasarkan line break atau buat satu poin
            desc = exp['description'].strip()
            if desc:
                # Coba pisah berdasarkan newline
                points = [p.strip() for p in desc.split('\n') if p.strip()]
                if len(points) > 1:
                    exp['description_points'] = points
                else:
                    # Jika cuma 1 kalimat panjang, jadikan 1 poin
                    exp['description_points'] = [desc]
            else:
                exp['description_points'] = []
    
    for org in refined_data.get('organization', []):
        if 'description_points' not in org and 'description' in org:
            desc = org['description'].strip()
            if desc:
                points = [p.strip() for p in desc.split('\n') if p.strip()]
                if len(points) > 1:
                    org['description_points'] = points
                else:
                    org['description_points'] = [desc]
            else:
                org['description_points'] = []

    # Generate Cover Letter
    try:
        cover_letter = generate_cover_letter_text(refined_data)
    except Exception as e:
        cover_letter = "Maaf, gagal membuat cover letter otomatis. Silakan coba lagi."

    # --- 4. GENERATE PDF (ReportLab) ---
    
    # Buat nama file yang aman (hapus karakter aneh)
    safe_name = "".join([c for c in refined_data['full_name'] if c.isalnum() or c==' ']).strip()
    filename = f"cv_{safe_name.replace(' ', '_')}.pdf"
    full_path = os.path.join('static', filename)
    
    # Panggil fungsi generator PDF
    generate_ats_cv(refined_data, full_path)

    # --- 5. RENDER HASIL ---
    return render_template('result.html', 
                           pdf_url=filename, 
                           cover_letter=cover_letter)

@app.route('/download/<filename>')
def download_pdf(filename):
    """Route untuk download PDF"""
    file_path = os.path.join('static', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        return "File tidak ditemukan", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)