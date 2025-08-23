import regex as re  
from typing import List  
  
# Extended sentence-ending punctuation triggers  
SENTENCE_END_TRIGGERS = r".!?…。！？؟؛।ฯ‽"  
  
class UniversalSplitter:  
    """  
    Universal rule-based sentence splitter using regex.  
    Handles common sentence boundaries, abbreviations, acronyms, decimals,  
    and misplaced punctuation.  
    """   
    def __init__(self):  
        # Core sentence split regex
        self.sentence_end_regex = re.compile(
            rf"""
            (?<!\n\s+\p{{N}}+\.\s+)        # Don't split decimals, numbered list headings
            (?<=\n\s?|[{SENTENCE_END_TRIGGERS}]\s+)  # Split AFTER newline or sentence-ending punctuation
            """,
            re.VERBOSE
        )
        
        # Regex for abbreviations (e.g., Dr., Mr.)  
        self.abbreviation_regex = re.compile(r"\p{Lu}\p{Ll}{1,3}\.\s?")  
   
    def split(self, text: str) -> List[str]:
        """  
        Splits text into sentences using a smart, rule-based regex approach.  
        Designed as a robust fallback, handling various sentence boundary issues.  
  
        Args:  
            text (str): The input text to split.  
  
        Returns:  
            List[str]: A list of sentences.  
        """  
        # Stage 1: initial split
        sentences = self.sentence_end_regex.split(text.strip()) 
        
        # Stage 2: post processing, merge fake positive splits
        fixed_sentences = []  
        if sentences:  
            fixed_sentences.append(sentences[0])  
   
        for curr_sent in sentences[1:]:  
            prev_sent = fixed_sentences[-1]  
            # Merge single-character previous sentence or abbreviations as before  
            if (
                len(prev_sent.strip()) == 1
            ):  # Re-join leftover punctuation, eg: hello!!  
                fixed_sentences[-1] += curr_sent  
            elif (  
                self.abbreviation_regex.fullmatch(prev_sent)  
                or self.abbreviation_regex.search(prev_sent) and not curr_sent[0].isupper()  
            ):  # Avoid splitting after an abbreviation
                fixed_sentences[-1] += " " + curr_sent  
            else:  
                fixed_sentences.append(curr_sent)  
  
        # Stage 3: Cleanup and normalized right trailings
        return [sent.rstrip() + " " for sent in fixed_sentences if sent.strip()]  

    
# Example usage
if __name__ == "__main__":
    import textwrap 
    
    complex_text = textwrap.dedent("""
    Dr. Smith, the lead researcher at the U.S.A. Space Agency, said: "We've reached 123.45 light-years… incredible!" 
    He added, Consider the following points (They are special.):
      1. All systems are operational.
      2. No anomalies detected.
      3. Data for 2025 is ready.

    Meanwhile, the team in Paris (France) exclaimed: "Bravo! Très bien!" They laughed at number 2. Could this be real? Yes, it is.
    The Playlist includes:
      - Video: Mars landing
      - Image: Satellite view
      - Music: Space-themed track
    """)

    splitter = UniversalSplitter()
    sentences = splitter.split(complex_text)

    for i, s in enumerate(sentences, 1):
        print(f"{i}: {s}")