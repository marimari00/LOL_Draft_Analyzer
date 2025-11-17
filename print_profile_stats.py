import pstats

stats = pstats.Stats('profile_single.prof')
stats.sort_stats('cumulative').print_stats(30)
print("\nCallees for simulate_chunk:\n")
stats.print_callees('simulate_chunk')
