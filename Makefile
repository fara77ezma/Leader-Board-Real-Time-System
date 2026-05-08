# run these as commands not files so they don't conflict with files of the same name
.PHONY: test dev clean

# Run tests
test: 
    # run instead of up to avoid starting unnecessary services for testing + ensure clean state + remove volumes after + open as shell to debug if needed
	docker-compose -f docker-compose.test.yml run --rm -it test-runner
	docker-compose -f docker-compose.test.yml down -v

# make test-one TARGET=tests/test_auth_integration.py::TestRegister::test_successful_registration_returns_201
test-one:
	docker-compose -f docker-compose.test.yml run --rm -it test-runner pytest $(TARGET)
	docker-compose -f docker-compose.test.yml down -v

# Alias for test
t: test

to: test-one

# Run development environment
dev:
	docker-compose up -d 

# Clean up containers and volumes
clean:
	docker-compose -f docker-compose.test.yml down -v
	docker-compose down -v

build:
	docker-compose build --no-cache