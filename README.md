# woooosh

A native Android todo app built around momentum: capture an **Idea**,
commit to it as an **Action**, pull it into **Focus**, land it in **Done**.

## Stack

- Kotlin 2.0 · Jetpack Compose · Material 3 with dynamic color (Material You)
- Room for persistence, MVVM with `StateFlow`
- Single activity, edge-to-edge, full dark-theme support
- min SDK 26 (Android 8.0) · target SDK 35

## Interactions

- **Tap the status ring** to complete a task (spring animation + haptic)
- **Swipe right** to advance a task one stage (idea → action → focus → done)
- **Swipe left** to delete, with snackbar undo
- **Tap a row** to edit: rename, jump between stages, delete
- Quick-add bar is always docked at the bottom, keyboard-aware

## Build

```bash
./gradlew assembleDebug
# APK lands in app/build/outputs/apk/debug/
```

CI builds every push and uploads the debug APK as a workflow artifact —
grab it from the Actions run to sideload on a device.
