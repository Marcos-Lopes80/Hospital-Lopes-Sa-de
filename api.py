import os
from flask import Flask, request, jsonify

from database.database_manager import SessionLocal
from database.models import Patient, Doctor, Appointment, MedicalExam, User # <-- Adicionado User
from vector_store.vector_manager import VectorManager
from llm_services.gemini_service import GeminiChatService
from llm_services.openai_service import OpenAIChatService

# --- Funções de Inicialização ---
def create_initial_user():
    """
    Cria o usuário administrador inicial se ele não existir.
    """
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter_by(username='adm').first()
        if not admin_user:
            print("Criando usuário administrador inicial para a API...")
            new_admin = User(
                username='adm',
                name='Dr Marcos Lopes',
                role='admin'
            )
            new_admin.set_password('123456')
            db.add(new_admin)
            db.commit()
            print("Usuário 'adm' criado com sucesso.")
    finally:
        db.close()

# --- Inicialização da Aplicação ---
app = Flask(__name__)

# Inicializa os módulos de IA
vector_manager = VectorManager()
gemini_chat_service = GeminiChatService()
openai_chat_service = OpenAIChatService()

# Cria o usuário admin e indexa os documentos ao iniciar a API
create_initial_user()
print("Inicializando e indexando exames médicos para a API...")
vector_manager.index_medical_exams()
print("Indexação concluída para a API.")

HOSPITAL_NAME = "Vinsaura Saúde"

# --- Endpoints da API ---

@app.route('/')
def home():
    return jsonify({"hospital_name": HOSPITAL_NAME, "message": "Bem-vindo à API do Sistema de Gerenciamento Hospitalar com IA!"})

# --- Endpoint de Autenticação ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "'username' e 'password' são obrigatórios."}), 400

    username = data['username']
    password = data['password']

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            # Em um sistema real, aqui você geraria um token (JWT)
            return jsonify({
                "message": "Login bem-sucedido!",
                "user": {
                    "username": user.username,
                    "name": user.name,
                    "role": user.role
                }
            })
        else:
            return jsonify({"error": "Credenciais inválidas."}), 401
    finally:
        db.close()

# --- Endpoints de Dados (a serem protegidos) ---

@app.route('/api/search', methods=['GET'])
def search_exams():
    # TODO: Proteger este endpoint
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Parâmetro 'q' (query) é obrigatório."}), 400

    similar_exams = vector_manager.search_similar_exams(query)
    results = []
    for exam in similar_exams:
        results.append({
            "exam_id": exam["exam_id"],
            "original_text_snippet": exam["original_text"][:200] + "...",
            "score": round(exam["score"], 4)
        })
    return jsonify({"query": query, "results": results})

@app.route('/api/summarize', methods=['GET'])
def summarize_patient_history():
    # TODO: Proteger este endpoint
    patient_name = request.args.get('patient_name')
    llm_service_choice = request.args.get('service', 'gemini').lower()

    if not patient_name:
        return jsonify({"error": "Parâmetro 'patient_name' é obrigatório."}), 400

    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.name.ilike(f"%{patient_name}%")).first()
        if not patient:
            return jsonify({"error": f"Paciente '{patient_name}' não encontrado."}), 404

        history_text = f"Histórico do Paciente: {patient.name} (Nasc: {patient.date_of_birth.strftime('%Y-%m-%d')})\n"
        # ... (lógica para construir o histórico)
        appointments = db.query(Appointment).filter_by(patient_id=patient.id).all()
        for appt in appointments:
            history_text += f"\n  Consulta em {appt.appointment_date.strftime('%Y-%m-%d')} com Dr. {appt.doctor.name}: {appt.description}\n"
            for exam in appt.exams:
                history_text += f"    - Exame: {exam.exam_type}\n      Resultados: {exam.results}\n      Plano: {exam.treatment_plan}\n"

        summary = ""
        if llm_service_choice == 'gemini':
            summary = gemini_chat_service.summarize_text(history_text)
        elif llm_service_choice == 'openai':
            summary = openai_chat_service.summarize_text(history_text)
        else:
            return jsonify({"error": "Serviço de LLM inválido. Escolha 'gemini' ou 'openai'."}), 400

        return jsonify({"patient_name": patient.name, "llm_service_used": llm_service_choice, "summary": summary})
    finally:
        db.close()

@app.route('/api/patients', methods=['GET'])
def list_patients():
    # TODO: Proteger este endpoint
    db = SessionLocal()
    try:
        patients = db.query(Patient).all()
        patient_list = []
        for p in patients:
            patient_list.append({"id": p.id, "name": p.name, "date_of_birth": p.date_of_birth.strftime('%Y-%m-%d') if p.date_of_birth else None})
        return jsonify({"patients": patient_list})
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)
