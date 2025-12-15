.PHONY: run

run:
	cd frontend && npm run dev -- --host &
	cd mcp && python server.py
