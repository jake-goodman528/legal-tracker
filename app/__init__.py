"""
STR Compliance Toolkit - Application Package

A Flask-based web application for tracking Short-Term Rental (STR) 
legal and compliance requirements across multiple jurisdictions.
"""

__version__ = "1.0.0"
__author__ = "Kaystreet Management"

from .application import create_app

__all__ = ['create_app'] 