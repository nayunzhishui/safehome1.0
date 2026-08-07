"""Production WSGI entrypoint with infrastructure adapters installed first."""

from services.runtime_bootstrap import configure_app, install_pre_app


install_pre_app()

from app import app as _app  # noqa: E402  (bootstrap must run before app import)


configure_app(_app)
app = _app
