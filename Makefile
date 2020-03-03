ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

install: install_dir
	-conda env create -f environment.yml || true
	cp friendly_gt ~/bin
	-ln -s ${ROOT_DIR} ~/bin || true
	chmod +x ~/bin/friendly_gt

uninstall:
	conda remove --name friendly_gt --all
	rm ~/bin/friendly_gt
	rm -rf ~/bin/friendly_ground_truth

install_dir:
	mkdir -p ~/bin
