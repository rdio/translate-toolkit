from translate.search import match
from translate.storage import csvl10n

class TestMatch:
    """Test the matching class"""
    def candidatestrings(self, list):
        """returns only the candidate strings out of the list with (score, string) tuples"""
        return [original for score, original, translation in list]

    def buildcsv(self, sources, targets=None):
        """Build a csvfile store with the given source and target strings"""
        if targets is None:
            targets = sources
        else:
            assert len(sources) == len(targets)
        csvfile = csvl10n.csvfile()
        for source, target in zip(sources, targets):
            unit = csvfile.addsourceunit(source)
            unit.target = target
        return csvfile
            
    def test_matching(self):
        """Test basic matching"""
        csvfile = self.buildcsv(["hand", "asdf", "fdas", "haas", "pond"])
        matcher = match.matcher(csvfile)
        candidates = self.candidatestrings(matcher.matches("hond"))
        candidates.sort()
        assert candidates == ["hand", "pond"]
        message = "Ek skop die bal"
        csvfile = self.buildcsv(
            ["Hy skop die bal", 
            message, 
            "Jannie skop die bal", 
            "Ek skop die balle", 
            "Niemand skop die bal nie"])
        matcher = match.matcher(csvfile)
        candidates = self.candidatestrings(matcher.matches(message))
        assert len(candidates) == 3
        #test that the 100% match is indeed first:
        assert candidates[0] == message
        candidates.sort()
        assert candidates[1:] == ["Ek skop die balle", "Hy skop die bal"]

    def test_terminology(self):
        csvfile = self.buildcsv(["file", "computer", "directory"])
        matcher = match.terminologymatcher(csvfile)
        candidates = self.candidatestrings(matcher.matches("Copy the files from your computer"))
        candidates.sort()
        assert candidates == ["computer", "file"]

