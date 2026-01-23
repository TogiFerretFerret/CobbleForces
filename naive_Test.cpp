#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

// Use long long to prevent overflow
typedef long long ll;

int main() {
    // Optimize I/O operations (though not strictly necessary for O(NQ))
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int N, Q;
    if (!(cin >> N >> Q)) return 0;

    // A stores current delinquency levels
    // H stores historic sum of delinquency levels
    vector<ll> A(N + 1);
    vector<ll> H(N + 1, 0);

    // Read initial array
    // Note: Initial state is time t=0. 
    // H should effectively be initialized to A (history includes time 0 state? 
    // Problem says H_i = sum A_i^(t). If t=0 is initial state, then H starts as A).
    // Let's assume the standard definition where history accumulates A 
    // AFTER every update operation.
    // If the problem implies H includes the initial state before any operations:
    for (int i = 1; i <= N; ++i) {
        cin >> A[i];
        H[i] = A[i]; // History includes initial state t=0
    }

    for (int q_idx = 0; q_idx < Q; ++q_idx) {
        int type;
        cin >> type;

        if (type == 1) {
            // Range Add
            int l, r;
            ll x;
            cin >> l >> r >> x;
            for (int i = l; i <= r; ++i) {
                A[i] += x;
            }
            // Update History for ALL nodes after an update step
            for (int i = 1; i <= N; ++i) H[i] += A[i];

        } else if (type == 2) {
            // Range ChMin
            int l, r;
            ll x;
            cin >> l >> r >> x;
            for (int i = l; i <= r; ++i) {
                A[i] = min(A[i], x);
            }
            // Update History for ALL nodes after an update step
            for (int i = 1; i <= N; ++i) H[i] += A[i];

        } else if (type == 3) {
            // Query Current Sum
            int l, r;
            cin >> l >> r;
            ll sum = 0;
            for (int i = l; i <= r; ++i) {
                sum += A[i];
            }
            cout << sum << "\n";

        } else if (type == 4) {
            // Query Historic Sum
            int l, r;
            cin >> l >> r;
            ll sum = 0;
            for (int i = l; i <= r; ++i) {
                sum += H[i];
            }
            cout << sum << "\n";
        }
    }

    return 0;
}
