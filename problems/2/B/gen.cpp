#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <algorithm>

using namespace std;

int main(int argc, char* argv[]) {
    unsigned int seed = std::chrono::system_clock::now().time_since_epoch().count();
    if (argc > 1) seed = atoi(argv[1]);
    mt19937_64 rng(seed);

    int N = 40;
    long long K_MAX = 1000000000LL;
    
    // Uncomment to create smaller tests manually if needed
    // N = 20;

    uniform_int_distribution<long long> k_dist(1, 100000); 
    long long K = k_dist(rng);

    cout << N << " " << K << endl;

    // We want to ensure at least one solution exists sometimes.
    // Strategy: Generate items normally. It's likely no subset sums to exact average.
    // To ensure feasibility: pick a random target subset size S, generate S items,
    // force their average to be K.
    
    // Actually, just pure random is fine for "Max Test", but let's make it solvable.
    // We will generate random pairs.
    
    uniform_int_distribution<long long> f_dist(1, 1000000);
    uniform_int_distribution<long long> c_dist(1, K * 2); 
    // C around K ensures C-K is smallish, mixing positive and negative.

    vector<pair<long long, long long>> items;
    for(int i=0; i<N; ++i) {
        long long f = f_dist(rng);
        long long c = c_dist(rng);
        items.push_back({f, c});
    }

    // Force a solution?
    // Let's pick 5 items and force their average to be K.
    // sum(C) = 5 * K.
    // We modify the last chosen item to fix the sum.
    
    vector<int> indices(N);
    for(int i=0; i<N; ++i) indices[i] = i;
    shuffle(indices.begin(), indices.end(), rng);
    
    long long current_sum = 0;
    for(int i=0; i<4; ++i) current_sum += items[indices[i]].second;
    
    long long needed = 5 * K - current_sum;
    if (needed > 0) {
        items[indices[4]].second = needed;
    }

    for (const auto& p : items) {
        cout << p.first << " " << p.second << endl;
    }

    return 0;
}
