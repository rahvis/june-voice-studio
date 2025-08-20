# Voice Cloning System — End-User Guide (Production)

## Overview
This guide explains how to use the Azure-first Voice Cloning System in production: enrolling a voice, generating speech, and managing your content.

## Prerequisites
- Valid account in the organization’s Azure Entra ID tenant
- Assigned role with permissions to use voice cloning features
- Stable network connection and a supported browser (latest Chrome/Edge)

## Login
1. Navigate to the production frontend URL provided by your administrator.
2. Sign in via the Microsoft login page (Entra ID).
3. If prompted, grant requested permissions.

## Enroll a Voice
1. Go to Voice Enrollment.
2. Provide consent by reading the consent statement and confirming.
3. Upload training audio per the requirements:
   - WAV, mono, 16 kHz or 24 kHz, < 10 minutes per file
   - Clear speech, minimal noise, no background music
4. Submit. Processing may take time; you will receive a status update on the Dashboard.
5. When training completes, your custom voice appears in the Voice Models list.

## Synthesize Speech
1. Go to Synthesis.
2. Select your custom voice.
3. Enter text or SSML.
4. Optionally enable translation and set target language.
5. Click Synthesize. Preview the audio and download as needed.

## Best Practices
- Keep texts concise; long passages should be broken into paragraphs.
- Use SSML for prosody, emphasis, and pauses.
- Respect licensing and consent constraints for all generated content.

## Data & Privacy
- Audio files are stored in Azure Blob Storage.
- Metadata resides in Azure Cosmos DB.
- Keys and secrets are in Azure Key Vault.
- Access is controlled via Azure Entra ID (RBAC).

## FAQs
- My model is stuck in training: check the Dashboard for errors or contact support.
- I hear artifacts in audio: re-upload higher quality samples and reduce background noise.
- I cannot see my voice: ensure you are in the correct tenant and have the required role.

## Support
For issues, follow the Support process detailed in `docs/support/README.md`.
