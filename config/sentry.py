import os


def init_sentry() -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    traces_sample_rate_str = os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")
    try:
        traces_sample_rate = float(traces_sample_rate_str)
    except ValueError:
        traces_sample_rate = 0.0

    send_pii = os.getenv("SENTRY_SEND_PII", "0") == "1"

    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", "local"),
        send_default_pii=send_pii,
        traces_sample_rate=traces_sample_rate,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
    )