# Elettra Mobile

Client Flutter mobile-ready per Elettra.

## Target

- Android e iOS sono i target prodotto.
- Web resta un target tecnico per test rapidi e demo.

## Comandi Locali

Da Linux:

```bash
flutter pub get
flutter analyze
flutter test
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Su Android emulator, il backend locale dell'host va normalmente raggiunto con:

```bash
flutter run -d emulator --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

## iOS

Da Linux il codice resta sviluppabile e testabile su web/Android. La build iOS va verificata tramite runner macOS:

```bash
flutter build ios --no-codesign
```
