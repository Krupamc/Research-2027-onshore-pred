# Wind-Informed Water-Quality Drone Research

## Use of Predicted Onshore Winds to Increase Autonomous Water Quality Drone Battery Efficiency in Barnegat Bay

A research project by Krupam Patel. I am working on predicting onshore winds and using those predictions to help a future water-quality drone make operating decisions.


I am not at the battery-testing part yet. The current release connects historical weather data, next-hour wind forecasts, and an experimental ranking of travel headings.
Use of Predicted Onshore Winds to Increase Autonomous Water Quality Drone Battery Efficiency in Barnegat Bay

## What are I yapping about?
There are three main parts:

- `MBB`: the buoy and shore receiver.
- `ML`: the weather preparation, forecasting models, and heading scorer.
- `website`: the FastAPI backend and website.

## Idea?
- MBB gets water data.
- Gets sent to website backend
- Backend uses ML to predict winds
- Displayed
- Uses this to predict which direction is most energy efficient

## Curent Status?
This release is a historical software prototype.
Forecast results are provisional while data-quality checks are completed. In particular, I am checking whether repeated observations or sequences were saved under different historical dates.
The demo running successfully does not prove the forecast evaluation is valid.


## Installation:
- Download/Clone the repository (if in Linux "git clone https://github.com/Krupamc/portfolio_website") 

### Docker (linux)
- Make sure docker is installed (this is not a docker guide. Check out their [https://docs.docker.com/engine/install/](docs)). - Open folder
  - Edit the .env file for what port you want the website run on. Edit the "FASTAPI_PORT" value (default is 8001)
<img width="1105" height="135" alt="image" src="https://github.com/user-attachments/assets/c9f94908-0da2-4b80-ad19-374937d18eaa" />

-Run docker compose up -d (-d flag is for detached mode or running in background. To watch for any errors, run without flag) 
  - If it does not work, try running it with "sudo in front of it.
  - To turn off, run docker compose down (-v flag will delete all of the containers fully. Does not delete the repo folder) 
<img width="1458" height="240" alt="image" src="https://github.com/user-attachments/assets/31c2365b-c8d9-421e-b2ab-635f9f4e94f9" />
- Navigate to your browser and then to http://127.0.0.1:8001 (or change the port or the numbers after the colon)
- TADA you are now running the website. (I would question why you would want to run a website of me, but you do you ig).

### Python (Windows/Mac):
- Make sure python is installed (this is not a python guide. Check out their [https://www.python.org/downloads/](docs)). - Open folder
- Unzip the folder.
- Open `CMD` on windows (type CMD) or open terminal in Mac.
- Do the command `cd` (change directory also known as a folder`) and move to where the unzipped folder is.
- Make a virtual environment `python -m venv env`
  - You can replace python with `python3` if it doesn't work. You can also change the name of the environment by replacing `env`
- Now we must activate the virtual environment. Run: `<env_name>\Scripts\activate.bat` (Make sure you use \'s and not /)
  - `source .venv/bin/activate` for mac
- Run: pip install -r requirements.txt to install from the list in requirements.txt.
- cd into the `app` folder
- Run  `uvicorn main:app --reload --port 8001` (can also change the port)
- Navigate to your browser and then to http://127.0.0.1:8001 (or change the port or the numbers after the colon)
- TADA you are now running the website. (I would question why you would want to run a website of me, but you do you ig).
