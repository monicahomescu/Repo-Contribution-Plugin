# Repo-Contribution-Plugin

Details on the project’s objectives, background and methodology can be found in the full report [here](https://github.com/monicahomescu/Repo-Contribution-Plugin/blob/main/Report.pdf).

<img width="100%" height="100%" src="" width="80%">

## How to run the plugin locally

Download and extract ZIP or clone the project by running:
   ```bash
   git clone https://github.com/monicahomescu/Repo-Contribution-Plugin.git
   ```
You will have two main folders:  
   - `\frontend` → Chrome Extension  
   - `\backend` → FastAPI Backend
  
### a. Set up the Chrome Extension

1. Open **Google Chrome**.
2. Go to `chrome://extensions` in the address bar.
3. Turn on **Developer Mode** (toggle switch in the top-right).
4. Click **Load unpacked**.
5. Select the `\frontend` folder from the project.
6. (Optional) Click the **pin icon** next to the extension to keep it visible on the toolbar.

### b. Set up the FastAPI Backend

1. Inside the `\backend` folder, create a new file named `.env` and add the following line inside it:

    ```env
    TOKEN="your_personal_github_token_here"
    ```
    
   For instructions on how to generate your personal access token visit [GitHub Docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic).

2. Open a terminal and navigate to the `\backend` folder:

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
    
7. Once the **"Application startup complete."** message appears, the Chrome Extension can be used. A `stats.csv` file is created in the `\backend` folder which will contain the metrics logged for each time the plugin is run. For future use, only steps `b.2`, `b.4` and `b.6` need to be repeated.
