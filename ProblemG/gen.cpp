#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <algorithm>

using namespace std;

int main(int argc, char* argv[]) {
    // Seed setup
    unsigned int seed = std::chrono::system_clock::now().time_since_epoch().count();
    if (argc > 1) {
        seed = atoi(argv[1]);
    }
    mt19937_64 rng(seed);

    // Constraints
    // N, Q up to 2e5
    // Let's make a decent sized test
    int N = 200000;
    int Q = 200000;
    
    // If you want smaller tests for debugging:
    // N = 100; Q = 100;

    cout << N << " " << Q << endl;

    // Initial Array
    // Values 0 to 10^9
    uniform_int_distribution<int> val_dist(0, 1000000000);
    for (int i = 0; i < N; ++i) {
        cout << val_dist(rng) << (i == N - 1 ? "" : " ");
    }
    cout << endl;

    // Operations
    // 1: Add, 2: ChMin, 3: Sum, 4: Hist Sum
    uniform_int_distribution<int> type_dist(1, 4);
    uniform_int_distribution<int> range_dist(1, N);
    uniform_int_distribution<long long> add_val_dist(-10000, 10000); 
    uniform_int_distribution<int> min_val_dist(0, 1000000000);

    for (int i = 0; i < Q; ++i) {
        int t = type_dist(rng);
        int l = range_dist(rng);
        int r = range_dist(rng);
        if (l > r) swap(l, r);

        cout << t << " " << l << " " << r;

        if (t == 1) {
            // Range Add
            cout << " " << add_val_dist(rng);
        } else if (t == 2) {
            // Range ChMin
            cout << " " << min_val_dist(rng);
        }
        cout << endl;
    }

    return 0;
}
