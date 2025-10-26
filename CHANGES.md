# Updated Configuration Summary

## Changes Made

### 1. API Service Updates
- **Switched from OpenAI to HKBU GenAI API**
  - Updated `.streamlit/secrets.toml` with HKBU GenAI credentials
  - API Key: `92a081c9-e293-40e2-8d7b-eb7dfb4e3c9e`
  - Endpoint: `https://genai.hkbu.edu.hk/api/v0/rest`

### 2. Email Service Implementation
- **Integrated Resend Email API**
  - API Key: `re_DQvDjCvy_7UeMMSuXLipU1FDkudrXbBmU`
  - From Address: `onboarding@resend.dev`
  - Created `services/alert_service.py` with email sending functionality

### 3. File Updates

#### `.streamlit/secrets.toml`
- Added MongoDB connection string
- Added HKBU GenAI API key and endpoint
- Added Resend API key and email from address

#### `config/api_keys.py`
- Updated functions to use HKBU GenAI instead of OpenAI
- Added Resend API key retrieval
- Added email from address retrieval

#### `services/ai_service.py`
- Updated to use HKBU GenAI API with requests library
- Replaced OpenAI SDK with direct API calls
- Uses `Ocp-Apim-Subscription-Key` header for authentication
- Removed OpenAI client initialization

#### `database/models.py`
- Added `update_alert_last_triggered()` function
- Recreated with all CRUD operations

#### `services/alert_service.py` (NEW)
- Email sending using Resend API
- HTML email templates with professional styling
- AI-generated email content integration
- Alert checking and triggering logic
- Stock statistics display in emails

#### `config/constants.py`
- Changed `OPENAI_MODEL` to `GENAI_MODEL`
- Updated model name to `gpt-4`

#### `requirements.txt`
- Removed `openai` package
- Added `requests` package

## Email Alert Format

The email alert includes:
- **Header**: Gradient purple header with alert title
- **Alert Badge**: Red warning badge
- **Alert Details**: Criteria and threshold information
- **Stock Information Box**:
  - Stock name and ticker
  - Current price (large, highlighted)
  - Statistics grid (Daily Change, Volume, P/E Ratio, Beta)
- **AI Analysis Section**: Personalized analysis from HKBU GenAI
- **Action Required**: Call-to-action for user
- **Footer**: Automated message disclaimer

## How Alert Emails Work

1. User creates an alert in the platform
2. System monitors stock data
3. When criteria is met, `check_alerts()` is called
4. AI generates personalized email content
5. Email is sent via Resend API to user's registered email
6. Alert last triggered timestamp is updated

## Alert Criteria Supported

- `price_above`: Price exceeds threshold
- `price_below`: Price drops below threshold
- `percent_change_daily`: Daily change exceeds threshold
- `volume_spike`: Volume exceeds threshold
- `rsi_overbought`: RSI above threshold
- `rsi_oversold`: RSI below threshold

## Next Steps

1. Run the application: `streamlit run app.py`
2. Register a new account (email will be used for alerts)
3. Create stock alerts in the "Email Alerts" page
4. Alerts will send emails when triggered
5. Check your email inbox for alert notifications
