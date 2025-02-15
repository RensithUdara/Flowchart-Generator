import os
from groq import Groq
import subprocess
import tempfile
import platform

def find_mmdc_path():
    """Find the mmdc executable path based on the operating system"""
    if platform.system() == "Windows":
        return os.path.expanduser("~\\AppData\\Roaming\\npm\\mmdc.cmd")
    else:
        return "mmdc"

def generate_flowchart_with_image(user_requirement, output_format='png'):
    """
    Generate a flowchart using Groq AI and save it as an image following ISO 5807:1985 standards
    """
    mmdc_path = find_mmdc_path()
    if not os.path.exists(mmdc_path):
        print("Error: Mermaid CLI (mmdc) not found!")
        print("Please install it using: npm install -g @mermaid-js/mermaid-cli")
        return
    
    # Initialize Groq client
    client = Groq(
        api_key="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"
    )
    
    example_flowchart = """flowchart TD
    A([Start]) --> B[/Input Data/]
    B --> C[Process Data]
    C --> D{Decision?}
    D -->|Yes| E[/Output Result/]
    D -->|No| F[[Subroutine]]
    F --> C
    E --> G([End])"""
    
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
    
    Example format:
    flowchart TD
        A([Start]) --> B[/Input/]
        B --> C[Process]
        C --> D{{Decision}}
    """

    try:
        # Get Mermaid code from Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Generate Mermaid flowchart code using standard symbols. Use only basic arrows (--> or -->|label|) without any special characters."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        # Get the raw Mermaid code and clean it
        mermaid_code = chat_completion.choices[0].message.content.strip()
        
        # Remove any markdown code blocks if present
        mermaid_code = mermaid_code.replace("```mermaid", "").replace("```", "").strip()
        
        # Add styling
        style_definitions = """

classDef process fill:#fff,stroke:#333,stroke-width:2px;
classDef decision fill:#fff,stroke:#333,stroke-width:2px;
classDef io fill:#fff,stroke:#333,stroke-width:2px;
classDef terminal fill:#fff,stroke:#333,stroke-width:2px,rx:10;

class A,Z terminal;
class B,I io;
class C,E,G,H process;
class D,F decision;"""
        
        mermaid_code += style_definitions
        
        # Create temporary files
        temp_dir = tempfile.gettempdir()
        mmd_file_path = os.path.join(temp_dir, 'temp_flowchart.mmd')
        output_path = os.path.join(os.getcwd(), f"flowchart.{output_format}")
        
        # Write mermaid code to temporary file with UTF-8 encoding
        with open(mmd_file_path, 'w', encoding='utf-8') as mmd_file:
            mmd_file.write(mermaid_code)
        
        print("\nGenerated Flowchart Code:")
        print("--------------------------")
        print(mermaid_code)
        print("--------------------------")
        
        # Generate image using mermaid-cli
        try:
            result = subprocess.run([
                mmdc_path,
                '-i', mmd_file_path,
                '-o', output_path,
                '-b', 'transparent'
            ], capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode != 0:
                print(f"\nError running mmdc: {result.stderr}")
            else:
                print(f"\nFlowchart saved as: {output_path}")
            
        except Exception as e:
            print(f"\nError generating image: {str(e)}")
            print("Please ensure Mermaid CLI is properly installed")
        finally:
            # Clean up temporary file
            try:
                os.remove(mmd_file_path)
            except:
                pass
            
    except Exception as e:
        print(f"Error generating flowchart: {str(e)}")

def main():
    print("Standard Flowchart Generator")
    print("==========================")
    
    user_requirement = input("\nDescribe the process for the flowchart: ")
    
    print("\nOutput formats:")
    print("1. PNG")
    print("2. SVG")
    print("3. PDF")
    format_choice = input("Choose format (1-3, default is 1): ")
    
    format_map = {'1': 'png', '2': 'svg', '3': 'pdf'}
    output_format = format_map.get(format_choice, 'png')
    
    generate_flowchart_with_image(user_requirement, output_format)

if __name__ == "__main__":
    main()
