import os
import platform
import subprocess
import tempfile
import threading
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from groq import Groq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="flowchart_generator.log",
)

def get_mmdc_path():
    """Determine the Mermaid CLI (mmdc) executable path based on the OS."""
    return os.path.expanduser("~\\AppData\\Roaming\\npm\\mmdc.cmd") if platform.system() == "Windows" else "mmdc"

def is_mmdc_installed(mmdc_path):
    """Check if mmdc is installed."""
    if not os.path.exists(mmdc_path):
        messagebox.showerror("Error", "Mermaid CLI (mmdc) not found!\nInstall it using: npm install -g @mermaid-js/mermaid-cli")
        return False
    return True

def generate_mermaid_code(user_input, client):
    """Generate Mermaid flowchart code using Groq AI."""
    prompt = f"""
    Create a Mermaid flowchart following ISO 5807:1985 standards for: {user_input}
    
    Rules:
    1. Start with 'flowchart TD'
    2. Use symbols: Start/End ([Text]), Process [Text], Decision {Text}, Input/Output [/Text/], Subroutine [[Text]]
    3. Use arrows: --> and -->|Label|
    4. Keep labels clear and simple
    5. Nodes should have single-letter unique IDs (A, B, C, etc.)
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Generate Mermaid flowchart code using standard symbols."},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        return response.choices[0].message.content.strip().replace("```mermaid", "").replace("```", "").strip()
    except Exception as e:
        logging.error(f"Error generating Mermaid code: {e}")
        messagebox.showerror("Error", f"Failed to generate Mermaid code.\n{e}")
        return None

def create_flowchart(mermaid_code, output_format, output_dir, status_label, progress_bar, root):
    """Generate and save the flowchart image using Mermaid CLI."""
    mmdc_path = get_mmdc_path()
    if not is_mmdc_installed(mmdc_path):
        return
    try:
        temp_file = os.path.join(tempfile.gettempdir(), "temp_flowchart.mmd")
        output_file = os.path.join(output_dir, f"flowchart.{output_format}")
        
        with open(temp_file, "w", encoding="utf-8") as file:
            file.write(mermaid_code)
        
        def update_status(text):
            root.after(0, lambda: status_label.config(text=text))
        
        update_status("Generating flowchart...")
        progress_bar.start()

        result = subprocess.run(
            [mmdc_path, "-i", temp_file, "-o", output_file, "-b", "transparent"],
            capture_output=True, text=True, encoding="utf-8",
        )
        progress_bar.stop()
        update_status(f"Flowchart saved as: {output_file}" if result.returncode == 0 else "Failed to generate flowchart.")
        if result.returncode != 0:
            messagebox.showerror("Error", f"Failed to generate flowchart.\n{result.stderr}")
    except Exception as e:
        logging.error(f"Flowchart generation error: {e}")
        messagebox.showerror("Error", f"Flowchart generation failed.\n{e}")

def handle_generate(user_input, output_format, output_dir, status_label, progress_bar, root):
    """Manage the flowchart generation workflow."""
    api_key = os.getenv("GROQ_API_KEY") or simpledialog.askstring("API Key", "Enter your Groq API key:", show="*")
    if not api_key:
        messagebox.showwarning("API Key Required", "Please enter a valid Groq API key.")
        return
    try:
        client = Groq(api_key=api_key)
        mermaid_code = generate_mermaid_code(user_input, client)
        if mermaid_code:
            create_flowchart(mermaid_code, output_format, output_dir, status_label, progress_bar, root)
    except Exception as e:
        logging.error(f"API error: {e}")
        messagebox.showerror("Error", f"Failed to connect to Groq.\n{e}")

def create_ui():
    """Build the graphical user interface."""
    root = tk.Tk()
    root.title("Flowchart Generator")
    root.geometry("600x400")
    
    tk.Label(root, text="Enter Flowchart Description:", font=("Arial", 12)).pack(pady=5)
    text_input = tk.Text(root, height=4, width=60)
    text_input.pack(pady=5)
    
    tk.Label(root, text="Select Output Format:", font=("Arial", 12)).pack(pady=5)
    format_var = tk.StringVar(value="png")
    format_dropdown = ttk.Combobox(root, textvariable=format_var, values=["png", "svg", "pdf"], state="readonly")
    format_dropdown.pack(pady=5)
    
    output_dir = tk.StringVar(value=os.getcwd())
    
    def select_directory():
        directory = filedialog.askdirectory()
        if directory:
            output_dir.set(directory)
    
    tk.Label(root, text="Select Output Directory:", font=("Arial", 12)).pack(pady=5)
    tk.Entry(root, textvariable=output_dir, state="readonly", width=50).pack(pady=5)
    tk.Button(root, text="Browse", command=select_directory).pack(pady=5)
    
    status_label = tk.Label(root, text="", font=("Arial", 10))
    status_label.pack(pady=5)
    progress_bar = ttk.Progressbar(root, mode="indeterminate", length=400)
    progress_bar.pack(pady=5)
    
    def on_generate():
        user_input = text_input.get("1.0", tk.END).strip()
        if not user_input:
            messagebox.showwarning("Input Required", "Please enter a flowchart description.")
            return
        threading.Thread(
            target=handle_generate,
            args=(user_input, format_var.get(), output_dir.get(), status_label, progress_bar, root),
        ).start()
    
    tk.Button(root, text="Generate Flowchart", command=on_generate, font=("Arial", 12), bg="#4CAF50", fg="white").pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    create_ui()