// Shadow FIFO primitive. Prices and quantities are integers; no Python objects
// cross the ABI. Cancellation ahead is deliberately not credited.
#include <algorithm>
#include <cstdint>
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API __attribute__((visibility("default")))
#endif
extern "C" API std::int64_t consume(std::int64_t eligible,
                                   std::int64_t* ahead,
                                   std::int64_t remaining) {
    if (eligible <= 0 || remaining <= 0) return 0;
    const auto cleared = std::min(*ahead, eligible);
    *ahead -= cleared;
    return std::min(remaining, eligible - cleared);
}
