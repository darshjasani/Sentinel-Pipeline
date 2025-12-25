.PHONY: up down clean logs seed demo-testfail demo-success health

# Start the entire system
up:
	@echo "🚀 Starting Sentinel Pipeline system..."
	@mkdir -p data/logs
	@docker-compose up -d --build
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 10
	@$(MAKE) health
	@$(MAKE) seed
	@echo ""
	@echo "✔ System ready!"
	@echo "✔ API listening on http://localhost:8000"
	@echo "✔ UI available at http://localhost:3000"
	@echo ""
	@echo "Try these commands:"
	@echo "  make demo:testfail  - Trigger deterministic test failure"
	@echo "  make demo:success   - Trigger successful run"
	@echo "  make logs          - View system logs"

# Stop all services
down:
	@echo "🛑 Stopping Sentinel Pipeline system..."
	@docker-compose down

# Clean everything including volumes
clean:
	@echo "🧹 Cleaning all data and volumes..."
	@docker-compose down -v
	@rm -rf data/logs/*
	@echo "✔ Clean complete"

# View logs
logs:
	@docker-compose logs -f

# View logs for specific service
logs-api:
	@docker-compose logs -f api

logs-worker:
	@docker-compose logs -f worker

logs-ui:
	@docker-compose logs -f ui

# Health check
health:
	@echo "🏥 Checking service health..."
	@docker-compose ps
	@echo ""
	@echo "Testing API health endpoint..."
	@curl -s http://localhost:8000/health | grep -q "ok" && echo "✔ API is healthy" || echo "✖ API is unhealthy"

# Seed database
seed:
	@echo "🌱 Seeding database..."
	@docker-compose exec -T api python -c "from database import seed_database; seed_database()" || echo "⚠️  Database already seeded or API not ready yet"

# Demo: Trigger deterministic test failure
demo:testfail:
	@echo "🔴 Triggering deterministic test failure..."
	@curl -s -X POST http://localhost:8000/runs \
		-H "Content-Type: application/json" \
		-d '{"repo_id":"python-sample","job_template":"pytest-fail","timeout_sec":300,"triggered_by":"demo"}' \
		| python3 -m json.tool
	@echo ""
	@echo "✔ Run triggered. Check UI at http://localhost:3000"
	@echo "Expected: Incident will be created after failure threshold"

# Demo: Trigger successful run
demo:success:
	@echo "🟢 Triggering successful run..."
	@curl -s -X POST http://localhost:8000/runs \
		-H "Content-Type: application/json" \
		-d '{"repo_id":"python-sample","job_template":"pytest-success","timeout_sec":300,"triggered_by":"demo"}' \
		| python3 -m json.tool
	@echo ""
	@echo "✔ Run triggered. Check UI at http://localhost:3000"

# Demo: Trigger flaky test
demo:flaky:
	@echo "🟡 Triggering flaky test scenario..."
	@for i in 1 2 3 4 5; do \
		curl -s -X POST http://localhost:8000/runs \
			-H "Content-Type: application/json" \
			-d '{"repo_id":"python-sample","job_template":"pytest-flaky","timeout_sec":300,"triggered_by":"demo"}' > /dev/null; \
		echo "Run $$i triggered..."; \
		sleep 3; \
	done
	@echo "✔ 5 runs triggered. Flaky test should be detected in UI"

# Restart worker (useful for debugging)
restart-worker:
	@docker-compose restart worker

# Restart API
restart-api:
	@docker-compose restart api

# Full rebuild
rebuild:
	@echo "🔨 Rebuilding all services..."
	@docker-compose down
	@docker-compose build --no-cache
	@$(MAKE) up

# Show recent runs via API
runs:
	@echo "📋 Recent CI runs:"
	@curl -s http://localhost:8000/runs?limit=10 | python3 -m json.tool

# Show incidents
incidents:
	@echo "🚨 Current incidents:"
	@curl -s http://localhost:8000/incidents | python3 -m json.tool

# Interactive shell in API container
shell-api:
	@docker-compose exec api /bin/sh

# Interactive shell in worker container
shell-worker:
	@docker-compose exec worker /bin/sh

# Database shell
shell-db:
	@docker-compose exec postgres psql -U ciuser -d ci_pipeline

# Help
help:
	@echo "Sentinel Pipeline - Available Commands"
	@echo ""
	@echo "Main commands:"
	@echo "  make up              - Start the entire system"
	@echo "  make down            - Stop all services"
	@echo "  make clean           - Clean all data and volumes"
	@echo ""
	@echo "Demo commands:"
	@echo "  make demo:testfail   - Trigger test failure"
	@echo "  make demo:success    - Trigger successful run"
	@echo "  make demo:flaky      - Trigger flaky test scenario"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs            - View all logs"
	@echo "  make health          - Check service health"
	@echo "  make runs            - Show recent runs"
	@echo "  make incidents       - Show current incidents"
	@echo ""
	@echo "Debugging:"
	@echo "  make shell-api       - API container shell"
	@echo "  make shell-worker    - Worker container shell"
	@echo "  make shell-db        - Database shell"

