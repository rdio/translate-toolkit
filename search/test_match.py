from translate.search import match

class TestMatch:
    """Test the matching class"""
    def candidatestrings(self, list):
        """returns only the candidate strings out of the list with (score, string) typles"""
        return [candidate for score, candidate in list]

    def test_matching(self):
        """Test basic matching"""
        matcher = match.matcher()
        candidates = self.candidatestrings(matcher.matches("hond", ["hand", "asdf", "fdas", "haas", "pond"]))
        candidates.sort()
        assert candidates == ["hand", "pond"]
        message = "Ek skop die bal"
        candidates = self.candidatestrings(matcher.matches(message, 
            ["Hy skop die bal", 
            message, 
            "Jannie skop die bal", 
            "Ek skop die balle", 
            "Niemand skop die bal nie"]))
        assert len(candidates) == 3
        #test that the 100% match is indeed first:
        assert candidates[0] == message
        candidates.sort()
        assert candidates[1:] == ["Ek skop die balle", "Hy skop die bal"]

	
