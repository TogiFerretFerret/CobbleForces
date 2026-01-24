#include <iostream>
#include <vector>
#include <random>
#include <chrono>

using namespace std;

int main(int argc, char* argv[]) {
    // Seed the random number generator
    unsigned int seed = std::chrono::system_clock::now().time_since_epoch().count();
    if (argc > 1) seed = atoi(argv[1]);
    mt19937_64 rng(seed);

    // Constraints: N, K <= 10^5
    int N = 100000;
    
    // Choose K randomly or fixed large
    uniform_int_distribution<int> k_dist(1, N);
    int K = k_dist(rng);
    
    // Uncomment for smaller specific tests
    // N = 10; K = 3;

    cout << N << " " << K << endl;

    // Generate Array A
    // Values up to 10^9 allowed, but keeping them reasonable avoids overflow in naive solutions early on
    uniform_int_distribution<long long> val_dist(1, 100000);
    for (int i = 0; i < N; ++i) {
        cout << val_dist(rng) << (i == N - 1 ? "" : " ");
    }
    cout << endl;

    return 0;
}
