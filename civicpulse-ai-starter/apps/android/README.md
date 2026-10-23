# Android app workspace

Create/open your Kotlin + Jetpack Compose project here in Android Studio.

## Required citizen flow
1. Photo picker/camera capture and preview.
2. Required location description; optional extra details.
3. Multipart POST to `/api/reports`.
4. Show report ID, AI category, preliminary severity, rationale, uncertainty and human-review note.
5. Allow status lookup only through a secure reference/authenticated flow in production.

## Networking
Use Retrofit/OkHttp or Ktor Client. Send multipart fields matching `docs/API_CONTRACT.md`.
The Android app must call the backend URL, never the AI provider directly. Never embed provider API keys in the APK.

For emulator access to a backend running on your development computer, Android Emulator commonly uses `http://10.0.2.2:8000` instead of `localhost`. A physical phone needs the computer's reachable LAN address and firewall configuration. Use HTTPS for deployed services.
