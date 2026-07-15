# PRD (Product Requirements Document)

# AI-Based Skin Lesion Classification & Risk Guidance Service

## 1. Problem & Goal

### Problem
Early detection of skin cancer significantly improves treatment outcomes, yet many people delay visiting a dermatologist because they are unsure whether a skin lesion is serious. Existing AI skin analysis services often provide only a classification result without practical follow-up guidance such as nearby hospitals or personalized care recommendations.

### Goal
Develop a web-based AI service that classifies skin lesion images into seven categories using a model trained on the HAM10000 dataset with **Google Cloud Vertex AI**. Based on the prediction and confidence level, the service provides appropriate follow-up guidance, including nearby dermatology clinics or hospitals, general skin care recommendations, and a downloadable PDF report summarizing the analysis.

---

## 2. Target User (Persona)

### Primary Persona
- Adults (18–60 years old) who notice unusual skin lesions or moles.
- Users who want a quick preliminary assessment before deciding whether to visit a dermatologist.
- Individuals interested in monitoring changes in skin lesions over time.

### Secondary Persona
- Users who want to keep personal skin lesion analysis records.
- Individuals living in areas where access to dermatology clinics is limited.

---

## 3. Value – Why Ours?

Unlike existing services that simply display an AI prediction, this service provides an **end-to-end user experience** by combining AI-based classification with practical decision support.

Key differentiators include:

- AI-powered classification using a Vertex AI model trained on the HAM10000 dataset.
- Image quality validation before prediction to reduce unreliable analyses.
- Confidence-based risk assessment instead of relying solely on the highest predicted class.
- Personalized follow-up guidance based on risk level.
- Nearby dermatology and hospital recommendations using location-based services.
- Downloadable PDF report for future reference or medical consultation.
- Personal analysis history for users who choose to save their results.

---

## 4. Must-have Features

### 1. User Authentication
- User registration and login
- Secure authentication using JWT
- Personal analysis history management

### 2. AI Skin Lesion Analysis
- Upload or capture a skin lesion image
- Automatic image quality validation
- Seven-class skin lesion classification using Vertex AI

### 3. Personalized Risk Guidance
- Confidence-aware risk assessment
- Nearby dermatology or hospital recommendations for high-risk cases
- General skin care guidance for low-risk cases

### 4. PDF Report Generation
- Generate a downloadable PDF containing:
  - Uploaded image
  - Prediction result
  - Class probabilities
  - Risk level
  - Recommended actions
  - Medical disclaimer

### 5. Analysis History
- Save analysis results (optional)
- View previous analyses
- Download previous PDF reports

---

## 5. User Stories

### User Story 1
**As a user**, I want to upload or capture a photo of my skin lesion so that the AI model can analyze it.

### User Story 2
**As a user**, I want the system to warn me if the uploaded image is blurry or unsuitable so that I can submit a better image.

### User Story 3
**As a user**, I want to receive a confidence-aware prediction and risk guidance instead of only a disease label.

### User Story 4
**As a user**, I want recommendations for nearby dermatology clinics or hospitals when the predicted risk is high.

### User Story 5
**As a user**, I want to download a PDF report summarizing my analysis for future reference or consultation with a healthcare professional.

### User Story 6
**As a registered user**, I want to review my previous analysis results so that I can monitor changes over time.

---

## 6. Out of Scope

The following features are intentionally excluded from the initial MVP:

- Medical diagnosis or treatment decisions by the AI system
- Real-time consultation with dermatologists
- Online appointment booking
- Prescription or medication recommendations
- Continuous monitoring using wearable devices
- Multi-lesion detection in a single image
- Automatic disease progression tracking across multiple visits
- Support for skin diseases outside the seven HAM10000 lesion categories
- Integration with Electronic Health Record (EHR) systems