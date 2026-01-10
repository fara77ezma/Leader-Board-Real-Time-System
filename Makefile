# run these as commands not files so they don't conflict with files of the same name
.PHONY: test dev clean

# Run tests
test: 
    # run instead of up to avoid starting unnecessary services for testing + ensure clean state + remove volumes after + open as shell to debug if needed
	docker-compose -f docker-compose.test.yml run --rm -it test-runner
	docker-compose -f docker-compose.test.yml down -v
	

# Alias for test
t: test

# Run development environment
dev:
	docker-compose up -d 

# Clean up containers and volumes
clean:
	docker-compose -f docker-compose.test.yml down -v
	docker-compose down -v

build:
	docker-compose build --no-cache