from database.database_manager import engine, Base, SessionLocal
from database.models import Patient, Doctor, Appointment, MedicalExam, User # <-- Adicionado User
from vector_store.vector_manager import VectorManager
from llm_services.gemini_service import GeminiChatService
from llm_services.openai_service import OpenAIChatService
import datetime
import os

def create_database_tables():
    """
    Cria todas as tabelas no banco de dados que ainda não existem.
    """
    print("Verificando e criando tabelas do banco de dados...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas com sucesso (se necessário).")
    except Exception as e:
        print(f"Ocorreu um erro ao criar as tabelas: {e}")

def populate_database_with_sample_data():
    """
    Popula o banco de dados com dados fictícios.
    """
    db = SessionLocal()
    try:
        if db.query(Patient).count() == 0:
            print("Banco de dados vazio. Populando com dados fictícios...")
            # ... (código de popular o banco de dados - omitido por brevidade)
            dr_ana = Doctor(name="Dr. Ana Silva", specialty="Cardiologia")
            dr_carlos = Doctor(name="Dr. Carlos Souza", specialty="Neurologia")
            dr_leticia = Doctor(name="Dr. Letícia Martins", specialty="Ortopedia")
            joao = Patient(name="João Pereira", date_of_birth=datetime.datetime(1985, 5, 20))
            maria = Patient(name="Maria Fernandes", date_of_birth=datetime.datetime(1992, 9, 15))
            pedro = Patient(name="Pedro Gonçalves", date_of_birth=datetime.datetime(1978, 1, 30))
            db.add_all([dr_ana, dr_carlos, dr_leticia, joao, maria, pedro])
            db.commit()
            consulta1 = Appointment(patient_id=joao.id, doctor_id=dr_ana.id, appointment_date=datetime.datetime(2023, 10, 25), description="Check-up anual, paciente relata cansaço.")
            db.add(consulta1)
            db.commit()
            exame1 = MedicalExam(appointment_id=consulta1.id, exam_type="Eletrocardiograma", file_path="/exames_ficticios/joao_ecg_20231025.pdf", results="Ritmo sinusal normal, sem anomalias significativas.", treatment_plan="Recomenda-se atividade física regular e dieta balanceada. Retorno em 1 ano.")
            consulta2 = Appointment(patient_id=maria.id, doctor_id=dr_carlos.id, appointment_date=datetime.datetime(2023, 11, 5), description="Paciente queixa-se de dores de cabeça frequentes.")
            db.add(consulta2)
            db.commit()
            exame2 = MedicalExam(appointment_id=consulta2.id, exam_type="Tomografia Computadorizada do Crânio", file_path="/exames_ficticios/maria_tc_cranio_20231105.pdf", results="Nenhuma evidência de anormalidades intracranianas.", treatment_plan="Prescrito analgésico para dores de cabeça. Observar e retornar se os sintomas persistirem ou piorarem.")
            consulta3 = Appointment(patient_id=pedro.id, doctor_id=dr_leticia.id, appointment_date=datetime.datetime(2023, 11, 10), description="Dor no joelho direito após atividade física.")
            db.add(consulta3)
            db.commit()
            exame3 = MedicalExam(appointment_id=consulta3.id, exam_type="Ressonância Magnética do Joelho", file_path="/exames_ficticios/pedro_rm_joelho_20231110.pdf", results="Leve estiramento do ligamento colateral medial. Sem ruptura.", treatment_plan="Fisioterapia por 4 semanas e aplicação de gelo. Evitar esportes de impacto por 2 meses.")
            db.add_all([exame1, exame2, exame3])
            db.commit()
            print("Dados fictícios adicionados com sucesso!")
    finally:
        db.close()

def create_initial_user():
    """
    Cria o usuário administrador inicial se ele não existir.
    """
    db = SessionLocal()
    try:
        # Verifica se o usuário 'adm' já existe
        admin_user = db.query(User).filter_by(username='adm').first()
        if not admin_user:
            print("Criando usuário administrador inicial...")
            new_admin = User(
                username='adm',
                name='Dr Marcos Lopes',
                role='admin'
            )
            new_admin.set_password('123456') # A senha será hasheada pelo método no modelo
            db.add(new_admin)
            db.commit()
            print("Usuário 'adm' criado com sucesso.")
    finally:
        db.close()

def main_cli(vector_manager, gemini_chat_service, openai_chat_service):
    # ... (código da CLI existente sem alterações)
    current_chat_service = gemini_chat_service
    print(f"Serviço de sumarização atual: {'Gemini' if current_chat_service == gemini_chat_service else 'OpenAI'}")
    while True:
        print("\n--- Sistema de Gerenciamento Hospitalar com IA ---")
        print("1. Buscar exames por similaridade (Busca Semântica)")
        print("2. Gerar resumo do histórico de um paciente")
        print("3. Listar todos os pacientes")
        print("4. Selecionar Serviço de LLM para Sumarização")
        print("5. Sair")
        choice = input("Escolha uma opção: ")
        if choice == '1':
            query = input("Digite o sintoma, diagnóstico ou termo que deseja buscar: ")
            similar_exams = vector_manager.search_similar_exams(query)
            if similar_exams:
                print(f"\n--- Resultados da busca para '{query}' ---")
                for exam in similar_exams:
                    print(f"  - ID do Exame: {exam['exam_id']} (Similaridade: {exam['score']:.2f})")
                    print(f"    Texto: '{exam['original_text'][:200]}...'")
            else:
                print("Nenhum exame similar encontrado.")
        elif choice == '2':
            patient_name = input("Digite o nome do paciente para gerar o resumo: ")
            db = SessionLocal()
            try:
                patient = db.query(Patient).filter(Patient.name.ilike(f"%{patient_name}%")).first()
                if patient:
                    history_text = f"Histórico do Paciente: {patient.name} (Nasc: {patient.date_of_birth.strftime('%Y-%m-%d')})\n"
                    appointments = db.query(Appointment).filter_by(patient_id=patient.id).all()
                    for appt in appointments:
                        history_text += f"\n  Consulta em {appt.appointment_date.strftime('%Y-%m-%d')} com Dr. {appt.doctor.name}: {appt.description}\n"
                        for exam in appt.exams:
                            history_text += f"    - Exame: {exam.exam_type}\n      Resultados: {exam.results}\n      Plano: {exam.treatment_plan}\n"
                    print(f"\nGerando resumo para {patient.name} usando {'Gemini' if current_chat_service == gemini_chat_service else 'OpenAI'}...\")
                    summary = current_chat_service.summarize_text(history_text)
                    print("\n--- Resumo do Histórico ---")
                    print(summary)
                else:
                    print(f"Paciente '{patient_name}' não encontrado.")
            finally:
                db.close()
        elif choice == '3':
            db = SessionLocal()
            try:
                patients = db.query(Patient).all()
                print("\n--- Lista de Pacientes ---")
                for p in patients:
                    print(f"  - ID: {p.id}, Nome: {p.name}")
            finally:
                db.close()
        elif choice == '4':
            print("\n--- Selecionar Serviço de LLM para Sumarização ---")
            print("1. Google Gemini")
            print("2. OpenAI (ChatGPT)")
            llm_choice = input("Escolha o serviço de LLM: ")
            if llm_choice == '1':
                current_chat_service = gemini_chat_service
                print("Serviço de sumarização alterado para Google Gemini.")
            elif llm_choice == '2':
                current_chat_service = openai_chat_service
                print("Serviço de sumarização alterado para OpenAI (ChatGPT).")
            else:
                print("Opção inválida. Mantendo o serviço atual.")
        elif choice == '5':
            print("Saindo do sistema. Até logo!")
            break
        else:
            print("Opção inválida. Por favor, tente novamente.")

if __name__ == "__main__":
    print("Iniciando o Sistema de Gerenciamento Hospitalar com IA...")
    create_database_tables()
    populate_database_with_sample_data()
    create_initial_user() # <-- Chamada para criar o usuário adm

    print("\n--- Inicializando Módulos de IA ---")
    vector_manager = VectorManager()
    vector_manager.index_medical_exams()
    gemini_chat_service = GeminiChatService()
    openai_chat_service = OpenAIChatService()

    # Inicia a interface de linha de comando
    main_cli(vector_manager, gemini_chat_service, openai_chat_service)
