# Repo-Contribution-Plugin

## How to run the plugin locally

### a. Download and extract the project

1. Click the green **Code** button on this GitHub repository and select **Download ZIP**.
2. Extract the ZIP file to a location on your computer.
3. You should have two main folders:  
   - `\frontend` → Chrome Extension  
   - `\backend` → FastAPI Backend
  
### b. Set up the Chrome Extension

1. Open **Google Chrome**.
2. Go to `chrome://extensions` in the address bar.
3. Turn on **Developer Mode** (toggle switch in the top-right).
4. Click **Load unpacked**.
5. Select the `\frontend` folder from the extracted project.
6. (Optional) Click the **pin icon** next to the extension to keep it visible on the toolbar.

### c. Set up the FastAPI Backend

1. Inside the `\backend` folder, create a new file named `.env` and add the following line inside it:

    ```env
      TOKEN="your_personal_github_token_here"
    ```
    
   For instructions on how to generate your personal access token visit [GitHub Docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic).

2. Open a terminal (Command Prompt or PowerShell) and navigate to the `\backend` folder:

   ```bash
    cd your_directory_path\backend
   ```

3. Create a virtual environment:
   
   ```bash
       python -m venv venv
    ```

4. Activate the virtual environment:

   ```bash
    venv\Scripts\activate  # On Windows
    ```
   ```bash
    source venv/bin/activate  # On Mac/Linux
    ```

5. Install dependencies:

    ```bash
      pip install -r requirements.txt
    ```

6. Start the FastAPI server:
   
    ```bash
      uvicorn main:app --reload
    ```
    
7. Once **"Application startup complete."** message appears, the Chrome Extension can be used. A `stats.csv` file is created in the `\backend` folder which will contain the metrics logged for each time the plugin is run. For future use, only steps `c.2`, `c.4` and `c.6` need to be repeated.
