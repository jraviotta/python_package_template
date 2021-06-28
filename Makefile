.PHONY: clean data lint requirements

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME := $(shell basename $(PWD))

PROFILE = default
PYTHON_INTERPRETER = `which python3`
SHELL = /bin/bash

ifeq (,$(shell which conda))
HAS_CONDA=False
else
HAS_CONDA=True
endif

#################################################################################
# COMMANDS                                                                      #
#################################################################################
## Print a variable EG: [make print-HOME]
# print-<VAR>
print-% : ; $(info $* is a $(flavor $*) variable set to [$($*)]) @true

## Use arguments with a make target EG: [make -- build foo bar baz]
# -- <command> <args>
%:
	@:
ARGS = $(filter-out $@,$(MAKECMDGOALS))
MAKEFLAGS += --silent

## Install Python Dependencies
environment : PYTHON_INTERPRETER = /usr/bin/python3
environment: test_environment
	test -e ./.venv
ifeq (True,$(HAS_CONDA))
	@echo ">>> Detected conda, creating conda environment."
ifeq (3,$(findstring 3,$(PYTHON_INTERPRETER)))
	conda create --name $(PROJECT_NAME) python=3
	conda env update --name $(PROJECT_NAME) -f environment.yml
else
	conda create --name $(PROJECT_NAME) python=2.7
	conda env update --name $(PROJECT_NAME) -f environment.yml
endif
	@echo ">>> New conda env created. Activate with: source activate $(PROJECT_NAME)"
else
	$(PYTHON_INTERPRETER) -m pip install --user -U pip setuptools wheel jupyter\
		nbstripout entrypoints flake8 yapf ipykernel
	@echo ">>> Installing virtualenv if not already intalled."
	$(PYTHON_INTERPRETER) -m venv .venv
	bash -c "source .venv/bin/activate \
		&& pip install -e . \
		&& ipython kernel install --user --name=$(PROJECT_NAME)"
	
	@printf ">>> New virtualenv created. Activate with:\nsource .venv/bin/activate\n\n"
	
endif


## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find -type d -name "*.egg-info" -exec rm -rf {} +
	find -type d -name ".venv" -exec rm -rf {} +
	find -type d -name "build" -exec rm -rf {} +
	find -type d -name "dist" -exec rm -rf {} +

## Lint using flake8
lint:
	flake8 fluve

## Test python environment is setup correctly
test_environment:
	$(PYTHON_INTERPRETER) test_environment.py

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
