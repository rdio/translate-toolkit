# Copyright 2002, 2003 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# this Makefile currently just contains tests that we can run to check against major errors...

maintests=test-moz2po test-po2moz test-oo2po test-po2oo
alltests=$(maintests) test-moz2po-notemplate test-moz2po-withtemplate

.PHONY: all clean test $(alltests)

all:

test: $(maintests) clean

clean:
	rm -fR $(alltests)

test-moz2po: test-moz2po-notemplate test-moz2po-withtemplate

# TODO: download xpi for tests and unpack if neccessary...
dtddir=/share/translate.org.za/dev/mozilla/dtd
oodir=/share/translate.org.za/dev/openoffice/oo
oopodir=/share/translate.org.za/translate.sourceforge.net/po/openoffice/

test-moz2po-notemplate: input=$(dtddir)/en-US-1.6
test-moz2po-notemplate: output=test-moz2po-notemplate
test-moz2po-notemplate:
	if [[ -e $(output) ]] ; then rm -R $(output) ; fi
	mkdir $(output)
	./moz2po --progress=none -P -i $(input) -o $(output)

test-moz2po-withtemplate: input=$(dtddir)/de-AT-1.6
test-moz2po-withtemplate: output=test-moz2po-withtemplate
test-moz2po-withtemplate: template=$(dtddir)/en-US-1.6
test-moz2po-withtemplate: 
	if [[ -e $(output) ]] ; then rm -R $(output) ; fi
	mkdir $(output)
	./moz2po --progress=none -i $(input) -o $(output) -t $(template)

test-po2moz: input=test-moz2po-withtemplate
test-po2moz: output=test-po2moz
test-po2moz: template=$(dtddir)/en-US-1.6
test-po2moz:
	if [[ -e $(output) ]] ; then rm -R $(output) ; fi
	mkdir $(output)
	./po2moz --progress=none -i $(input) -o $(output) -t $(template)

test-oo2po: input=$(oodir)/1.1/en
test-oo2po: output=test-oo2po
test-oo2po:
	if [[ -e $(output) ]] ; then rm -R $(output) ; fi
	mkdir $(output)
	./oo2po.py --progress=none -R -P -i $(input) -o $(output)

test-po2oo: input=$(oopodir)/af
test-po2oo: output=test-po2oo
test-po2oo: template=$(oodir)/1.1/en
test-po2oo: languagecode=27
test-po2oo:
	if [[ -e $(output) ]] ; then rm -R $(output) ; fi
	mkdir $(output)
	./po2oo.py --progress=none -R -l $(languagecode) -i $(input) -o $(output) -t $(template)


