# AI Fitness & Health Analytics Platform

A full-stack fitness tracker that logs workouts, weight, and calories, and uses a machine learning model to recommend how much weight to lift next session.

Built with an Angular frontend, a FastAPI backend, MongoDB for storage, and a scikit-learn model for the workout recommendations. I built this to get hands-on experience combining a normal full-stack app with an actual ML pipeline, rather than just tacking a model onto some sample data.

## Live Application

Frontend: [AI Fitness Platform](https://ai-fitness-platform-zqca.onrender.com)

Backend API: [AI Fitness API](https://ai-fitness-api-dthc.onrender.com)

## Why I built this

Most beginner ML projects stop at "train a model, print the accuracy." I wanted to see the whole thing through — collect/prepare real training data, engineer features from it, train a model, and then actually wire that model into a working product with auth, a database, and a UI. This project is that end-to-end attempt.

## Features

### Authentication

- User registration and login
- JWT-based authentication
- Password hashing with Argon2
- Protected API endpoints
- User-specific workout and prediction data

### Workout Tracking

Users can log individual workouts with:

- Exercise
- Muscle group
- Sets
- Repetitions
- Weight
- Duration
- Date

The workout history can be viewed by training date, and individual workouts can be deleted.

### Exercise Suggestions

The workout form provides suggestions based on exercises already recorded by the user.

This is not a fixed list. When a user records a new exercise, it can become part of their future suggestions.

### Workout Weight Recommendations

The main ML feature of the application is the workout weight recommendation.

After selecting an exercise, the system uses the user's previous training history to estimate a suitable working weight for the next session.

The recommendation shows information such as:

- Current weight
- Previous weight
- ML prediction
- Recent best weight
- Recent average weight
- Model confidence
- Number of historical sessions

The final recommendation also goes through additional progression and safety checks before being returned.

### Calorie Predictions

Users can generate a calorie-burn prediction based on their fitness information.

Generated predictions are saved so that previous predictions can be viewed later.

### Weight Tracking

Users can record their body weight and view their weight history over time.

### Responsive Interface

The application works across desktop and mobile screen sizes.

On smaller screens, the desktop sidebar is replaced with a navigation drawer to make the application easier to use on mobile devices.

## The ML side

The recommendation model is a `RandomForestRegressor` (scikit-learn), trained offline and loaded via Joblib at request time — the backend doesn't retrain on the fly.

**Features (30 total)**, engineered from workout history rather than raw logs:

- Previous weight, volume, reps, and estimated 1RM
- Session-over-session deltas (weight, volume, reps, 1RM)
- Days since last session, session count
- Rolling averages and recent bests (weight, 1RM)
- Weight / volume / 1RM trend

**Pipeline:**

```
Workout History → Preprocessing → Feature Engineering
   → Random Forest Model → Predicted Weight
   → Progression & Safety Checks → Final Recommendation
```

## Architecture

```
                Angular Frontend
                       |
              REST API + JWT
                       |
                FastAPI Backend
                       |
        ┌──────────────┼──────────────┐
        │              │              │
     Auth          Workouts      Predictions
        │              │              │
        └──────────────┼──────────────┘
                       |
                    MongoDB
                       |
             ML Recommendation Engine
                       |
              Random Forest Model
```

## Tech stack

| Layer    | Tech                                               |
| -------- | -------------------------------------------------- |
| Frontend | Angular 22, TypeScript, Angular Router/Forms, RxJS |
| Backend  | Python 3.12, FastAPI, Uvicorn, Pydantic, PyMongo   |
| Database | MongoDB                                            |
| Auth     | JWT (PyJWT), Argon2                                |
| ML       | Pandas, scikit-learn, Joblib                       |

## Project Structure

```text
ai-fitness-platform/
│
├── backend/
│   └── app/
│       ├── auth/
│       ├── db/
│       ├── models/
│       ├── routes/
│       ├── schemas/
│       └── services/
│
├── data/
│   ├── weightlifting_721_workouts.csv
│   └── processed/
│       └── workout_progression_features.csv
│
├── docs/
│
├── frontend/
│   └── src/
│       └── app/
│           ├── core/
│           └── features/
│
├── ml/
│   ├── data_processing/
│   ├── train_model.py
│   ├── evaluate_model.py
│   ├── evaluate_recommendations.py
│   ├── inspect_recommendations.py
│   └── recommendation.py
│
├── models/
│   └── workout_weight_model.joblib
│
├── tests/
│
├── .env.example
├── .gitignore
└── README.md
```

The main directories are separated by responsibility. The backend contains the API and application logic, the frontend contains the Angular application, and the ml directory contains the data processing, training, and recommendation code.

The trained model and processed feature data are kept separately from the application code so that the model can be loaded by the backend without putting the training process directly into the API.

This is a high-level structure — not every Angular component or backend file is listed here, to keep the README readable.

## Getting Started

### Prerequisites

Make sure the following are installed:

- Python 3.12
- Node.js 24.15.0
- npm 10.9.8
- MongoDB

### Clone the Repository

```bash
git clone https://github.com/cbhavesh09/ai-fitness-platform.git
cd ai-fitness-platform
```

### Backend Setup

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
.\venv\Scripts\Activate.ps1
```

Install the required Python packages:

```bash
pip install -r backend\requirements.txt
```

#### Environment Variables

Create a `.env` file in the project root. The repository includes `.env.example` as a template:

```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=ai_fitness
JWT_SECRET=replace-with-a-real-secret
```

Update these values if you are using a different MongoDB setup. For example, `MONGODB_URI` can point to a local MongoDB instance or a hosted MongoDB database.

`JWT_SECRET` should be replaced with a secure secret before running the application, and the `.env` file should not be committed to Git.

#### Run the Backend

From the project root:

```bash
uvicorn backend.app.main:app --reload
```

The backend will normally be available at `http://127.0.0.1:8000`.

### Frontend Setup

Open another terminal and move into the frontend directory:

```bash
cd frontend
```

Install the frontend dependencies:

```bash
npm install
```

Start the Angular development server:

```bash
npm start
```

The frontend will normally be available at `http://localhost:4200`.

#### Production Build

To create a production build of the Angular application:

```bash
npm run build
```

The generated files are placed in the Angular `dist` directory.

## API

Routes are grouped under `/auth`, `/workouts`, and `/predictions`, covering things like:

- Login
- Create / fetch / delete workouts
- Workout summaries
- Exercise suggestions
- Working weight recommendations
- Calorie predictions + prediction history

All routes besides login/register require a valid JWT.

## Testing

Tested manually during development — Angular production builds, FastAPI endpoint checks with an authenticated client, and recommendation testing against real recorded workout history (including verifying the trained model actually gets the 30 features it expects).

## Deployment

Frontend and backend are deployed separately on Render, talking to each other over the REST API. Config (DB connection, JWT secret, etc.) is handled through environment variables in production.

## Current Limitations

There are a few areas of the project that could be improved:

- The workout recommendation model depends on having enough useful workout history for an exercise.
- Exercise names entered manually can vary in spelling or naming.
- The recommendation system focuses on working-weight progression rather than generating a complete workout program.
- Calorie predictions could be improved by using more activity and user data.
- Backend automated test coverage can be expanded.
- The application does not currently integrate with wearable fitness devices.

## Future Improvements

Some features I would like to explore in future versions include:

- Improving exercise name normalization and handling variations in exercise names
- Adding more detailed progress charts and long-term training analytics
- Improving the calorie prediction model with additional activity data
- Exploring additional machine learning models for comparison
- Expanding the workout recommendation system to suggest complete training programs
- Adding more detailed nutrition tracking
- Integrating wearable fitness devices
- Improving recommendation explanations
- Adding more automated backend tests
- Exploring automatic model retraining as more workout data becomes available

## Author

Bhavesh

This project was developed as a university-level full-stack and machine learning project to gain practical experience with Angular, FastAPI, MongoDB, authentication, data processing, and machine learning.
