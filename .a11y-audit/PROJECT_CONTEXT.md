# SafeHome accessibility audit context

- Standard target: WCAG 2.1 AA engineering checks; this repository does not claim full conformance without human assistive-technology evidence.
- Scope: `apps/web` participant/researcher routes and all pages declared by `apps/miniprogram/app.json`.
- Primary users: parents, students, researchers, supervisors and administrators, including people using larger text, keyboard navigation, screen readers or reduced motion.
- Critical flows: assessment submission, emotion diary, practice check-in, relationship growth record, supervision request and researcher review.
- Current evidence: deterministic source/token audit plus Playwright desktop/mobile/200%-text/reduced-motion checks.
- External gates: real screen reader, WeChat embedded browser, Android/iOS devices and formative cognitive interviews remain unsigned.
- Exclusions: authentication passwords and one-time family bind codes must not be persisted as drafts.
