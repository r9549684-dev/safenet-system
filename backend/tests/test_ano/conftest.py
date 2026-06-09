"""Конфигурация тестов SafeNet ANO."""
import os
import sys
import shutil

import pytest

# Добавляем backend в sys.path для импортов (3 уровня вверх от conftest.py)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

TEST_DATA_DIR = os.path.join(BACKEND_DIR, ".test_ano_data")
ANO_DIR = os.path.join(TEST_DATA_DIR, "ano")

# Отключаем использование реального снапшота для тестов
os.environ["ANO_DATA_DIR"] = TEST_DATA_DIR

@pytest.fixture(autouse=True)
def isolate_ano_environment():
    """Гарантирует чистое состояние графа и памяти перед каждым тестом."""
    if os.path.exists(ANO_DIR):
        shutil.rmtree(ANO_DIR)
    os.makedirs(ANO_DIR, exist_ok=True)
    yield
