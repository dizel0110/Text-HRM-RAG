"""
Generate multi-domain synthetic QA dataset for VORTEX benchmark.
Creates data/multi_domain/corpus.json and data/multi_domain/questions.json.

All ground truth is explicitly written (no fragile parsing).

Usage:
    python scripts/generate_multi_domain_data.py
"""

import json
import os


DOMAIN_QUESTIONS = 5  # questions per domain


def main():
    corpus = []
    questions = []
    cid = 0
    domain_q_count = 0

    def add(name: str, facts: list[str], qas: list[tuple[str, str]]):
        nonlocal cid, domain_q_count
        # Always add facts to corpus (search needs all documents)
        for fact in facts:
            corpus.append({"id": str(cid), "text": fact, "entity": name})
            cid += 1
        # Only add questions up to the domain limit
        if domain_q_count < DOMAIN_QUESTIONS:
            room = DOMAIN_QUESTIONS - domain_q_count
            for q, a in qas[:room]:
                questions.append({"question": q, "ground_truth": a})
                domain_q_count += 1

    # ---- Literature & Authors ----
    domain_q_count = 0
    add("Jane Austen", [
        "Jane Austen was born on 16 December 1775 in Steventon, England.",
        "Jane Austen wrote 'Pride and Prejudice', first published in 1813.",
        "Jane Austen wrote 'Sense and Sensibility' and 'Emma'.",
    ], [
        ("What year was Jane Austen born?", "1775"),
        ("What novel did Jane Austen write that was published in 1813?", "Pride and Prejudice"),
        ("Where was Jane Austen born?", "Steventon, England"),
        ("In what country was Jane Austen born?", "England"),
        ("Who wrote 'Pride and Prejudice' and where were they born?", "Jane Austen, Steventon, England"),
    ])

    add("George Orwell", [
        "George Orwell was born Eric Arthur Blair on 25 June 1903 in Motihari, India.",
        "George Orwell wrote 'Nineteen Eighty-Four', published in 1949.",
        "George Orwell wrote 'Animal Farm', a political satire published in 1945.",
    ], [
        ("What year was George Orwell born?", "1903"),
        ("What is George Orwell's birth name?", "Eric Arthur Blair"),
        ("What novel did George Orwell publish in 1949?", "Nineteen Eighty-Four"),
        ("Where was George Orwell born?", "Motihari, India"),
        ("Who wrote both 'Animal Farm' and 'Nineteen Eighty-Four'?", "George Orwell"),
    ])

    domain_q_count = 0
    # ---- Science ----
    add("Marie Curie", [
        "Marie Curie was born on 7 November 1867 in Warsaw, Poland.",
        "Marie Curie discovered the elements polonium and radium.",
        "Marie Curie won the Nobel Prize in Physics in 1903 and in Chemistry in 1911.",
    ], [
        ("What year was Marie Curie born?", "1867"),
        ("What elements did Marie Curie discover?", "polonium and radium"),
        ("In what country was Marie Curie born?", "Poland"),
        ("What Nobel Prizes did Marie Curie win?", "Physics in 1903 and Chemistry in 1911"),
        ("Who discovered radium and in what year were they born?", "Marie Curie, 1867"),
    ])

    add("Rosalind Franklin", [
        "Rosalind Franklin was born on 25 July 1920 in London, England.",
        "Rosalind Franklin's X-ray crystallography images were critical to discovering DNA structure.",
        "Rosalind Franklin also made contributions to the understanding of coal and viruses.",
    ], [
        ("What year was Rosalind Franklin born?", "1920"),
        ("What technique did Rosalind Franklin use that helped discover DNA?", "X-ray crystallography"),
        ("Where was Rosalind Franklin born?", "London, England"),
        ("What was Rosalind Franklin's contribution to science?", "X-ray images critical to DNA structure discovery"),
        ("Who was born in London and contributed to the discovery of DNA?", "Rosalind Franklin"),
    ])

    domain_q_count = 0
    # ---- Music ----
    add("Ludwig van Beethoven", [
        "Ludwig van Beethoven was born on 17 December 1770 in Bonn, Germany.",
        "Beethoven composed 9 symphonies; Symphony No. 9 is his most famous.",
        "Beethoven began losing his hearing in his late 20s and was nearly deaf by the end of his life.",
    ], [
        ("What year was Beethoven born?", "1770"),
        ("How many symphonies did Beethoven compose?", "9"),
        ("What was Beethoven's most famous symphony?", "Symphony No. 9"),
        ("What physical challenge did Beethoven face?", "He lost his hearing"),
        ("Who composed 9 symphonies and was born in Germany?", "Ludwig van Beethoven"),
    ])

    add("Aretha Franklin", [
        "Aretha Franklin was born on 25 March 1942 in Memphis, Tennessee, USA.",
        "Aretha Franklin is known as the Queen of Soul and her hit song 'Respect'.",
        "Aretha Franklin won 18 Grammy Awards during her career.",
    ], [
        ("What year was Aretha Franklin born?", "1942"),
        ("What is Aretha Franklin's nickname?", "Queen of Soul"),
        ("What is Aretha Franklin's famous song?", "Respect"),
        ("How many Grammy Awards did Aretha Franklin win?", "18"),
        ("Who was known as the Queen of Soul and born in 1942?", "Aretha Franklin"),
    ])

    domain_q_count = 0
    # ---- Sports ----
    add("Muhammad Ali", [
        "Muhammad Ali was born Cassius Clay on 17 January 1942 in Louisville, Kentucky, USA.",
        "Muhammad Ali won the world heavyweight boxing title three times.",
        "Muhammad Ali was known for 'float like a butterfly, sting like a bee'.",
    ], [
        ("What year was Muhammad Ali born?", "1942"),
        ("What was Muhammad Ali's birth name?", "Cassius Clay"),
        ("How many times did Muhammad Ali win the heavyweight title?", "three"),
        ("What is Muhammad Ali's famous catchphrase?", "float like a butterfly, sting like a bee"),
        ("Who won the heavyweight title three times and was born in 1942?", "Muhammad Ali"),
    ])

    add("Serena Williams", [
        "Serena Williams was born on 26 September 1981 in Saginaw, Michigan, USA.",
        "Serena Williams won 23 Grand Slam singles titles, the most in the Open Era.",
        "Serena Williams is considered one of the greatest tennis players of all time.",
    ], [
        ("What year was Serena Williams born?", "1981"),
        ("How many Grand Slam titles did Serena Williams win?", "23"),
        ("What sport does Serena Williams play?", "tennis"),
        ("Where was Serena Williams born?", "Saginaw, Michigan"),
        ("Who won 23 Grand Slam titles and was born in 1981?", "Serena Williams"),
    ])

    domain_q_count = 0
    # ---- History ----
    add("Cleopatra", [
        "Cleopatra VII was born in 69 BC in Alexandria, Egypt.",
        "Cleopatra was the last active ruler of the Ptolemaic Kingdom of Egypt.",
        "Cleopatra allied with Julius Caesar and later Mark Antony of Rome.",
    ], [
        ("When was Cleopatra born?", "69 BC"),
        ("Who was the last ruler of the Ptolemaic Kingdom?", "Cleopatra"),
        ("Who did Cleopatra ally with?", "Julius Caesar and Mark Antony"),
        ("Where was Cleopatra born?", "Alexandria, Egypt"),
        ("Who was the last Ptolemaic ruler and born in 69 BC?", "Cleopatra"),
    ])

    add("Genghis Khan", [
        "Genghis Khan was born Temujin around 1162 near the Onon River in Mongolia.",
        "Genghis Khan founded the Mongol Empire, the largest contiguous land empire.",
        "Genghis Khan united the nomadic Mongol tribes and established the Yassa legal code.",
    ], [
        ("When was Genghis Khan born?", "1162"),
        ("What was Genghis Khan's birth name?", "Temujin"),
        ("What empire did Genghis Khan found?", "Mongol Empire"),
        ("What legal code did Genghis Khan establish?", "Yassa"),
        ("Who founded the Mongol Empire and was born in 1162?", "Genghis Khan"),
    ])

    domain_q_count = 0
    # ---- Technology ----
    add("Alan Turing", [
        "Alan Turing was born on 23 June 1912 in London, England.",
        "Alan Turing developed the concept of the Turing machine, a foundation of computer science.",
        "Alan Turing played a crucial role in breaking the Enigma code during World War II.",
    ], [
        ("What year was Alan Turing born?", "1912"),
        ("What concept did Alan Turing develop?", "Turing machine"),
        ("What code did Alan Turing help break?", "Enigma"),
        ("Where was Alan Turing born?", "London, England"),
        ("Who developed the Turing machine and was born in 1912?", "Alan Turing"),
    ])

    add("Grace Hopper", [
        "Grace Hopper was born on 9 December 1906 in New York City, USA.",
        "Grace Hopper invented the first compiler for a programming language.",
        "Grace Hopper contributed to the COBOL programming language.",
    ], [
        ("What year was Grace Hopper born?", "1906"),
        ("What did Grace Hopper invent?", "the first compiler"),
        ("What programming language did Grace Hopper contribute to?", "COBOL"),
        ("Where was Grace Hopper born?", "New York City"),
        ("Who invented the first compiler and was born in 1906?", "Grace Hopper"),
    ])

    domain_q_count = 0
    # ---- Art ----
    add("Leonardo da Vinci", [
        "Leonardo da Vinci was born on 15 April 1452 in Vinci, Florence, Italy.",
        "Leonardo da Vinci painted the Mona Lisa, one of the most famous paintings.",
        "Leonardo da Vinci designed flying machines and studied anatomy.",
    ], [
        ("What year was Leonardo da Vinci born?", "1452"),
        ("What is Leonardo da Vinci's most famous painting?", "Mona Lisa"),
        ("What did Leonardo da Vinci design?", "flying machines"),
        ("Where was Leonardo da Vinci born?", "Vinci, Florence, Italy"),
        ("Who painted the Mona Lisa and was born in 1452?", "Leonardo da Vinci"),
    ])

    add("Frida Kahlo", [
        "Frida Kahlo was born on 6 July 1907 in Coyoacan, Mexico City, Mexico.",
        "Frida Kahlo is known for her self-portraits exploring identity and pain.",
        "Frida Kahlo's house La Casa Azul is now a museum.",
    ], [
        ("What year was Frida Kahlo born?", "1907"),
        ("What is Frida Kahlo known for?", "self-portraits"),
        ("What is the name of Frida Kahlo's house?", "La Casa Azul"),
        ("Where was Frida Kahlo born?", "Coyoacan, Mexico City"),
        ("Who was known for self-portraits and born in 1907?", "Frida Kahlo"),
    ])

    domain_q_count = 0
    # ---- Geography ----
    add("Amazon River", [
        "The Amazon River flows through South America, mainly Brazil and Peru.",
        "The Amazon River is the largest river by discharge volume in the world.",
        "The Amazon basin covers about 7 million square kilometers.",
    ], [
        ("What is the largest river by discharge volume?", "Amazon River"),
        ("What continents does the Amazon River flow through?", "South America"),
        ("Which countries does the Amazon River flow through?", "Brazil and Peru"),
        ("How large is the Amazon basin?", "7 million square kilometers"),
        ("What is the name of the river with a 7 million sq km basin in South America?", "Amazon River"),
    ])

    add("Mount Everest", [
        "Mount Everest is the highest mountain on Earth at 8848 meters above sea level.",
        "Mount Everest is located in the Himalayas on the border of Nepal and Tibet.",
        "Edmund Hillary and Tenzing Norgay first summited Mount Everest in 1953.",
    ], [
        ("What is the highest mountain on Earth?", "Mount Everest"),
        ("How tall is Mount Everest?", "8848 meters"),
        ("Who first summited Mount Everest?", "Edmund Hillary and Tenzing Norgay"),
        ("What year was Mount Everest first summited?", "1953"),
        ("Where is Mount Everest located?", "Himalayas, border of Nepal and Tibet"),
    ])

    domain_q_count = 0
    # ---- Biology & Medicine ----

    add("Charles Darwin", [
        "Charles Darwin was born on 12 February 1809 in Shrewsbury, England.",
        "Charles Darwin developed the theory of evolution by natural selection.",
        "Darwin's book 'On the Origin of Species' was published in 1859.",
    ], [
        ("What year was Charles Darwin born?", "1809"),
        ("What theory did Charles Darwin develop?", "evolution by natural selection"),
        ("What book did Darwin publish in 1859?", "On the Origin of Species"),
        ("Where was Charles Darwin born?", "Shrewsbury, England"),
        ("Who developed the theory of evolution and was born in 1809?", "Charles Darwin"),
    ])

    add("Louis Pasteur", [
        "Louis Pasteur was born on 27 December 1822 in Dole, France.",
        "Louis Pasteur developed pasteurization and vaccines for rabies and anthrax.",
        "Louis Pasteur is considered one of the founders of microbiology.",
    ], [
        ("What year was Louis Pasteur born?", "1822"),
        ("What process did Louis Pasteur develop?", "pasteurization"),
        ("What vaccines did Louis Pasteur develop?", "rabies and anthrax"),
        ("Where was Louis Pasteur born?", "Dole, France"),
        ("Who developed pasteurization and was born in 1822?", "Louis Pasteur"),
    ])

    domain_q_count = 0
    # ---- Astronomy ----
    add("Mars", [
        "Mars is the fourth planet from the Sun and is known as the Red Planet.",
        "Mars has the tallest mountain in the solar system, Olympus Mons at 21.9 km.",
        "Mars has two small moons named Phobos and Deimos.",
    ], [
        ("Which planet is known as the Red Planet?", "Mars"),
        ("What is the tallest mountain in the solar system?", "Olympus Mons"),
        ("What are the moons of Mars called?", "Phobos and Deimos"),
        ("How many moons does Mars have?", "two"),
        ("Which planet has the mountain Olympus Mons?", "Mars"),
    ])

    add("Voyager 1", [
        "Voyager 1 was launched by NASA on 5 September 1977.",
        "Voyager 1 is the farthest human-made object from Earth, in interstellar space.",
        "Voyager 1 carries a Golden Record with sounds and images representing Earth.",
    ], [
        ("What year was Voyager 1 launched?", "1977"),
        ("What is the farthest human-made object from Earth?", "Voyager 1"),
        ("What does Voyager 1 carry?", "Golden Record"),
        ("Where is Voyager 1 now?", "interstellar space"),
        ("Which spacecraft carries a Golden Record and was launched in 1977?", "Voyager 1"),
    ])

    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "multi_domain")
    os.makedirs(out_dir, exist_ok=True)

    corpus_path = os.path.join(out_dir, "corpus.json")
    questions_path = os.path.join(out_dir, "questions.json")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    n_corpus = len(corpus)
    n_q = len(questions)
    multi = sum(1 for q in questions if q["ground_truth"].count(",") >= 2)
    print(f"Generated {n_corpus} chunks  → {corpus_path}")
    print(f"Generated {n_q} Q&A pairs → {questions_path}")
    print(f"  Domains: 10, Entities: 20")
    print(f"  Simple: {n_q - multi}, Multi-hop: {multi}")


if __name__ == "__main__":
    main()
