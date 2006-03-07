#!/usr/bin/env python

from translate.storage import dtd
from translate.misc import wStringIO

class TestDTD:
    def dtdparse(self, dtdsource):
        """helper that parses dtd source without requiring files"""
        dummyfile = wStringIO.StringIO(dtdsource)
        dtdfile = dtd.dtdfile(dummyfile)
        return dtdfile

    def dtdregen(self, dtdsource):
        """helper that converts dtd source to dtdfile object and back"""
        return str(self.dtdparse(dtdsource))

    def test_simpleentity(self):
        """checks that a simple dtd entity definition is parsed correctly"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.dtdelements) == 1
        dtdelement = dtdfile.dtdelements[0]
        assert dtdelement.entity == "test.me"
        assert dtdelement.definition == '"bananas for sale"'

    def test_blanklines(self):
        """checks that blank lines don't break the parsing or regeneration"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_simpleentity_source(self):
        """checks that a simple dtd entity definition can be regenerated as source"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_hashcomment_source(self):
        """checks that a #expand comment is retained in the source"""
        dtdsource = '#expand <!ENTITY lang.version "__MOZILLA_LOCALE_VERSION__">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_commentclosing(self):
        """tests that comment closes with trailing space aren't duplicated"""
        dtdsource = '<!-- little comment --> \n<!ENTITY pane.title "Notifications">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_commententity(self):
        """check that we don't process messages in <!-- comments -->: bug 102"""
        dtdsource = '''<!-- commenting out until bug 38906 is fixed
<!ENTITY messagesHeader.label         "Messages"> -->'''
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.dtdelements) == 1
        dtdelement = dtdfile.dtdelements[0]
        print dtdelement
        assert dtdelement.isnull()

    def test_newlines_in_entity(self):
        """tests that we can handle newlines in the entity itself"""
        dtdsource = '''<!ENTITY fileNotFound.longDesc "
<ul>
  <li>Check the file name for capitalisation or other typing errors.</li>
  <li>Check to see if the file was moved, renamed or deleted.</li>
</ul>
">
'''
        dtdregen = self.dtdregen(dtdsource)
        print dtdregen
        print dtdsource
        assert dtdsource == dtdregen

    def test_conflate_comments(self):
        """Tests that comments don't run onto the same line"""
        dtdsource = '<!-- test comments -->\n<!-- getting conflated -->\n<!ENTITY sample.txt "hello">\n'
        dtdregen = self.dtdregen(dtdsource)
        print dtdsource
        print dtdregen
        assert dtdsource == dtdregen

    def test_localisation_notes(self):
        """test to ensure that we retain the localisation note correctly"""
        dtdsource = '''<!--LOCALIZATION NOTE (publishFtp.label): Edit box appears beside this label -->
<!ENTITY publishFtp.label "If publishing to a FTP site, enter the HTTP address to browse to:">
'''
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_entitityreference_in_source(self):
        """checks that an &entity; in the source is retained"""
        dtdsource = '<!ENTITY % realBrandDTD SYSTEM "chrome://branding/locale/brand.dtd">\n%realBrandDTD;\n'
        dtdregen = self.dtdregen(dtdsource)
        print dtdsource
        print dtdregen
        assert dtdsource == dtdregen

    def test_comment_following(self):
        """check that comments that appear after and entity are not pushed onto another line"""
        dtdsource = '<!ENTITY textZoomEnlargeCmd.commandkey2 "="> <!-- + is above this key on many keyboards -->'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen
   
