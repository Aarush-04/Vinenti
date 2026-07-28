# Vinenti *(working title)*

> An AI life companion that connects to your calendar, GitHub, and (soon)
> your phone to help you stay on track — without the guilt-trip.

**Status:** early personal-use prototype, actively in development. Not yet
public-facing, but the long-term goal is a real product.

## What this is

Most productivity tools ask you to manually plan your day. This project
takes the opposite approach: it connects directly to the tools and signals
that already reflect your life — calendar, GitHub activity, and eventually
screen time and location — and uses an LLM to turn that into a short,
honest, encouraging daily brief. No manual setup, no dashboards to
maintain, minimal friction.

## Current state (v1)

- [x] Google Calendar integration (reads today's events)
- [x] GitHub activity tracking (recent commits/PRs)
- [x] LLM-generated daily brief via Groq
- [ ] Native mobile app (iOS first, via Expo/React Native)
- [ ] Screen time awareness + limits
- [ ] Location awareness
- [ ] Job application tracking
- [ ] Sleep tracking

## Why

Built out of a real, personal need: staying accountable and organized
during a period of school/job-search overload, without needing to
manually maintain five different apps to do it. If it turns out to be
genuinely useful beyond just me, the plan is to bring it to market.

## Tech stack

- Python (v1 prototype / core logic)
- Groq API (LLM reasoning)
- Google Calendar API
- GitHub API
- Planned: React Native (Expo) for the iOS/Android app

## Running it locally

See `README_SETUP.md` for full setup instructions (API keys, Google OAuth,
etc.). Note: you'll need your own API keys — none are included in this repo.

---

*This is a solo, work-in-progress project. Feedback and issues welcome, but
expect rough edges — this is v1 of what's meant to become something much
bigger.*
