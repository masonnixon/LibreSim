#!/usr/bin/env python3
"""Validation script to check backend can import and start correctly."""

import sys


def validate_imports():
    """Test that all modules can be imported."""
    errors = []

    print("Validating imports...")

    # Test core imports
    try:
        from pydantic import BaseModel
        print("  ✓ pydantic")
    except ImportError as e:
        errors.append(f"pydantic: {e}")
        print(f"  ✗ pydantic: {e}")

    try:
        from pydantic_settings import BaseSettings
        print("  ✓ pydantic_settings")
    except ImportError as e:
        errors.append(f"pydantic_settings: {e}")
        print(f"  ✗ pydantic_settings: {e}")

    try:
        from fastapi import FastAPI
        print("  ✓ fastapi")
    except ImportError as e:
        errors.append(f"fastapi: {e}")
        print(f"  ✗ fastapi: {e}")

    # Test config
    try:
        from src.config import settings
        print("  ✓ src.config")
    except Exception as e:
        errors.append(f"src.config: {e}")
        print(f"  ✗ src.config: {e}")

    # Test models
    try:
        from src.models.model import Model
        from src.models.block import Block, Connection
        from src.models.simulation import SimulationConfig
        print("  ✓ src.models")
    except Exception as e:
        errors.append(f"src.models: {e}")
        print(f"  ✗ src.models: {e}")

    # Test OSK
    try:
        from src.osk import State, Block as OSKBlock, Sim
        from src.osk.blocks import Constant, Scope, Integrator, Sum, Gain
        print("  ✓ src.osk")
    except Exception as e:
        errors.append(f"src.osk: {e}")
        print(f"  ✗ src.osk: {e}")

    # Test simulation
    try:
        from src.simulation.runner import SimulationRunner
        from src.simulation.compiler import ModelCompiler
        from src.simulation.osk_adapter import OSKAdapter
        print("  ✓ src.simulation")
    except Exception as e:
        errors.append(f"src.simulation: {e}")
        print(f"  ✗ src.simulation: {e}")

    # Test routes
    try:
        from src.api.routes import models, blocks, simulation, import_export
        print("  ✓ src.api.routes")
    except Exception as e:
        errors.append(f"src.api.routes: {e}")
        print(f"  ✗ src.api.routes: {e}")

    # Test main app
    try:
        from src.main import app
        print("  ✓ src.main")
    except Exception as e:
        errors.append(f"src.main: {e}")
        print(f"  ✗ src.main: {e}")

    return errors


def validate_app():
    """Test that FastAPI app can be created."""
    print("\nValidating FastAPI app...")

    try:
        from src.main import app

        # Check routes are registered
        routes = [route.path for route in app.routes]
        expected_routes = ["/api/simulate/start", "/api/simulate/status", "/health"]

        for expected in expected_routes:
            if expected in routes:
                print(f"  ✓ Route {expected}")
            else:
                print(f"  ✗ Route {expected} not found")
                return [f"Missing route: {expected}"]

        print("  ✓ All expected routes registered")
        return []
    except Exception as e:
        print(f"  ✗ Failed to validate app: {e}")
        return [str(e)]


def main():
    """Run all validations."""
    print("=" * 50)
    print("LibreSim Backend Validation")
    print("=" * 50)

    all_errors = []

    # Run validations
    all_errors.extend(validate_imports())
    all_errors.extend(validate_app())

    print("\n" + "=" * 50)
    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s) found")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("SUCCESS: All validations passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
