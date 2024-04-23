import sqlite3
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class GerenciadorConsultas:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Consultas Médicas")
        self.root.geometry("800x600")

        # Configurar o estilo do treeview
        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12))
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        # Configurar o banco de dados
        self.setup_db()

        # Componentes da interface gráfica
        self.setup_widgets()

    def setup_db(self):
        self.conn = sqlite3.connect("consultas.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultas (
                id INTEGER PRIMARY KEY, 
                data_consulta TEXT, 
                hora_consulta TEXT,
                paciente TEXT, 
                medico TEXT,
                status TEXT)
            """)
        self.conn.commit()

    def setup_widgets(self):
        # Frame para os botões
        frame_botoes = ttk.Frame(self.root)
        frame_botoes.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Botões para gerenciamento de consultas
        botao_agendar = ttk.Button(frame_botoes, text="Agendar Consulta", command=self.agendar_consulta)
        botao_agendar.pack(side=tk.LEFT, padx=10)
        botao_atualizar = ttk.Button(frame_botoes, text="Atualizar Consulta", command=self.atualizar_consulta)
        botao_atualizar.pack(side=tk.LEFT, padx=10)
        botao_anexar = ttk.Button(frame_botoes, text="Anexar Exame", command=self.anexar_exames)
        botao_anexar.pack(side=tk.LEFT, padx=10)
        botao_enviar_email = ttk.Button(frame_botoes, text="Enviar Email", command=self.enviar_email)
        botao_enviar_email.pack(side=tk.LEFT, padx=10)

        # Treeview para exibição de consultas
        self.tree = ttk.Treeview(self.root, columns=('ID', 'Data', 'Hora', 'Paciente', 'Médico', 'Status'), show='headings')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Data', text='Data')
        self.tree.heading('Hora', text='Hora')
        self.tree.heading('Paciente', text='Paciente')
        self.tree.heading('Médico', text='Médico')
        self.tree.heading('Status', text='Status')
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Data', width=100, anchor='center')
        self.tree.column('Hora', width=100, anchor='center')
        self.tree.column('Paciente', width=150, anchor='center')
        self.tree.column('Médico', width=150, anchor='center')
        self.tree.column('Status', width=100, anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self.editar_consulta)

        self.carregar_consultas()

    def carregar_consultas(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.cursor.execute("SELECT id, data_consulta, hora_consulta, paciente, medico, status FROM consultas"):
            self.tree.insert('', tk.END, values=row)

    def agendar_consulta(self):
        # Diálogo para inserir nova consulta
        data_consulta = simpledialog.askstring("Data da Consulta", "Informe a data da consulta:")
        hora_consulta = simpledialog.askstring("Hora da Consulta", "Informe a hora da consulta:")
        paciente = simpledialog.askstring("Paciente", "Nome do paciente:")
        medico = simpledialog.askstring("Médico", "Nome do médico:")
        if data_consulta and hora_consulta and paciente and medico:
            status = "Agendada"
            self.cursor.execute("INSERT INTO consultas (data_consulta, hora_consulta, paciente, medico, status) VALUES (?, ?, ?, ?, ?)", 
                                (data_consulta, hora_consulta, paciente, medico, status))
            self.conn.commit()
            self.carregar_consultas()  # Recarregar consultas

    def atualizar_consulta(self):
        item_selecionado = self.tree.selection()
        if item_selecionado:
            item = self.tree.item(item_selecionado)
            status = simpledialog.askstring("Status", "Informe o novo status da consulta:")
            if status:
                self.cursor.execute("UPDATE consultas SET status = ? WHERE id = ?", (status, item['values'][0]))
                self.conn.commit()
                self.carregar_consultas()  # Recarregar consultas

    def editar_consulta(self, event):
        item_selecionado = self.tree.selection()
        if item_selecionado:
            item = self.tree.item(item_selecionado)
            # Obter os valores atuais da consulta
            id_consulta = item['values'][0]
            data_consulta = item['values'][1]
            hora_consulta = item['values'][2]
            paciente = item['values'][3]
            medico = item['values'][4]
            # Diálogo para editar consulta
            nova_data = simpledialog.askstring("Editar Consulta", "Nova data da consulta:", initialvalue=data_consulta)
            nova_hora = simpledialog.askstring("Editar Consulta", "Nova hora da consulta:", initialvalue=hora_consulta)
            novo_paciente = simpledialog.askstring("Editar Consulta", "Novo nome do paciente:", initialvalue=paciente)
            novo_medico = simpledialog.askstring("Editar Consulta", "Novo nome do médico:", initialvalue=medico)
            if nova_data and nova_hora and novo_paciente and novo_medico:
                self.cursor.execute("UPDATE consultas SET data_consulta = ?, hora_consulta = ?, paciente = ?, medico = ? WHERE id = ?", 
                                    (nova_data, nova_hora, novo_paciente, novo_medico, id_consulta))
                self.conn.commit()
                self.carregar_consultas()  # Recarregar consultas

    def anexar_exames(self):
        item_selecionado = self.tree.selection()
        if item_selecionado:
            item = self.tree.item(item_selecionado)
            paciente = item['values'][3]
            self.criar_pasta_usuario(paciente)
            filename = filedialog.askopenfilename(initialdir="/", title="Selecione um arquivo",
                                              filetypes=(("jpeg files", "*.jpg"), ("all files", "*.*")))
            if filename:
                # Armazenar o caminho do arquivo para uso posterior no envio de email
                self.arquivo_anexo = filename
                simpledialog.messagebox.showinfo("Sucesso", "Exame anexado com sucesso!")

    def enviar_email(self):
        item_selecionado = self.tree.selection()
        if item_selecionado:
            item = self.tree.item(item_selecionado)
            destinatario = simpledialog.askstring("Enviar Email", "Informe o email do destinatário:")
            if destinatario and hasattr(self, 'arquivo_anexo'):
                msg = MIMEMultipart()
                msg['From'] = 'EMAIL DO USUARIO'
                msg['To'] = destinatario
                msg['Subject'] = "Exame Médico Anexado"
                
                body = "Segue anexo o exame médico."
                msg.attach(MIMEText(body, 'plain'))

                attachment = open(self.arquivo_anexo, "rb")
                
                p = MIMEBase('application', 'octet-stream')
                p.set_payload((attachment).read())
                encoders.encode_base64(p)
                
                p.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(self.arquivo_anexo))
                msg.attach(p)
                
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)  # Use o servidor SMTP adequado
                    server.starttls()
                    server.login(msg['From'], "SENHA DE LOGIN GMAIL")
                    text = msg.as_string()
                    server.sendmail(msg['From'], msg['To'], text)
                    server.quit()
                    simpledialog.messagebox.showinfo("Sucesso", "E-mail enviado com sucesso!")
                except Exception as e:
                    print("Erro ao enviar e-mail:", str(e))
                    simpledialog.messagebox.showerror("Erro", "Erro ao enviar e-mail. Verifique sua conexão com a internet e tente novamente.")
            else:
                messagebox.showwarning("Aviso", "Selecione um paciente e anexe um exame antes de enviar o e-mail.")
        else:
            messagebox.showwarning("Aviso", "Selecione uma consulta antes de enviar o e-mail.")

    def criar_pasta_usuario(self, usuario):
        if not os.path.exists(usuario):
            os.makedirs(usuario)

# O código abaixo para iniciar a GUI será descomentado no script final.
root = tk.Tk()
app = GerenciadorConsultas(root)
root.mainloop()
