# Bug Surgeon Development Makefile

.PHONY: help install test test-github clean setup

help:
	@echo "Bug Surgeon Development Commands:"
	@echo "  setup     - Complete project setup"
	@echo "  install   - Install Python dependencies"
	@echo "  test      - Run local functionality test"
	@echo "  test-github - Run GitHub integration test"
	@echo "  clean     - Clean up generated files"

setup:
	@echo "🚀 Setting up Bug Surgeon development environment..."
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"
	@echo "Then run: make install"

install:
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully"

test:
	@echo "🧪 Running local functionality test..."
	python test_local.py

test-github:
	@echo "🔗 Running GitHub integration test..."
	python test_github.py

clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	@echo "✅ Cleanup complete"

dev-setup:
	@echo "🛠️  Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.template .env && echo "📝 Created .env file - please add your API keys"; fi
	@echo "✅ Development setup complete"
