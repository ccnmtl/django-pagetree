JS_FILES=pagetree/static/pagetree/js/src

node_modules/jshint/bin/jshint:
	npm install jshint@~2.9.5 --prefix .

node_modules/jscs/bin/jscs:
	npm install jscs@~3.0.7 --prefix .

jshint: node_modules/jshint/bin/jshint
	./node_modules/jshint/bin/jshint $(JS_FILES)

jscs: node_modules/jscs/bin/jscs
	./node_modules/jscs/bin/jscs $(JS_FILES)

clean:
	rm -rf node_modules

.PHONY: jshint jscs clean
