# CerebroCare360 🧠

> AI-powered brain tumor detection web platform using an ensemble of three deep learning models.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?style=flat-square)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-orange?style=flat-square)
![Ensemble Accuracy](https://img.shields.io/badge/Ensemble%20Accuracy-92.87%25-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Overview

CerebroCare360 is a full-stack medical AI web application that analyses brain MRI scans and classifies them into four categories — **Glioma**, **Meningioma**, **Pituitary Tumor**, and **No Tumor** — using a weighted ensemble of three convolutional neural networks.

The platform is designed for educational and research purposes and includes a clinical-grade neurological symptom checker, AI chatbot (CerebroBot), PDF report generation, and a hospital finder for specialist referrals.

---

## Features

- **MRI Upload & Analysis** — drag-and-drop MRI upload with real-time AI ensemble prediction
- **Ensemble Model** — weighted combination of VGG16, ResNet50, and EfficientNetB0 achieving 92.87% accuracy
- **Probability Breakdown** — per-class probability bars with confidence scoring
- **Low Confidence Warning** — automatic caution flag when model confidence is below 50%
- **PDF Report Generation** — downloadable A4 clinical report via ReportLab
- **Symptom Checker** — 6-screen neurological triage tool covering brain tumors, stroke, MS, dementia, movement disorders, migraine, and cluster headache — based on Harrison's Principles of Internal Medicine
- **CerebroBot** — AI chatbot powered by Groq (llama-3.1-8b-instant) for brain health queries
- **Hospital Finder** — search nearby neurological specialists by city and specialty
- **Admin Panel** — manage hospitals and symptom rules via a protected dashboard
- **Scan History** — searchable and filterable scan history per user
- **User Profiles** — account management with password change and scan statistics

---

## Model Performance

| Model | Val Accuracy |
|---|---|
| VGG16 | 93.69% |
| ResNet50 | 71.25% |
| EfficientNetB0 | 90.69% |
| **Ensemble (weighted)** | **92.87%** |

**Per-class F1 scores (ensemble):**

| Class | F1 Score | Precision | Recall |
|---|---|---|---|
| Glioma | 0.8812 | 0.9846 | 0.7975 |
| Meningioma | 0.9175 | 0.9175 | 0.9175 |
| No Tumor | 0.9547 | 0.9132 | 1.0000 |
| Pituitary | 0.9547 | 0.9132 | 1.0000 |

> Dataset: Masoud Nickparvar Brain Tumor MRI Dataset (Kaggle) — 5,608 training / 1,600 test images across 4 classes.

---

## Tech Stack

**Backend**
- Python 3.10+, Flask 3.0, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt, Flask-WTF, Flask-Migrate
- TensorFlow 2.15 / Keras — VGG16, ResNet50, EfficientNetB0
- SQLite (development) / PostgreSQL (production)
- ReportLab (PDF generation), Groq API (chatbot), Pillow (image processing)

**Frontend**
- Bootstrap 5 CDN, Bootstrap Icons
- DM Sans + Fraunces (Google Fonts)
- Custom CSS design system with CSS variables

**ML Training**
- Google Colab (T4 GPU)
- Two-stage training: frozen backbone → fine-tune last 20 layers
- EfficientNet-specific preprocessing fix (`preprocess_input` vs `rescale=1./255`)
- Class-weighted training, ReduceLROnPlateau, EarlyStopping, ModelCheckpoint

---

## Project Structure

```
CEREBROCARE_360/
├── run.py
├── .env
├── requirements.txt
├── models/
│   ├── vgg16_best.h5
│   ├── resnet50_best.h5
│   └── efficientnet_best.h5
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── user.py
│   │   ├── scan.py
│   │   ├── prediction.py
│   │   ├── report.py
│   │   ├── hospital.py
│   │   └── symptom_rule.py
│   ├── blueprints/
│   │   ├── auth/
│   │   ├── scan/
│   │   ├── report/
│   │   ├── hospital/
│   │   ├── symptom/
│   │   ├── admin/
│   │   └── chat/
│   ├── services/
│   │   ├── ai_service.py
│   │   ├── image_service.py
│   │   ├── report_service.py
│   │   └── gradcam_service.py
│   ├── static/
│   │   ├── uploads/
│   │   ├── reports/
│   │   └── heatmaps/
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── auth/
│       ├── scan/
│       ├── report/
│       ├── hospital/
│       ├── symptom/
│       ├── admin/
│       ├── chat/
│       └── errors/
└── migrations/
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- Groq API key (free at [console.groq.com](https://console.groq.com))
- Trained model `.h5` files (see Training section)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/cerebrocare360.git
cd cerebrocare360
```

### 2. Create virtual environment
```bash
python -m venv brain
# Windows
brain\Scripts\activate
# macOS / Linux
source brain/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root directory:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///cerebrocare.db
FLASK_ENV=development
GROQ_API_KEY=gsk_your_actual_key_here
TF_ENABLE_ONEDNN_OPTS=0
```

### 5. Place model files
Download or train the three models and place them in the `models/` folder:
```
models/
├── vgg16_best.h5
├── resnet50_best.h5
└── efficientnet_best.h5
```

### 6. Initialise the database
```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

### 7. Run the application
```bash
python run.py
```

Visit `http://127.0.0.1:5000`

---

## Training the Models

The ML training notebook is included at `CerebroCare360_Training.ipynb`.

Open it in **Google Colab** with a T4 GPU runtime.

**Important:** The notebook uses a two-stage training strategy and includes a critical preprocessing fix for EfficientNetB0 — it uses `preprocess_input` (range -1 to +1) rather than `rescale=1./255` (range 0 to 1), which was the root cause of EfficientNet previously being stuck at ~42% accuracy.

Run cells in order. All three models save automatically to Google Drive.

---

## Ensemble Weights

After training, update `app/services/ai_service.py`:

```python
_ensemble_weights = {
    'vgg16':        0.3665,
    'resnet50':     0.2787,
    'efficientnet': 0.3548
}
```

These weights are normalized from the individual validation accuracies so that better-performing models have proportionally more influence on the final prediction.

---

## Symptom Checker

The neurological symptom checker covers:
- Brain tumor red flags (glioma, meningioma, pituitary, vestibular schwannoma)
- Stroke / FAST protocol
- Subarachnoid hemorrhage
- Spinal cord compression
- Multiple sclerosis / optic neuritis
- Dementia (Alzheimer's, vascular, Lewy body)
- Parkinsonism and essential tremor
- Migraine, cluster headache, tension headache
- Post-concussion syndrome

Clinical logic is grounded in Harrison's Principles of Internal Medicine. The tool outputs urgency guidance only — it does not diagnose.

---

## Disclaimer

This application is built for **educational and research purposes only**. It is not a certified medical device and must not be used as a substitute for professional clinical diagnosis. All results should be reviewed by a qualified neurologist or radiologist.

---

## License

MIT License — see `LICENSE` for details.

---

## Acknowledgements

- Dataset: [Masoud Nickparvar — Brain Tumor MRI Dataset](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset) (Kaggle)
- Clinical reference: Harrison's Principles of Internal Medicine
- Chatbot: [Groq](https://groq.com) — llama-3.1-8b-instant