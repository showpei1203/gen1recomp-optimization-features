# SoulGold M6A2 FIX1 — Native Library Extraction Authority

Date: 2026-09-03
Branch: feature/soulgold-showdown-m6a2

## Failure observed on AYN THOR

M6A2 reached Android/JNI but failed before ROM selection because the bridge opened `ApplicationInfo.nativeLibraryDir/libmgba_libretro.so` and that extracted file did not exist on the THOR install.

The APK build itself already contained the arm64-v8a mGBA and runtime bridge libraries. The defect was therefore Android native-library packaging/extraction semantics, not failure to cross-compile mGBA.

## FIX1

- `android:extractNativeLibs="true"`
- Gradle `jniLibs { useLegacyPackaging true }`
- versionCode 2 / versionName `M6A2-FIX1`
- CI rebuilds pinned mGBA arm64-v8a and requires the final APK to contain:
  - `lib/arm64-v8a/libmgba_libretro.so`
  - `lib/arm64-v8a/libsoulgold_m6a2.so`

## Build evidence

- GitHub Actions run: `33744790433`
- Artifact id: `9889224912`
- Result: SUCCESS
- APK SHA-256: `66ffce246e021ed7fbb292f1d5108498db3f5853aa816c2591c37a73b2d7d62d`
- ROM bundled: no

## Acceptance

- Build / APK packaging contract: PASS
- AYN THOR FIX1 runtime boot: PENDING USER DEVICE TEST
- SoulGold gameplay runtime: PENDING
- Showdown Android compositor: deferred to M6A3

## Regression rules

- R-SD-144: When the bridge resolves mGBA via nativeLibraryDir, Android packaging must guarantee an extraction-compatible JNI contract.
- R-SD-145: Native-library presence inside an APK is build evidence only; it never constitutes THOR runtime PASS without device evidence.
