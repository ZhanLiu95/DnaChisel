from dnachisel import (EnforceTranslation, DnaOptimizationProblem,
                       random_dna_sequence, Location, EnforcePattern)

# sequence = random_dna_sequence(5000, seed=123456)
# sequence = random_dna_sequence(5000, seed=2)
# sequence = random_dna_sequence(5000, seed=3)
# for seed in [2, 3, 123456]:
sequence = random_dna_sequence(5000, seed=123)

constraints = [
    EnforceTranslation(Location(1000, 2500)),
    EnforceTranslation(Location(3000, 4500)),
    EnforcePattern("ANANANANTT", location=Location(1100, 2150)),
    EnforcePattern("ATGATGCCTK", location=Location(2700, 2800))
]

problem = DnaOptimizationProblem(
    sequence=sequence,
    constraints=constraints
)
print (problem.constraints_text_summary())
assert not problem.all_constraints_pass()
problem.resolve_constraints()
assert problem.all_constraints_pass()
print (problem.constraints_text_summary())
