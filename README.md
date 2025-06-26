# Repo-Contribution-Plugin

## How to run the project locally

### a. Download and extract the project

1. Click the green **Code** button on the GitHub repository and select **Download ZIP**.
2. Extract the ZIP file to a location on your computer.
3. You should see two main folders:  
   - `frontend/` → Chrome Extension  
   - `backend/` → FastAPI Backend
  
### b. Set up the Chrome Extension

1. Open **Google Chrome**.
2. Go to `chrome://extensions/` in the address bar.
3. Turn on **Developer Mode** (toggle switch in the top-right).
4. Click **Load unpacked**.
5. Select the `frontend/` folder from the extracted project.
6. (Optional) Click the **pin icon** next to the extension to keep it visible on the toolbar.

### c. Set up the FastAPI Backend

1. Add a `.env` file
   
Inside the `backend/` folder, create a new file named `.env` and add the following line inside it:

 ```env
   TOKEN="your_personal_github_token_here"
 ```
For instructions on how to generate your personal access token visit [GitHub Docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic).

2. Set up a virtual environment
   
Open a terminal (Command Prompt or PowerShell), then run:

```bash
    cd backend
    python -m venv venv
    venv\Scripts\activate  # On Windows
    source venv/bin/activate  # On Mac/Linux
 ```

3. Install dependencies

 ```bash
   pip install -r requirements.txt
 ```

4. Start the FastAPI server

 ```bash
   uvicorn main:app --reload
 ```
