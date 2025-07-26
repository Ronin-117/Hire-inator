from transformer.app import AcademicTextHumanizer, download_nltk_resources

def run_example():
    """
    A simple script to demonstrate the AcademicTextHumanizer.
    """
    # 1. Download necessary NLTK resources (only needs to be done once)
    # This function is included in app.py and ensures all data is available.
    print("Downloading NLTK resources...")
    download_nltk_resources()
    print("Downloads complete.")

    # 2. Initialize the humanizer
    # You can adjust the probabilities for different transformation styles if needed.
    humanizer = AcademicTextHumanizer(
        p_passive=0.3,
        p_synonym_replacement=0.3,
        p_academic_transition=0.4
    )

    # 3. Define the text you want to transform
    original_text = (
    "I think we kind of rushed through the whole process without fully understanding the consequences. "
    "We didn’t spend enough time researching the background, so some of our assumptions might be flawed. "
    "I guess the team just wanted to meet the deadline more than anything else. "
    "At first, it looked like everything was going smoothly, but then some unexpected problems started to show up. "
    "Honestly, I’m not really surprised, given how fast we moved. "
    "Now we’re trying to fix things on the fly, which isn’t ideal. "
    "Hopefully, the stakeholders will be understanding, but I’m not totally sure. "
    "It’s hard to explain the situation without sounding like we were careless, even though we weren’t trying to cut corners. "
    "We just didn’t realize how complex things would get. "
    "Anyway, lessons learned. Next time, we should probably set aside more time for planning and make sure every team member is on the same page from the beginning."
    )

    print("\n" + "="*40)
    print("Original Text:")
    print(original_text)
    print("="*40 + "\n")

    # 4. Run the transformation
    # You can enable or disable passive voice and synonym replacement.

    # Example 1: Basic transformation (expands contractions, adds transitions)
    transformed_basic = humanizer.humanize_text(
        original_text,
        use_passive=False,
        use_synonyms=False
    )
    print("--- Transformed (Basic) ---")
    print(transformed_basic)
    print("\n")

    # Example 2: Transformation with passive voice enabled
    transformed_passive = humanizer.humanize_text(
        original_text,
        use_passive=True,
        use_synonyms=False
    )
    print("--- Transformed (with Passive Voice) ---")
    print(transformed_passive)
    print("\n")

    # Example 3: Transformation with everything enabled
    transformed_full = humanizer.humanize_text(
        original_text,
        use_passive=True,
        use_synonyms=True
    )
    print("--- Transformed (Full) ---")
    print(transformed_full)
    print("\n")

if __name__ == "__main__":
    run_example()
