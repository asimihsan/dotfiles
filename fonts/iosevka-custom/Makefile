MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
IOSEVKA_VERSION := $(shell curl -s https://api.github.com/repos/be5invis/Iosevka/releases/latest | jq -r .tag_name | sed 's/v//')

.PHONY: clean build shell install update-version

clean:
	rm -rf $(MAKEFILE_DIR)/build

build:
	docker buildx build --target output -t iosevka -f Dockerfile . --progress plain
	docker create --name temp_container iosevka /bin/sh
	docker cp temp_container:/dist/ build/
	docker rm temp_container

shell:
	docker run --rm -it -v $(MAKEFILE_DIR):/build iosevka /bin/bash

install:
	rsync -av $(MAKEFILE_DIR)build/ $(HOME)/Fonts/
	rsync -av $(MAKEFILE_DIR)build/ $(HOME)/Library/Fonts/

update-version:
	sed -i '' 's/FONT_VERSION=.*/FONT_VERSION=$(IOSEVKA_VERSION)/' Dockerfile
	@echo "Updated Iosevka version to $(IOSEVKA_VERSION)"
	@echo "Don't forget to update FONT_SHA256SUM manually!"
