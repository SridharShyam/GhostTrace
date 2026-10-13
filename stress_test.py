from ghosttrace import audit, calculate_score

edge_cases = [
    # Case 1: Multiple rhetorical constructions in one short sentence
    ("Whether you are a beginner or an expert, it is not just a tool, but a way of life.", "Multiple construction cliches in 18 words"),
    
    # Case 2: Classic AI filler transitions without vocabulary trigger words
    ("Furthermore, moreover, it is worth noting that we must pay attention to this development.", "Stacked academic transitions"),
    
    # Case 3: Academic boilerplate opener with NO single vocabulary hit
    ("In recent years, the rapid advancement of artificial intelligence has attracted widespread attention across academia and industry.", "Classic abstract opener filler"),
    
    # Case 4: Adverb-stacking / Quadruple AI adverbs
    ("The model comprehensively, seamlessly, meticulously, and robustly optimizes parameters.", "Quadruple AI adverbs in 9 words"),
    
    # Case 5: The robotic essay conclusion
    ("In conclusion, our study paves the way for future breakthroughs in this domain.", "Robotic closing paragraph boilerplate"),
    
    # Case 6: Human technical control case
    ("We formulate the convex optimization problem as a semidefinite program and prove asymptotic convergence.", "Authentic human paper control"),
]

print("=" * 80)
print("  EDGE-CASE STRESS TEST & ACCURACY AUDIT")
print("=" * 80)

for text, desc in edge_cases:
    words = len(text.split())
    hits = audit(text, mode="academic")
    score, vocab_hits, density, phrase_hits = calculate_score(hits, word_count=words)
    print(f"\nTEST: {desc} ({words} words)")
    print(f"  Input: \"{text}\"")
    print(f"  Hits: {dict((k, v) for k, v in hits.items() if v)}")
    print(f"  Calculated Score: {score}/5 (Density Penalty: {density})")
