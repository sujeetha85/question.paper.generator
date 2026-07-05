"""
Question Paper Generator - Completely Standalone (No API Key Needed)
Uses Ollama for local AI - download once, use offline
"""
import sys
import json
import subprocess
import requests
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QTextEdit, QSpinBox, QComboBox, QPushButton, QCheckBox,
                             QFrame, QMessageBox, QFileDialog, QProgressBar, QDialog, QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

class GeneratorThread(QThread):
    progress_update = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, material, num_questions, difficulty, question_types):
        super().__init__()
        self.material = material
        self.num_questions = num_questions
        self.difficulty = difficulty
        self.question_types = question_types
    
    def run(self):
        try:
            self.progress_update.emit("Connecting to local AI (Ollama)...")
            
            # Check if Ollama is running
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code != 200:
                    raise Exception("Ollama not responding")
            except:
                self.error.emit(
                    "Ollama is not running!\n\n"
                    "Please:\n"
                    "1. Install Ollama from ollama.ai\n"
                    "2. Run: ollama pull mistral\n"
                    "3. Start Ollama\n"
                    "4. Try again"
                )
                return
            
            self.progress_update.emit("Crafting questions...")
            
            type_labels = {
                "mcq": "multiple choice (4 options A-D)",
                "short": "short answer (1-2 sentences)",
                "truefalse": "true or false",
                "fillblank": "fill in the blank"
            }
            type_list = ", ".join([type_labels.get(t, t) for t in self.question_types])
            
            prompt = f"""You are a question paper generator. Create exactly {self.num_questions} {self.difficulty} difficulty questions from this material.

QUESTION TYPES TO USE: {type_list}

MATERIAL:
{self.material}

INSTRUCTIONS:
- Return ONLY valid JSON, no other text
- Create {self.num_questions} questions
- Distribute question types evenly
- For MCQ: provide exactly 4 options (A, B, C, D)
- All answers must be from the material
- Include brief explanations

JSON FORMAT:
{{
  "questions": [
    {{
      "number": 1,
      "type": "mcq",
      "text": "question text here",
      "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
      "answer": "B",
      "explanation": "why this is correct"
    }}
  ]
}}

Generate the questions now:"""

            # Call Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception("Ollama generation failed")
            
            result = response.json()
            response_text = result.get("response", "")
            
            self.progress_update.emit("Processing results...")
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                raise Exception("Could not parse response")
            
            parsed = json.loads(json_match.group())
            questions = parsed.get("questions", [])
            
            if not questions:
                raise Exception("No questions generated")
            
            self.finished.emit({"questions": questions, "message": f"Generated {len(questions)} questions locally"})
        
        except Exception as e:
            self.error.emit(str(e))

class OllamaSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Setup Required - Ollama")
        self.setModal(True)
        self.setGeometry(100, 100, 500, 400)
        
        layout = QVBoxLayout()
        
        title = QLabel("Ollama Setup Required")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        info = QLabel(
            "This app uses Ollama for local AI (no internet API needed).\n\n"
            "Quick Setup:\n\n"
            "1. Download & Install Ollama\n"
            "   → Go to ollama.ai\n"
            "   → Download for your OS\n"
            "   → Run installer\n\n"
            "2. Download the AI Model\n"
            "   → Open Terminal/Command Prompt\n"
            "   → Run: ollama pull mistral\n"
            "   → Wait for download (~5GB)\n\n"
            "3. Keep Ollama Running\n"
            "   → Ollama app should be open\n"
            "   → Runs in background\n\n"
            "4. Start This App\n"
            "   → Click button below\n"
            "   → Ready to generate!"
        )
        info.setFont(QFont("Arial", 10))
        info.setWordWrap(True)
        layout.addWidget(info)
        
        button_layout = QHBoxLayout()
        open_btn = QPushButton("Open ollama.ai")
        open_btn.clicked.connect(lambda: __import__('webbrowser').open('https://ollama.ai'))
        ok_btn = QPushButton("I've Installed Ollama")
        ok_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class QuestionPaperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📝 Question Paper Generator - Offline")
        self.setGeometry(100, 100, 1200, 900)
        
        self.current_questions = []
        self.answer_key_revealed = False
        self.generator_thread = None
        
        # Check Ollama on startup
        if not self.check_ollama():
            dialog = OllamaSetupDialog(self)
            dialog.exec_()
        
        self.init_ui()
    
    def check_ollama(self):
        """Check if Ollama is running"""
        try:
            requests.get("http://localhost:11434/api/tags", timeout=2)
            return True
        except:
            return False
    
    def init_ui(self):
        """Initialize the user interface"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QHBoxLayout()
        
        # Left panel - Input
        left_panel = self.create_input_panel()
        
        # Right panel - Output
        right_panel = self.create_output_panel()
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
        main_widget.setLayout(main_layout)
    
    def create_input_panel(self):
        """Create the input panel"""
        panel = QFrame()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📚 Configuration")
        title_font = QFont("Arial", 14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Status
        status = QLabel("✓ Offline Mode - No API Key Needed")
        status.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(status)
        
        # Material input
        layout.addWidget(QLabel("Study Material:"))
        self.material_input = QTextEdit()
        self.material_input.setPlaceholderText("Paste your study notes here...")
        self.material_input.setText("Photosynthesis is the process by which green plants convert light energy into chemical energy. It has two stages: light-dependent reactions in the thylakoid membrane producing ATP and NADPH, and light-independent reactions (Calvin cycle) converting CO2 to glucose. The overall equation is 6CO2 + 6H2O + light → C6H12O6 + 6O2.")
        self.material_input.setMinimumHeight(150)
        layout.addWidget(self.material_input)
        
        # Number of questions
        layout.addWidget(QLabel("Number of Questions:"))
        num_layout = QHBoxLayout()
        self.num_questions = QSpinBox()
        self.num_questions.setMinimum(3)
        self.num_questions.setMaximum(15)
        self.num_questions.setValue(5)
        num_layout.addWidget(self.num_questions)
        num_layout.addStretch()
        layout.addLayout(num_layout)
        
        # Difficulty
        layout.addWidget(QLabel("Difficulty Level:"))
        diff_layout = QHBoxLayout()
        self.difficulty = QComboBox()
        self.difficulty.addItems(["Easy", "Medium", "Hard"])
        self.difficulty.setCurrentIndex(1)
        diff_layout.addWidget(self.difficulty)
        diff_layout.addStretch()
        layout.addLayout(diff_layout)
        
        # Question types
        layout.addWidget(QLabel("Question Types:"))
        self.question_types = {}
        types_layout = QVBoxLayout()
        for qtype, label in [("mcq", "Multiple Choice"), ("short", "Short Answer"), 
                             ("truefalse", "True/False"), ("fillblank", "Fill in the Blank")]:
            checkbox = QCheckBox(label)
            checkbox.setChecked(qtype in ["mcq", "short"])
            self.question_types[qtype] = checkbox
            types_layout.addWidget(checkbox)
        layout.addLayout(types_layout)
        
        # Generate button
        self.generate_btn = QPushButton("🚀 Generate Questions Locally")
        self.generate_btn.setFont(QFont("Arial", 11))
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5a6fd8, stop:1 #6a3f92);
            }
            QPushButton:disabled { opacity: 0.5; }
        """)
        self.generate_btn.clicked.connect(self.generate_questions)
        layout.addWidget(self.generate_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready (Local AI)")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_output_panel(self):
        """Create the output panel"""
        panel = QFrame()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📄 Results")
        title_font = QFont("Arial", 14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Questions
        layout.addWidget(QLabel("Questions:"))
        self.questions_output = QTextEdit()
        self.questions_output.setReadOnly(True)
        self.questions_output.setFont(QFont("Courier", 10))
        self.questions_output.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.questions_output)
        
        # Answer key seal
        self.key_seal = QFrame()
        seal_layout = QVBoxLayout()
        seal_label = QLabel("🔒 Answer Key - Sealed")
        seal_label.setFont(QFont("Arial", 12))
        seal_label.setAlignment(Qt.AlignCenter)
        seal_layout.addStretch()
        seal_layout.addWidget(seal_label)
        
        self.reveal_btn = QPushButton("Reveal Answers")
        self.reveal_btn.setMaximumWidth(200)
        self.reveal_btn.setStyleSheet("""
            QPushButton {
                background: #764ba2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #6a3f92; }
        """)
        self.reveal_btn.clicked.connect(self.reveal_answer_key)
        seal_layout.addWidget(self.reveal_btn)
        seal_layout.addStretch()
        self.key_seal.setLayout(seal_layout)
        self.key_seal.setStyleSheet("""
            QFrame {
                border: 2px dashed #764ba2;
                border-radius: 8px;
                background-color: rgba(118, 75, 162, 0.05);
                min-height: 150px;
            }
        """)
        layout.addWidget(self.key_seal)
        
        self.answer_key_output = QTextEdit()
        self.answer_key_output.setReadOnly(True)
        self.answer_key_output.setFont(QFont("Courier", 10))
        self.answer_key_output.setVisible(False)
        self.answer_key_output.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.answer_key_output)
        
        # Export buttons
        export_layout = QHBoxLayout()
        export_txt_btn = QPushButton("💾 Save as Text")
        export_txt_btn.clicked.connect(self.export_as_text)
        export_pdf_btn = QPushButton("📕 Save as PDF")
        export_pdf_btn.clicked.connect(self.export_as_pdf)
        
        export_layout.addWidget(export_txt_btn)
        export_layout.addWidget(export_pdf_btn)
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
        panel.setLayout(layout)
        return panel
    
    def generate_questions(self):
        """Generate questions using local AI"""
        material = self.material_input.toPlainText().strip()
        if not material:
            QMessageBox.warning(self, "Input Error", "Please paste some study material")
            return
        
        selected_types = [t for t, cb in self.question_types.items() if cb.isChecked()]
        if not selected_types:
            QMessageBox.warning(self, "Input Error", "Select at least one question type")
            return
        
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Generating locally...")
        self.answer_key_revealed = False
        self.questions_output.clear()
        self.answer_key_output.clear()
        
        self.generator_thread = GeneratorThread(
            material,
            self.num_questions.value(),
            self.difficulty.currentText().lower(),
            selected_types
        )
        self.generator_thread.progress_update.connect(self.update_progress)
        self.generator_thread.finished.connect(self.on_generation_finished)
        self.generator_thread.error.connect(self.on_generation_error)
        self.generator_thread.start()
    
    def update_progress(self, message):
        """Update progress message"""
        self.status_label.setText(message)
        self.progress_bar.setValue(min(self.progress_bar.value() + 20, 90))
    
    def on_generation_finished(self, data):
        """Handle generation completion"""
        self.current_questions = data["questions"]
        self.display_questions()
        self.generate_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText(f"✓ {data['message']}")
        
        QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))
    
    def on_generation_error(self, error):
        """Handle generation error"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("✗ Error")
        QMessageBox.critical(self, "Generation Error", f"Failed:\n{error}")
    
    def display_questions(self):
        """Display questions"""
        text = ""
        type_map = {"mcq": "MCQ", "short": "Short Answer", "truefalse": "True/False", "fillblank": "Fill Blank"}
        
        for q in self.current_questions:
            text += f"\n{'='*60}\n"
            text += f"Q{q['number']} [{type_map.get(q['type'], q['type'])}]\n"
            text += f"{'='*60}\n"
            text += f"{q['text']}\n"
            
            if q.get('options'):
                text += "\n"
                for option in q['options']:
                    text += f"  {option}\n"
            text += "\n"
        
        self.questions_output.setText(text)
        self.key_seal.setVisible(True)
        self.answer_key_output.setVisible(False)
    
    def reveal_answer_key(self):
        """Reveal answer key"""
        if self.answer_key_revealed:
            return
        
        text = "ANSWER KEY\n" + "="*60 + "\n\n"
        for q in self.current_questions:
            text += f"Q{q['number']}: {q['answer']}\n"
            if q.get('explanation'):
                text += f"   → {q['explanation']}\n"
            text += "\n"
        
        self.answer_key_output.setText(text)
        self.answer_key_output.setVisible(True)
        self.key_seal.setVisible(False)
        self.answer_key_revealed = True
    
    def export_as_text(self):
        """Export as text"""
        if not self.current_questions:
            QMessageBox.warning(self, "No Data", "Generate questions first")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Save", "", "Text Files (*.txt)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("QUESTION PAPER\n" + "="*60 + "\n\n")
                    
                    type_map = {"mcq": "MCQ", "short": "Short Answer", "truefalse": "True/False", "fillblank": "Fill Blank"}
                    for q in self.current_questions:
                        f.write(f"Q{q['number']} [{type_map.get(q['type'], q['type'])}]\n")
                        f.write(f"{q['text']}\n")
                        if q.get('options'):
                            f.write("\n")
                            for option in q['options']:
                                f.write(f"  {option}\n")
                        f.write("\n")
                    
                    f.write("\n" + "="*60 + "\n")
                    f.write("ANSWER KEY\n" + "="*60 + "\n\n")
                    for q in self.current_questions:
                        f.write(f"Q{q['number']}: {q['answer']}\n")
                        if q.get('explanation'):
                            f.write(f"   → {q['explanation']}\n")
                        f.write("\n")
                
                QMessageBox.information(self, "Success", f"Saved to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
    
    def export_as_pdf(self):
        """Export as PDF"""
        try:
            import reportlab
        except ImportError:
            QMessageBox.warning(self, "Missing Library", 
                              "PDF export requires reportlab.\n"
                              "Install with: pip install reportlab")
            return
        
        if not self.current_questions:
            QMessageBox.warning(self, "No Data", "Generate questions first")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Save", "", "PDF Files (*.pdf)")
        if filename:
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                
                doc = SimpleDocTemplate(filename, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                    fontSize=24, textColor=colors.HexColor('#667eea'), spaceAfter=30)
                
                story.append(Paragraph("Question Paper", title_style))
                
                type_map = {"mcq": "MCQ", "short": "Short Answer", "truefalse": "True/False", "fillblank": "Fill Blank"}
                
                for q in self.current_questions:
                    question_text = f"<b>Q{q['number']} [{type_map.get(q['type'], q['type'])}]</b><br/>{q['text']}"
                    story.append(Paragraph(question_text, styles['BodyText']))
                    
                    if q.get('options'):
                        for option in q['options']:
                            story.append(Paragraph(option, styles['BodyText']))
                    
                    story.append(Spacer(1, 0.2*inch))
                
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph("<b>ANSWER KEY</b>", styles['Heading2']))
                story.append(Spacer(1, 0.2*inch))
                
                for q in self.current_questions:
                    answer_text = f"<b>Q{q['number']}:</b> {q['answer']}"
                    if q.get('explanation'):
                        answer_text += f"<br/><i>→ {q['explanation']}</i>"
                    story.append(Paragraph(answer_text, styles['BodyText']))
                    story.append(Spacer(1, 0.1*inch))
                
                doc.build(story)
                QMessageBox.information(self, "Success", f"Saved to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

def main():
    app = QApplication(sys.argv)
    window = QuestionPaperApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
