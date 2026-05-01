"""Compat shim: BKP usa Agendor (não Pipedrive). Reexporta tudo."""
from agendor_api import *  # noqa
from agendor_api import _request, _normalize_person, _normalize_org, _normalize_deal  # noqa
