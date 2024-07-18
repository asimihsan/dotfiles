MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
IOSEVKA_VERSION := $(shell curl -s https://api.github.com/repos/be5invis/Iosevka/releases/latest | jq -r .tag_name | sed 's/v//')

.PHONY: clean build shell install update-version

clean:
	rm -rf $(MAKEFILE_DIR)/build

build:
	docker buildx build --target output --output type=local,dest=$(MAKEFILE_DIR)/build -t iosevka -f Dockerfile .

shell:
	docker run --rm -it -v $(MAKEFILE_DIR):/build iosevka /bin/bash

install:
	rsync -av $(MAKEFILE_DIR)build/ $(HOME)/Fonts/

update-version:
	sed -i '' 's/FONT_VERSION=.*/FONT_VERSION=$(IOSEVKA_VERSION)/' Dockerfile
	@echo "Updated Iosevka version to $(IOSEVKA_VERSION)"
	@echo "Don't forget to update FONT_SHA256SUM manually!"
