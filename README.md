# 🤖 kisanBot

![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)

An intelligent assistant for farmers, providing quick access to information on disease diagnosis, market analysis, and more. This bot leverages the Google AI platform to deliver accurate and timely support.

## 📋 Prerequisites

Before you begin, ensure you have the following:

* **Python 3.12** or higher.
* **A Google AI API Key**. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).

## 🚀 Installation & Setup

Follow these steps to get your development environment set up.

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/parassharm80/kisanBot.git](https://github.com/parassharm80/kisanBot.git)
    cd kisanBot
    ```

2.  **Create and Activate a Virtual Environment**

    * On **macOS/Linux**:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * On **Windows**:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install Required Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Your API Key**
    Create an environment variable for your Google AI API key. Replace `"YOUR_API_KEY_HERE"` with your actual key.

    * On **macOS/Linux**:
        ```bash
        export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```
    * On **Windows (Command Prompt)**:
        ```bash
        set GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```
    * On **Windows (PowerShell)**:
        ```bash
        $env:GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```
    > **Note:** This environment variable is only set for the current terminal session. For a permanent solution, add it to your shell's profile file (e.g., `.zshrc`, `.bash_profile`) or your system's environment variables on Windows.

## ▶️ How to Run

Once the setup is complete, you can run the application's test cases from the root directory:

```bash
python main.py