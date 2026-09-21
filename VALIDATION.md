# Release validation — version 1.1.0

Verified on macOS on 21 September 2026 using Python 3.14.6:

- Automated suite: **21 passed, 1 skipped**. The skipped test needs an old development HTML capture intentionally absent from this distribution.
- Both map formats, unavailable ticket categories, URL validation, local HTTP bridge request/response behavior, and startup failure handling are covered.
- Mac launcher and POSIX shell launcher dependency checks and help commands run successfully.
- Both shell launchers pass shell syntax checks; both extension JavaScript files pass Node syntax checks.
- A real Chrome capture of Santiano in Bad Segeberg (22 May 2027) succeeded: **10 ticket categories, 18 sections, no parser warnings**. The earlier parser/map fixes were used in that live capture; later packaging improvements do not change those extraction rules.

The release archive is checked for corruption, allowed file contents, LF shell endings, CRLF Windows batch endings, and executable permissions for the Mac/Linux launchers. First-run installation is tested from a clean extraction in a folder containing spaces before delivery.

## Platform limits

Windows and Linux launchers are included and use the same standard-library Python setup. No Windows or Linux runtime was available for this release session, so their native launchers and browser capture were **not run here**. The bundled GitHub Actions workflow can run startup and automated tests on all three operating systems when the project is placed in a GitHub repository; those remote jobs have not been run in this session.

The historical README reported a successful Windows run of an earlier version. That is not a test of this updated Windows launcher.

Python and Chrome must be installed separately. The extension must be loaded once in Chrome on each computer/profile. A website layout change or unsupported event can still require a future parser update; no release can guarantee every future EVENTIM page.
