# run these as commands not files so they don't conflict with files of the same name
.PHONY: test dev clean

# Run tests
test: 
    # run instead of up to avoid starting unnecessary services for testing + ensure clean state + remove volumes after + open as shell to debug if needed
	docker-compose -f docker-compose.test.yml run --rm -it test-runner
	docker-compose -f docker-compose.test.yml down -v

# make test-one TARGET=test_successful_registration_returns_201
test-one:
# -k allows you to specify a substring to match test names, so you can run specific tests without running the entire suite 
# -vv for more verbose output, -s to disable output capture so you can see print statements in real time (useful for debugging)
	docker-compose -f docker-compose.test.yml run --rm -it test-runner pytest -s -vv -k  $(TARGET)
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