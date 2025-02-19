import os
import platform
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from groq import Groq


def find_mmdc_path():
    """Find the mmdc executable path based on the operating system."""
    if platform.system() == "Windows":
        return os.path.expanduser("~\\AppData\\Roaming\\npm\\mmdc.cmd")
    else:
        return "mmdc"


def check_mmdc_installed(mmdc_path):
    """Check if Mermaid CLI (mmdc) is installed and accessible."""
    if not os.path.exists(mmdc_path):
        messagebox.showerror(
            "Error",
            "Mermaid CLI (mmdc) not found!\nInstall it using: npm install -g @mermaid-js/mermaid-cli",
        )
        return False
    return True


def generate_mermaid_code(user_requirement, client):
    """Generate Mermaid flowchart code using Groq AI."""
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
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        mermaid_code = chat_completion.choices[0].message.content.strip()
        return mermaid_code.replace("```mermaid", "").replace("```", "").strip()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate Mermaid code.\n{str(e)}")
        return None


def save_and_generate_flowchart(mermaid_code, output_format, output_dir):
    """Save Mermaid code to a temporary file and generate the flowchart."""
    mmdc_path = find_mmdc_path()
    if not check_mmdc_installed(mmdc_path):
        return

    try:
        temp_dir = tempfile.gettempdir()
        mmd_file_path = os.path.join(temp_dir, "temp_flowchart.mmd")
        output_path = os.path.join(output_dir, f"flowchart.{output_format}")

        # Save Mermaid code to a temporary file
        with open(mmd_file_path, "w", encoding="utf-8") as mmd_file:
            mmd_file.write(mermaid_code)

        # Generate flowchart using mmdc
        result = subprocess.run(
            [mmdc_path, "-i", mmd_file_path, "-o", output_path, "-b", "transparent"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.returncode == 0:
            messagebox.showinfo("Success", f"Flowchart saved as: {output_path}")
        else:
            messagebox.showerror("Error", f"Failed to generate flowchart.\n{result.stderr}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate flowchart.\n{str(e)}")


def generate_flowchart(user_requirement, output_format, output_dir):
    """Generate a flowchart using Groq AI and Mermaid CLI."""
    client = Groq(api_key="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")
    mermaid_code = generate_mermaid_code(user_requirement, client)
    if mermaid_code:
        save_and_generate_flowchart(mermaid_code, output_format, output_dir)


def create_ui():
    """Create a simple UI for user interaction."""
    root = tk.Tk()
    root.title("Flowchart Generator")
    root.geometry("500x350")

    # Input description
    tk.Label(root, text="Enter Flowchart Description:", font=("Arial", 12)).pack(pady=5)
    text_input = tk.Text(root, height=4, width=50)
    text_input.pack(pady=5)

    # Output format selection
    tk.Label(root, text="Select Output Format:", font=("Arial", 12)).pack(pady=5)
    format_var = tk.StringVar(value="png")
    format_dropdown = ttk.Combobox(root, textvariable=format_var, values=["png", "svg", "pdf"], state="readonly")
    format_dropdown.pack(pady=5)

    # Output directory selection
    output_dir = tk.StringVar(value=os.getcwd())

    def select_output_dir():
        directory = filedialog.askdirectory()
        if directory:
            output_dir.set(directory)

    tk.Label(root, text="Select Output Directory:", font=("Arial", 12)).pack(pady=5)
    tk.Entry(root, textvariable=output_dir, state="readonly", width=40).pack(pady=5)
    tk.Button(root, text="Browse", command=select_output_dir).pack(pady=5)

    # Generate button
    def on_generate():
        user_requirement = text_input.get("1.0", tk.END).strip()
        if not user_requirement:
            messagebox.showwarning("Input Required", "Please enter a flowchart description.")
            return
        generate_flowchart(user_requirement, format_var.get(), output_dir.get())

    generate_button = tk.Button(
        root, text="Generate Flowchart", command=on_generate, font=("Arial", 12), bg="#4CAF50", fg="white"
    )
    generate_button.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    create_ui()