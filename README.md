# 🗳️ CART-Based Student Government Election Outcome Prediction System

An AI-powered full-stack web application that predicts student government election outcomes using the **CART (Decision Tree)** algorithm, with **Random Forest** comparison.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "c:\Users\LENOVO\Documents\DMA PROJECT"
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Open the Frontend

Open `frontend/index.html` in your browser.

> Default login: **admin** / **admin123**

---

## 🎯 Usage Flow

1. **Login** → `admin` / `admin123`
2. **Dashboard** → Click **Train Model** (uses sample data)
3. **New Prediction** → Enter candidate details → Get result
4. **Results** → Download PDF report
5. **Model Insights** → View confusion matrix, tree diagram, feature importance
6. **Dataset** → Upload your own CSV or download sample template

---

## 📡 API Endpoints

| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| POST   | `/auth/login`      | Login                    |
| POST   | `/auth/signup`     | Register                 |
| POST   | `/train-model`     | Train CART + RF          |
| POST   | `/predict`         | Predict election outcome |
| POST   | `/upload-dataset`  | Upload CSV               |
| GET    | `/model-metrics`   | Get evaluation metrics   |
| GET    | `/sample-data`     | Download sample CSV      |
| POST   | `/generate-report` | Download PDF report      |

**Swagger Docs:** http://127.0.0.1:8000/docs

---

## 🧩 Tech Stack

| Layer      | Technology                     |
|------------|--------------------------------|
| Frontend   | HTML5, CSS3, Vanilla JS (SPA)  |
| Backend    | FastAPI + Uvicorn              |
| ML         | scikit-learn (CART, RF)        |
| Viz        | Matplotlib, Seaborn            |
| PDF        | ReportLab                      |
| Persistence| joblib (model serialization)   |

---

## 📦 Project Structure

```
DMA PROJECT/
├── backend/
│   ├── main.py          # FastAPI app
│   ├── auth.py          # Authentication
│   ├── report.py        # PDF generator
│   └── ml/
│       ├── data_gen.py  # Sample dataset
│       ├── train.py     # Training pipeline
│       └── predict.py   # Prediction logic
├── frontend/
│   ├── index.html       # Main SPA
│   ├── css/styles.css   # Dark theme
│   └── js/
│       ├── app.js       # Router + state
│       ├── auth.js      # Login/signup
│       ├── dashboard.js # Dashboard page
│       ├── predict.js   # Predict page
│       └── insights.js  # Visualizations
├── requirements.txt
└── README.md
```
