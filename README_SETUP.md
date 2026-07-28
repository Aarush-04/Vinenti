# AI Life Companion — v1 (local prototype)

This is the first slice of the app: a script that reads your GitHub activity
and Google Calendar, and generates a short AI "daily brief." It runs on your
PC. Nothing here touches your iPhone yet — that comes after this logic is
proven out (see "Where this goes next" at the bottom).

## 1. Install Python dependencies

Open a terminal in this folder and run:

```
pip install -r requirements.txt
```

## 2. Get a Groq API key (free)

1. Go to https://console.groq.com and sign up.
2. Create an API key.
3. Copy `.env.example` to a new file called `.env`.
4. Paste your key into `GROQ_API_KEY=`.

## 3. Get a GitHub token (free, 2 minutes)

1. Go to https://github.com/settings/tokens
2. Generate a new token (classic), no special scopes needed for public
   activity — if you want private repo activity too, check the `repo` scope.
3. Put your GitHub username and the token into `.env`.

## 4. Connect Google Calendar (~10 minutes, one-time)

This is the fiddly one — Google requires you to register your own small
"app" with them before it can read your calendar. This is normal for every
developer, not something specific to you being new at this.

1. Go to https://console.cloud.google.com/ and create a new project (free).
2. In the search bar, enable the **Google Calendar API** for that project.
3. Go to "APIs & Services" → "OAuth consent screen." Choose "External,"
   fill in an app name (can be anything, e.g. "My Companion App"), your
   email, and save. You can leave it in "Testing" mode — you don't need to
   publish it since you're the only user for now.
4. Under "Test users," add your own Google email address.
5. Go to "Credentials" → "Create Credentials" → "OAuth client ID" →
   choose "Desktop app."
6. Download the resulting JSON file, rename it `credentials.json`, and put
   it in this folder.
7. Run:
   ```
   python google_auth.py
   ```
   A browser window opens, you log in and approve access, and a `token.json`
   file is created. You won't need to repeat this step again unless you
   delete that file.

## 5. Run it

```
python companion.py
```

You should see your GitHub activity, your calendar for today, and then an
AI-generated brief underneath.

## Troubleshooting

- **"GROQ_API_KEY not set"** — check your `.env` file exists (not just
  `.env.example`) and is in the same folder as `companion.py`.
- **Google login says "app not verified"** — this is expected while your
  app is in "Testing" mode with only you as a test user. Click
  "Advanced" → "Go to [app name] (unsafe)." It's your own app talking to
  your own account, so this is safe.
- **GitHub summary always says "no activity"** — the free GitHub events API
  only returns public activity by default; make sure `GITHUB_TOKEN` has the
  `repo` scope if you want private repo commits counted too.

## Where this goes next

Once this logic feels right (the brief is actually useful, not just
technically working), the plan is to port this into an **Expo
(React Native)** app so it runs natively on your iPhone — using Expo Go to
test on your actual phone without needing a Mac, and Expo's cloud build
service (EAS) for the eventual App Store submission. That's also when
screen time limits and location awareness become possible, since those
need real iOS permissions that a desktop script can't access.
