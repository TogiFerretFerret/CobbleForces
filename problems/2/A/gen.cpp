#include <iostream>
#include <vector>
#include <random>
#include <chrono>

using namespace std;

int main(int argc, char* argv[]) {
    unsigned int seed = std::chrono::system_clock::now().time_since_epoch().count();
    if (argc > 1) seed = atoi(argv[1]);
    mt19937_64 rng(seed);

    int N = 200000;
    
    // Uncomment for small test
    // N = 5;

    cout << N << endl;

    uniform_int_distribution<long long> val_dist(1, 1000000000);
    for (int i = 0; i < N; ++i) {
        cout << val_dist(rng) << (i == N - 1 ? "" : " ");
    }
    cout << endl;

    return 0;
}
