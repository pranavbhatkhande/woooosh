# woooosh — Agent Notes

Native Android app (Kotlin + Jetpack Compose + Material 3 + Room).

## Version Bumping
- Bump `versionName`/`versionCode` in `app/build.gradle.kts` when landing a feature branch to `main`
- Format: semantic versioning (major.minor.patch)

## Build
- `./gradlew assembleDebug` — CI (`.github/workflows/android.yml`) builds every push and uploads the APK artifact
- Note: Google's artifact hosts (dl.google.com) are blocked in some sandboxes; rely on CI for compile verification when local resolution fails
