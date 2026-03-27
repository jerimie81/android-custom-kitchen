# Suggested Improvements

1. **Make the workspace path dynamic and configurable**  
   The sidebar currently hardcodes `~/android-custom-kitchen`, which may not match where users launch the app. Read the actual working directory (or a saved setting) and display that value so logs and instructions remain accurate.

2. **Add preflight severity levels and one-click remediation helpers**  
   `run_preflight()` correctly checks tool presence, but all failures are treated the same. Add severity categories (required vs optional), plus actions such as "Copy install command" and "Re-check" to improve onboarding.

3. **Improve command result diagnostics in the status bar**  
   The status bar currently reports only pass/fail. Include command name, exit code, and a shortcut action like "Open logs" so users can diagnose failures faster without hunting through output.
