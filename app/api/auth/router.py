"""The auth APIRouter instance. Endpoints are registered in views.py."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])
