SHELL := /bin/zsh

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
KERYX := $(VENV)/bin/keryx
CONFIG ?= local.config.yaml
LAUNCHD_INSTALLER := scripts/install_launchd.py
API_LABEL := io.keryx.api
MCP_LABEL := io.keryx.mcp

.PHONY: help venv install test index serve mcp watch install-launchd restart-launchd status-launchd health mcp-check logs

help:
	@echo "Targets:"
	@echo "  make venv               Create local virtualenv"
	@echo "  make install            Install package and dev dependencies"
	@echo "  make test               Run test suite"
	@echo "  make index              Index vault using CONFIG=$(CONFIG)"
	@echo "  make serve              Run HTTP API using CONFIG=$(CONFIG)"
	@echo "  make mcp                Run MCP server using CONFIG=$(CONFIG)"
	@echo "  make watch              Run polling re-index watcher"
	@echo "  make install-launchd    Install/update launchd services"
	@echo "  make restart-launchd    Kickstart launchd services"
	@echo "  make status-launchd     Show launchd service status"
	@echo "  make health             Check HTTP health endpoint"
	@echo "  make mcp-check          List MCP tools from local server"
	@echo "  make logs               Tail launchd logs"

venv:
	python3 -m venv $(VENV)

install: venv
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -e '.[dev]'

test:
	$(PYTEST) -q tests

index:
	$(KERYX) index --config $(CONFIG)

serve:
	$(KERYX) serve --config $(CONFIG)

mcp:
	$(KERYX) mcp --config $(CONFIG)

watch:
	$(KERYX) watch --config $(CONFIG)

install-launchd:
	PYTHONPATH=src $(PYTHON) $(LAUNCHD_INSTALLER)

restart-launchd:
	launchctl kickstart -k gui/$$(id -u)/$(API_LABEL)
	launchctl kickstart -k gui/$$(id -u)/$(MCP_LABEL)

status-launchd:
	launchctl print gui/$$(id -u)/$(API_LABEL) | head -n 60
	launchctl print gui/$$(id -u)/$(MCP_LABEL) | head -n 60

health:
	curl -s http://127.0.0.1:8765/health | python3 -m json.tool

mcp-check:
	$(PYTHON) scripts/check_mcp.py

logs:
	tail -n 80 -f \
		"$$HOME/Library/Logs/keryx/keryx-api.err.log" \
		"$$HOME/Library/Logs/keryx/keryx-mcp.err.log"
