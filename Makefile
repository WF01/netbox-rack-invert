sources = netbox_rack_inverter

.PHONY: test format lint pre-commit clean test-install-script
test: format lint

format:
	ruff check --select I --fix $(sources)
	ruff format $(sources)

lint:
	ruff check $(sources)

pre-commit:
	pre-commit run --all-files

clean:
	rm -rf *.egg-info
	rm -rf .tox dist site


test-install-script:
	bash ./testing/test_install_script.sh
