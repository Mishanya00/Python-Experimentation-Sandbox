Первый запуск benchmark.py 
показал скорость Готенберга ~1,5 раза быстрее ручного способа.

Однако все остальные запуски показали скорость ручного метода быстрее в 1.15-1,45 раза.

Бенчмарк на моем ноуте:

Sequential benchmark.py with template generation:
========================================
📊 BENCHMARK RESULTS SUMMARY
========================================
Manual (Subprocess) Average: 0.3819s
Gotenberg (API) Average:     0.3401s
----------------------------------------
🚀 Gotenberg is 1.12x faster (saves ~0.0418s per file)
========================================

========================================
📊 BENCHMARK RESULTS SUMMARY
========================================
Manual (Subprocess) Average: 0.3845s
Gotenberg (API) Average:     0.3246s
----------------------------------------
🚀 Gotenberg is 1.18x faster (saves ~0.0599s per file)
========================================

========================================
📊 BENCHMARK RESULTS SUMMARY
========================================
Manual (Subprocess) Average: 0.4279s
Gotenberg (API) Average:     0.3355s
----------------------------------------
🚀 Gotenberg is 1.28x faster (saves ~0.0924s per file)
========================================


Sequential benchmark2.py with converting huge 1000-page file
========================================
📊 BENCHMARK RESULTS SUMMARY
========================================
Manual (Subprocess) Average: 4.6647s
Gotenberg (API) Average:     7.2960s
----------------------------------------
🐢 Manual is 1.56x faster
========================================

========================================
📊 BENCHMARK RESULTS SUMMARY
========================================
Manual (Subprocess) Average: 3.9181s
Gotenberg (API) Average:     5.5610s
----------------------------------------
🐢 Manual is 1.42x faster
========================================


Concurrent 25 files:
========================================
Manual Total:    25.1342s
Gotenberg Total: 6.9304s
========================================

Concurrent 10 files:
========================================
Manual Total:    8.5160s
Gotenberg Total: 2.8950s
========================================

Concurrent 100 files:
========================================
Manual Total:    134.8419s
Gotenberg Total: 27.9493s
========================================