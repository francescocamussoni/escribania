.PHONY: install setup migrate seed demo-data user test run demo db-up db-down smoke frontend-install frontend-dev

# Atajos desde la raíz del repo → delegan a backend/
install setup migrate seed demo-data user test run demo frontend-install frontend-dev:
	$(MAKE) -C backend $@

smoke:
	@chmod +x scripts/smoke_test.sh
	@./scripts/smoke_test.sh

db-up:
	docker compose up db -d

db-down:
	docker compose down -v
