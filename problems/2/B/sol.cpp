#include <iostream>
#include <vector>
#include <map>
#include <algorithm>

using namespace std;

typedef long long ll;

/**
 * Problem B: Sayaka's Blend
 * Algorithm: Meet-in-the-middle
 * Complexity: O(N * 2^(N/2))
 * * Logic:
 * Transform C_i => W_i = C_i - K.
 * We want a subset where sum(W_i) = 0 and sum(F_i) is maximized.
 * Split into two halves, compute all subset sums, match using a map.
 */

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n;
    ll k;
    if (!(cin >> n >> k)) return 0;

    vector<pair<ll, ll>> items(n);
    for (int i = 0; i < n; ++i) {
        cin >> items[i].first >> items[i].second; // F, C
        items[i].second -= k; // Transform
    }

    int n1 = n / 2;
    int n2 = n - n1;

    // Map: Weight -> Max Flavor
    map<ll, ll> left_map;
    
    // Iterate 0 to 2^n1 - 1
    for (int i = 0; i < (1 << n1); ++i) {
        ll w = 0, f = 0;
        for (int j = 0; j < n1; ++j) {
            if ((i >> j) & 1) {
                f += items[j].first;
                w += items[j].second;
            }
        }
        if (left_map.find(w) == left_map.end()) {
            left_map[w] = f;
        } else {
            left_map[w] = max(left_map[w], f);
        }
    }

    ll ans = 0;
    bool found = false;

    // Iterate 0 to 2^n2 - 1
    for (int i = 0; i < (1 << n2); ++i) {
        ll w = 0, f = 0;
        bool r_non_empty = false;
        for (int j = 0; j < n2; ++j) {
            if ((i >> j) & 1) {
                f += items[n1 + j].first;
                w += items[n1 + j].second;
                r_non_empty = true;
            }
        }

        ll target = -w;
        if (left_map.count(target)) {
            ll l_f = left_map[target];
            // Check if the total set is non-empty.
            // If right is non-empty, total is valid.
            // If right is empty, left must be non-empty (l_f > 0, assuming F_i > 0).
            // Or simpler: F_i >= 1 is usually true. If total F > 0, it's valid.
            ll total_f = f + l_f;
            if (total_f > 0) {
                ans = max(ans, total_f);
                found = true;
            }
        }
    }

    cout << ans << endl;

    return 0;
}
