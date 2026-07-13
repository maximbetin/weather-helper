# Android Development and APK Builds

This guide assumes no previous Android experience. Weather Helper is still a
Python project: Flet supplies the mobile interface and packages the Python code
for Android. You do not need to rewrite the application in Kotlin or install
Android Studio for the normal workflow described here.

## How the project fits together

The Windows and Android applications share the same weather and scoring logic:

| Area | Purpose |
| --- | --- |
| `src/core/` | Weather API, models, evaluation, and scoring |
| `src/application/` | UI-independent loading and display helpers |
| `src/gui/` | Tkinter Windows interface |
| `src/mobile/view_model.py` | Mobile selection and presentation state |
| `src/mobile/app.py` | Responsive Flet interface |
| `weather_helper.py` | Windows entry point |
| `weather_helper_mobile.py` | Flet/Android entry point |

Put business rules in `src/core/` or `src/application/`, not directly in either
UI. This keeps Windows and Android results consistent.

## First-time setup on Windows

You need Git, Python 3.13, an internet connection, and several gigabytes of free
disk space. The first Android build is slow because Flet may download Flutter,
JDK 17, Android SDK components, and Gradle packages. Later builds reuse them.

From PowerShell in the repository root:

```powershell
py -3.13 -m venv .venv-mobile
.\.venv-mobile\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[mobile,dev]"
```

The prompt should begin with `(.venv-mobile)` after activation. Activate this
environment again whenever you open a new PowerShell window.

## Previewing the mobile interface

Run the Flet desktop preview:

```powershell
flet run weather_helper_mobile.py
```

For responsive testing in a browser:

```powershell
flet run --web weather_helper_mobile.py
```

The browser preview is useful for layout work, but test important behavior on a
real Android phone before considering a release finished.

## A safe development loop

1. Activate `.venv-mobile`.
2. Make one focused change.
3. Run `python -m pytest`.
4. Run the Flet preview and check narrow and wide layouts.
5. Build an APK when the tests and preview are clean.
6. Install it on the phone and check loading, selectors, ranking, scrolling,
   and hourly details.

To run all tests:

```powershell
python -m pytest
```

## Building an APK locally

The build configuration lives under `[tool.flet]` in `pyproject.toml`. From the
activated mobile environment, run:

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
flet build apk --yes --no-rich-output
```

The completed file is normally:

```text
build\apk\weather-helper.apk
```

The UTF-8 settings prevent older Windows console encodings from failing on
Flet's progress characters. `--yes` permits Flet to install missing build tools,
and `--no-rich-output` produces cleaner logs.

### Version numbers

Android uses two version values:

- `[project].version` is the user-visible version, such as `1.2.0`.
- `[tool.flet].build_number` is Android's internal integer version code.

Increase the build number before distributing a new local APK. Android will not
install an update whose build number is lower than the installed version. The
GitHub workflow overrides the local build number with `github.run_number`, so CI
builds increase automatically.

## Installing or updating on a phone

1. Copy or upload the APK to the phone.
2. Open it from Files, Drive, or the browser.
3. If Android asks, allow that app to install unknown apps.
4. Choose **Install** or **Update**.

Android updates also require the new APK to use the same package ID and signing
certificate as the installed APK. Weather Helper's package ID is
`com.maximbk.weatherhelper`.

## Signing: why it matters

Every APK must be signed. Without a configured keystore, Flet uses a debug key.
That is acceptable for personal testing, but GitHub's temporary runners can
create different debug keys on different runs. APKs signed by different keys
cannot update one another.

For repeatable GitHub downloads, create one private release keystore and keep it
for the lifetime of the app. Never commit the keystore or its passwords.

### Create a release keystore

With JDK 17's `keytool` available:

```powershell
keytool -genkeypair -v `
  -keystore weather-helper-release.jks `
  -keyalg RSA `
  -keysize 2048 `
  -validity 10000 `
  -alias weather-helper
```

Store the file and passwords in a secure backup. Losing this key means future
builds cannot update installations signed by it.

Convert the file to Base64 and copy it to the clipboard:

```powershell
[Convert]::ToBase64String(
  [IO.File]::ReadAllBytes("weather-helper-release.jks")
) | Set-Clipboard
```

In GitHub, open **Settings → Secrets and variables → Actions** and create these
repository secrets:

| Secret | Value |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | Base64 text copied above |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_PASSWORD` | Key password |
| `ANDROID_KEY_ALIAS` | `weather-helper` |

The workflow detects these secrets and signs the APK with that key. If they are
missing, the workflow still builds a debug-signed APK and displays a warning.

Important: switching from the current debug key to a release key requires
uninstalling the debug-signed app once before installing the release-signed APK.
After that transition, future APKs signed with the release key can update it.

## What GitHub Actions does

`.github/workflows/release.yml` runs for relevant pushes to `main` and can also
be started manually from the Actions page. It:

1. runs the complete test suite;
2. calculates the next release version;
3. builds the Windows executable and Android APK in parallel;
4. stores both as workflow artifacts;
5. creates a GitHub Release containing both downloads.

Release version rules are based on the latest `vX.Y.Z` tag:

- ordinary commit: patch release (`1.2.3` → `1.2.4`);
- commit beginning with `feat:` or containing `[minor]`: minor release;
- commit beginning with `BREAKING:` or containing `[major]`: major release.

Downloads appear in two places:

- **Actions → workflow run → Artifacts**, after each successful build;
- **Releases**, as versioned Windows ZIP and Android APK files.

## Troubleshooting

### `No Android SDK found`

Flet normally installs or finds the SDK. If Windows has the SDK but Flutter does
not detect it, set these variables and retry:

```powershell
$env:ANDROID_HOME = "$env:USERPROFILE\Android\sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
flet build apk --yes --no-rich-output
```

If Flet installed Java itself and Java is not detected, set `JAVA_HOME` to the
versioned directory under `$env:USERPROFILE\java`.

### `PermissionError` while copying to `build\apk`

Close File Explorer previews, terminals, or antivirus dialogs using the old APK,
then retry. Flet clears the output directory before copying the new result.

### Android refuses to update

Check both likely causes:

- the new build number must be higher;
- the new APK must use the same signing key.

If the signing key changed intentionally, uninstall the old app once and install
the new APK. Uninstalling removes the app's local data.

### The APK is large

The default APK contains multiple Android CPU architectures for maximum device
compatibility. Flet can build separate ABI-specific APKs later, but a single
universal APK is simpler for private sideloading.

## Official references

- [Flet publishing guide](https://flet.dev/docs/publish/)
- [Flet Android packaging guide](https://flet.dev/docs/publish/android/)
- [GitHub Actions workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts)
