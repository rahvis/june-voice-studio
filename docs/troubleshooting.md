# Troubleshooting Guide

## Login Issues
- Ensure you are using the correct tenant.
- Clear browser cache; try an incognito window.

## Enrollment Errors
- Audio format invalid: provide mono WAV at 16/24 kHz.
- Low SNR: record in a quiet environment.
- Consent missing: complete consent step first.

## Training Delays
- Check Function App queue length and App Insights traces.
- Verify storage availability and Cosmos DB RU usage.

## Synthesis Problems
- Distortion: lower input volume or normalize audio in preprocessing.
- Latency: verify Redis cache status and region proximity.

## API Errors
- 401/403: token expired or insufficient roles.
- 429: rate limit exceeded; retry with backoff.
- 5xx: check App Insights live metrics and logs.

## Where to Get Help
- See `docs/support/README.md` for raising tickets and escalation.
