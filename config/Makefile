MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

clean:
	rm -rf $(MAKEFILE_DIR)/build

iosevka-docker-build:
	docker buildx build -t iosevka -f Dockerfile.iosevka .

iosevka-docker-shell:
	docker run --volume $(MAKEFILE_DIR):/build -it iosevka /bin/bash

iosevka-font-build:
	docker run -it --volume $(MAKEFILE_DIR):/build iosevka /bin/bash /build/iosevka-run.sh
	rsync -av dist/iosevka-custom/ttf/ $HOME/Library/Fonts
