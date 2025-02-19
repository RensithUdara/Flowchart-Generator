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
        logging.error(f"Failed to generate Mermaid code: {str(e)}")
        messagebox.showerror("Error", f"Failed to generate Mermaid code.\n{str(e)}")
        return None


def save_and_generate_flowchart(mermaid_code, output_format, output_dir, status_label, progress_bar):
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

        # Update UI
        status_label.config(text="Generating flowchart...")
        progress_bar.start()

        # Generate flowchart using mmdc
        result = subprocess.run(
            [mmdc_path, "-i", mmd_file_path, "-o", output_path, "-b", "transparent"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        progress_bar.stop()
        if result.returncode == 0:
            status_label.config(text=f"Flowchart saved as: {output_path}")
            messagebox.showinfo("Success", f"Flowchart saved as: {output_path}")
        else:
            status_label.config(text="Failed to generate flowchart.")
            messagebox.showerror("Error", f"Failed to generate flowchart.\n{result.stderr}")
    except Exception as e:
        logging.error(f"Failed to generate flowchart: {str(e)}")
        status_label.config(text="Failed to generate flowchart.")
        messagebox.showerror("Error", f"Failed to generate flowchart.\n{str(e)}")


def generate_flowchart(user_requirement, output_format, output_dir, status_label, progress_bar):
    """Generate a flowchart using Groq AI and Mermaid CLI."""
    api_key = os.getenv("GROQ_API_KEY") or simpledialog.askstring("API Key", "Enter your Groq API key:", show="*")
    if not api_key:
        messagebox.showwarning("API Key Required", "Please enter a valid Groq API key.")
        return

    try:
        client = Groq(api_key=api_key)
        mermaid_code = generate_mermaid_code(user_requirement, client)
        if mermaid_code:
            save_and_generate_flowchart(mermaid_code, output_format, output_dir, status_label, progress_bar)
    except Exception as e:
        logging.error(f"Failed to initialize Groq client: {str(e)}")
        messagebox.showerror("Error", f"Failed to initialize Groq client.\n{str(e)}")


def create_ui():
    """Create a simple UI for user interaction."""
    root = tk.Tk()
    root.title("Flowchart Generator")
    root.geometry("600x400")

    # Dark mode toggle
    dark_mode = tk.BooleanVar(value=False)

    def toggle_dark_mode():
        if dark_mode.get():
            root.configure(bg="#2d2d2d")
            for widget in root.winfo_children():
                widget.configure(bg="#2d2d2d", fg="#ffffff")
        else:
            root.configure(bg="#ffffff")
            for widget in root.winfo_children():
                widget.configure(bg="#ffffff", fg="#000000")

    # Tooltips
    def create_tooltip(widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.wm_overrideredirect(True)
        label = tk.Label(tooltip, text=text, bg="#ffffe0", relief="solid", borderwidth=1)
        label.pack()

        def show_tooltip(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def hide_tooltip(event):
            tooltip.withdraw()

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    # Input description
    tk.Label(root, text="Enter Flowchart Description:", font=("Arial", 12)).pack(pady=5)
    text_input = tk.Text(root, height=4, width=60)
    text_input.pack(pady=5)
    create_tooltip(text_input, "Describe the flowchart you want to generate.")

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
    tk.Entry(root, textvariable=output_dir, state="readonly", width=50).pack(pady=5)
    tk.Button(root, text="Browse", command=select_output_dir).pack(pady=5)

    # Status label and progress bar
    status_label = tk.Label(root, text="", font=("Arial", 10))
    status_label.pack(pady=5)
    progress_bar = ttk.Progressbar(root, mode="indeterminate", length=400)
    progress_bar.pack(pady=5)

    # Generate button
    def on_generate():
        user_requirement = text_input.get("1.0", tk.END).strip()
        if not user_requirement:
            messagebox.showwarning("Input Required", "Please enter a flowchart description.")
            return
        threading.Thread(
            target=generate_flowchart,
            args=(user_requirement, format_var.get(), output_dir.get(), status_label, progress_bar),
        ).start()

    generate_button = tk.Button(
        root, text="Generate Flowchart", command=on_generate, font=("Arial", 12), bg="#4CAF50", fg="white"
    )
    generate_button.pack(pady=20)

    # Dark mode toggle button
    ttk.Checkbutton(root, text="Dark Mode", variable=dark_mode, command=toggle_dark_mode).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    create_ui()