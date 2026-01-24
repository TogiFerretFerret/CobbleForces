#include <iostream>
#include <vector>
#include <string>
#include <random>
#include <chrono>
#include <algorithm>

using namespace std;

int main(int argc, char* argv[]) {
    unsigned int seed = std::chrono::system_clock::now().time_since_epoch().count();
    if (argc > 1) seed = atoi(argv[1]);
    mt19937 rng(seed);

    int N = 100000;
    int Q = 100000;
    
    // N = 10; Q = 5; // Debug

    // Generate random string
    string S = "";
    uniform_int_distribution<int> char_dist(0, 25);
    for(int i=0; i<N; ++i) {
        S += (char)('a' + char_dist(rng));
    }

    cout << S << endl;
    cout << Q << endl;

    uniform_int_distribution<int> pos_dist(1, N);
    
    for(int i=0; i<Q; ++i) {
        int l = pos_dist(rng);
        int r = pos_dist(rng);
        if (l > r) swap(l, r);
        cout << l << " " << r << endl;
    }

    return 0;
}
