#!/usr/bin/env python
import subprocess
import sys
import os
from pathlib import Path

def install_requirements(requirements_file="requirements.txt"):
    """Install packages from requirements.txt file"""
    try:
        # Check if requirements file exists
        if not os.path.exists(requirements_file):
            print(f"Error: Could not find {requirements_file}")
            sys.exit(1)
            
        print(f"Installing packages from {requirements_file}...")
            
        # Run pip install with the requirements file
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ])
        
        print("\nAll packages installed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to install packages: {e}")
        sys.exit(1)

def create_directory_structure():
    """Create the basic directory structure for the project"""
    # Directories to create
    directories = ["output"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")

def create_example_env():
    """Create an example .env file if it doesn't exist"""
    env_file = Path(".env.example")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write("""# API Keys
GROQ_API_KEY=your_groq_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# LLM Settings
LLM_PROVIDER=groq/llama-3.1-8b-instant
LLM_TEMPERATURE=0.04
LLM_MAX_TOKENS=2000

# Scraping Settings
BROKER_NAME=YourHouse
AREA=utrecht
OUTPUT_DIR=output

# Debug Settings
DEBUG=False
""")
        print("Created .env.example file - rename to .env and add your API keys")

if __name__ == "__main__":
    print("Setting up Property Scraper...\n")
    
    # Create directory structure
    create_directory_structure()
    
    # Create example .env file
    create_example_env()
    
    # Install requirements
    install_requirements()
    
    print("\nSetup complete! You can now run: python crawlai.py --help")