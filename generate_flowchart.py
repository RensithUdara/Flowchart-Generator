import os
import platform
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox
from groq import Groq

def find_mmdc_path():
    """Find the mmdc executable path based on the operating system"""
    if platform.system() == "Windows":
        return os.path.expanduser("~\\AppData\\Roaming\\npm\\mmdc.cmd")
    else:
        return "mmdc"

def generate_flowchart(user_requirement, output_format):
    """
    Generate a flowchart using Groq AI and save it as an image following ISO 5807:1985 standards
    """
    mmdc_path = find_mmdc_path()
    if not os.path.exists(mmdc_path):
        messagebox.showerror("Error", "Mermaid CLI (mmdc) not found!\nInstall it using: npm install -g @mermaid-js/mermaid-cli")
        return
    
    client = Groq(api_key="your_api_key_here")
    
    prompt = f"""
    Create a Mermaid flowchart following ISO 5807:1985 standards for: {user_requirement}
    
    Rules:
    1. Start with 'flowchart TD'
    2. Use these symbols exactly:
       - Start/End: ([Text])
       - Process: [Text]
       - Decision: {{Text}}
       - Input/Output: [/Text/]
       - Subroutine: [[Text]]
    3. Use simple arrows: -->
    4. For labeled arrows use: -->|Label|
    5. No special characters in the arrows
    6. Keep labels simple and clear
    7. Each node should have a unique single-letter ID (A, B, C, etc.)
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Generate Mermaid flowchart code using standard symbols."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        mermaid_code = chat_completion.choices[0].message.content.strip()
        mermaid_code = mermaid_code.replace("```mermaid", "").replace("```", "").strip()
        
        temp_dir = tempfile.gettempdir()
        mmd_file_path = os.path.join(temp_dir, 'temp_flowchart.mmd')
        output_path = os.path.join(os.getcwd(), f"flowchart.{output_format}")
        
        with open(mmd_file_path, 'w', encoding='utf-8') as mmd_file:
            mmd_file.write(mermaid_code)
        
        result = subprocess.run([
            mmdc_path, '-i', mmd_file_path, '-o', output_path, '-b', 'transparent'
        ], capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            messagebox.showinfo("Success", f"Flowchart saved as: {output_path}")
        else:
            messagebox.showerror("Error", f"Failed to generate flowchart.\n{result.stderr}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate flowchart.\n{str(e)}")

def create_ui():
    """Create a simple UI for user interaction"""
    root = tk.Tk()
    root.title("Flowchart Generator")
    root.geometry("500x300")
    
    tk.Label(root, text="Enter Flowchart Description:", font=("Arial", 12)).pack(pady=5)
    text_input = tk.Text(root, height=4, width=50)
    text_input.pack(pady=5)
    
    tk.Label(root, text="Select Output Format:", font=("Arial", 12)).pack(pady=5)
    format_var = tk.StringVar(value="png")
    format_dropdown = ttk.Combobox(root, textvariable=format_var, values=["png", "svg", "pdf"], state="readonly")
    format_dropdown.pack(pady=5)
    
    def on_generate():
        user_requirement = text_input.get("1.0", tk.END).strip()
        if not user_requirement:
            messagebox.showwarning("Input Required", "Please enter a flowchart description.")
            return
        generate_flowchart(user_requirement, format_var.get())
    
    generate_button = tk.Button(root, text="Generate Flowchart", command=on_generate, font=("Arial", 12), bg="#4CAF50", fg="white")
    generate_button.pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    create_ui()
